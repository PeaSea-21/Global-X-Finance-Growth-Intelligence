from __future__ import annotations

import argparse
import json
import re
import sqlite3
import threading
import webbrowser
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

from .db import connect
from .errors import ValidationError
from .compliance import run_financial_ads_precheck
from .normalization import TwseNormalizationService
from .twse_collector import TwseOpenApiCollector, load_twse_config
from .ben_radar import compute_anomalies
from .x_intelligence import (
    attach_market_response,
    build_unified_events,
    cluster_diagnostic_report,
    cluster_quality_report,
    filter_time_window,
    localize_zh,
    taipei_time,
)
from .translation_summary import TranslationSummaryAdapter
from .radar_analytics import select_snapshot_events, source_concentration
from .stock_workbench import build_stock_workbench
from .channel_briefs import channel_brief_payload_for_date, latest_channel_brief_payload


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _connection(database_path: str | Path) -> sqlite3.Connection:
    return connect(database_path)


def _status_class(status: str | None) -> str:
    value = (status or "UNKNOWN").upper()
    if value in {"SUCCESS", "VERIFIED", "ALLOWED", "API_VERIFIED", "ACTIVE", "PASS_PRECHECK", "VERIFIED_OFFICIAL_HTTP_200"}:
        return "status-good"
    if "BLOCKED" in value or value == "FAILED":
        return "status-bad"
    if "NEEDS" in value or "REVIEW" in value or "MANUAL" in value or value == "PARTIAL_FAILED":
        return "status-warn"
    return "status-neutral"


def _summary(raw_payload_json: str, dataset: dict | None) -> str:
    try:
        payload = json.loads(raw_payload_json)
    except json.JSONDecodeError:
        return raw_payload_json[:120]
    fields = (dataset or {}).get("title_fields", [])
    parts = [str(payload[field]) for field in fields if payload.get(field) not in (None, "")]
    if parts:
        return " · ".join(parts)
    return " · ".join(f"{key}: {value}" for key, value in list(payload.items())[:3])


SIGNAL_TITLES = {
    "HIGH_TRADE_VOLUME": "成交量較高",
    "HIGH_TRADE_VALUE": "成交金額較高",
    "NOTABLE_DAILY_CHANGE": "當日漲跌較明顯",
    "FOREIGN_HOLDING_RATIO": "外資及陸資持股比例",
}


def _signal_title(value: str) -> str:
    return SIGNAL_TITLES.get(value, value)


def _freshness_label(value: str) -> str:
    return {
        "CURRENT_OFFICIAL_DATA": "官方當日可用資料",
        "OFFICIAL_LATEST_AVAILABLE_DATA": "官方最新可用資料",
        "UNKNOWN_DATA_DATE": "官方未提供資料日期",
    }.get(value, "資料日期狀態 UNKNOWN")


def _homepage_freshness(data_date: str | None) -> dict:
    if not data_date:
        return {"status": "UNKNOWN_DATA_DATE", "label": "尚無可判定日期的標準化資料"}
    today = datetime.now(timezone(timedelta(hours=8))).date().isoformat()
    if data_date == today:
        return {
            "status": "CURRENT_OFFICIAL_DATA",
            "label": f"官方當日可用資料：{data_date}（日頻資料，不代表兩小時即時資料）",
        }
    return {
        "status": "OFFICIAL_LATEST_AVAILABLE_DATA",
        "label": f"官方最新可用資料：{data_date}（依官方資料日期顯示）",
    }


def _decimal(value: object) -> Decimal | None:
    if value in (None, "", "UNKNOWN"):
        return None
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        return None


def _compact_amount(value: Decimal | None) -> str:
    if value is None:
        return "UNKNOWN"
    if value >= Decimal("100000000"):
        return f"{value / Decimal('100000000'):.1f} 億"
    if value >= Decimal("10000"):
        return f"{value / Decimal('10000'):.1f} 萬"
    return f"{value:,.0f}"


def _daily_change_percent(closing_price: object, price_change: object) -> Decimal | None:
    close = _decimal(closing_price)
    change = _decimal(price_change)
    if close is None or change is None:
        return None
    previous_close = close - change
    if previous_close == 0:
        return None
    return change / previous_close * Decimal("100")


def _heatmap_layout(items: list[dict], columns: int = 5) -> list[dict]:
    """Create a strip treemap whose rectangle area follows trade value."""
    total = sum((item["trade_value_number"] for item in items), Decimal("0"))
    if total <= 0:
        return []
    rows = [items[index : index + columns] for index in range(0, len(items), columns)]
    y = Decimal("0")
    output: list[dict] = []
    for row_index, row in enumerate(rows):
        row_total = sum((item["trade_value_number"] for item in row), Decimal("0"))
        height = (row_total / total * Decimal("100")) if row_index < len(rows) - 1 else Decimal("100") - y
        x = Decimal("0")
        for item_index, item in enumerate(row):
            width = (
                item["trade_value_number"] / row_total * Decimal("100")
                if item_index < len(row) - 1
                else Decimal("100") - x
            )
            output.append({**item, "left": float(x), "top": float(y), "width": float(width), "height": float(height)})
            x += width
        y += height
    return output


def _hotspot_category(text: str) -> str:
    value = text.lower()
    if any(term in value for term in ("semiconductor", "nvidia", "tsmc", "openai", " ai ", "chip")):
        return "半導體與 AI"
    if any(term in value for term in ("fed", "cpi", "inflation", "interest rate", "央行", "利率")):
        return "宏觀與政策"
    if any(term in value for term in ("war", "sanction", "geopolit", "tariff", "戰爭", "制裁", "關稅")):
        return "國際與地緣事件"
    if any(term in value for term in ("nasdaq", "s&p", "dow jones", "nyse", "美股")):
        return "美國市場"
    if any(term in value for term in ("twse", "台股", "櫃買", "上市", "上櫃")):
        return "台股與公司"
    return "其他"


def _short_excerpt(text: str, limit: int = 116) -> str:
    cleaned = re.sub(r"https?://\S+", "", text or "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return "原文主要為來源連結，請開啟原帖查看。"
    return cleaned if len(cleaned) <= limit else f"{cleaned[:limit].rstrip()}…"


def _signal_explanation(signal_type: str) -> str:
    return {
        "HIGH_TRADE_VOLUME": "成交量進入官方資料的規則排序前段，適合再查量價是否同步。",
        "HIGH_TRADE_VALUE": "成交金額進入官方資料的規則排序前段，代表市場資金關注度較高。",
        "NOTABLE_DAILY_CHANGE": "單日漲跌幅進入規則排序前段，值得回查公告與事件來源。",
        "FOREIGN_HOLDING_RATIO": "官方產業彙總的外資及陸資持股比例較高，僅供產業研究。",
    }.get(signal_type, "規則條件被觸發，值得進一步回查官方資料。")


def _latest_timestamp(*values: str | None) -> str:
    parsed: list[datetime] = []
    for value in values:
        if not value:
            continue
        try:
            parsed.append(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            continue
    if not parsed:
        return "UNKNOWN"
    latest = max(item.astimezone(timezone.utc) for item in parsed)
    local = latest.astimezone(timezone(timedelta(hours=8)))
    return local.strftime("%Y-%m-%d %H:%M:%S UTC+8")


def create_app(
    database_path: str | Path | None = None,
    dataset_config_path: str | Path | None = None,
    *,
    collector_factory=None,
    normalizer_factory=None,
) -> Flask:
    app = Flask(__name__)
    app.config["DATABASE_PATH"] = str(database_path or PROJECT_ROOT / "data" / "taiwan-demo.db")
    app.config["DATASET_CONFIG_PATH"] = str(
        dataset_config_path or PROJECT_ROOT / "config" / "twse_openapi.datasets.json"
    )
    app.config["ANOMALY_CONFIG_PATH"] = str(PROJECT_ROOT / "config" / "anomaly_rules.v0.1.json")
    stock_workbench_cache: dict[str, object] = {}
    dataset_config = load_twse_config(app.config["DATASET_CONFIG_PATH"])
    datasets_by_endpoint = {dataset["endpoint"]: dataset for dataset in dataset_config["datasets"]}
    app.jinja_env.filters["status_class"] = _status_class
    app.jinja_env.filters["signal_title"] = _signal_title
    app.jinja_env.filters["freshness_label"] = _freshness_label
    app.jinja_env.filters["zh"] = localize_zh
    app.jinja_env.filters["taipei_time"] = taipei_time

    def make_collector(connection):
        if collector_factory:
            return collector_factory(connection, dataset_config)
        return TwseOpenApiCollector(connection, dataset_config)

    def make_normalizer(connection):
        if normalizer_factory:
            return normalizer_factory(connection, dataset_config)
        return TwseNormalizationService(connection, dataset_config)

    @app.get("/health")
    def health():
        return {"status": "ok", "market": "TW"}

    @app.get("/channel-radar")
    def channel_radar():
        selected_date = request.args.get("date", "").strip()
        if selected_date and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", selected_date):
            abort(400)
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            payload = (
                channel_brief_payload_for_date(connection, selected_date)
                if selected_date else latest_channel_brief_payload(connection)
            )
            dates = [
                row["market_session_date"]
                for row in connection.execute(
                    """SELECT DISTINCT market_session_date
                       FROM ben_channel_brief_runs
                       WHERE session_state IN ('READY','DEGRADED')
                       ORDER BY market_session_date DESC"""
                )
            ] if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ben_channel_brief_runs'"
            ).fetchone() else []
        finally:
            connection.close()
        return render_template(
            "channel_radar.html",
            payload=payload,
            dates=dates,
            selected_date=selected_date or (payload or {}).get("market_session_date", ""),
            language="zh-tw",
        )

    @app.get("/")
    def dashboard():
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            counts = connection.execute(
                """
                SELECT
                    COUNT(*) AS source_count,
                    SUM(CASE WHEN collection_status = 'API_VERIFIED' THEN 1 ELSE 0 END) AS api_count,
                    SUM(CASE WHEN collection_status LIKE 'NEEDS_%'
                                  OR collection_status LIKE 'BLOCKED_%'
                             THEN 1 ELSE 0 END) AS restricted_count
                FROM sources s
                JOIN markets m ON m.id = s.market_id
                WHERE m.country_code = 'TW'
                """
            ).fetchone()
            raw_count = connection.execute("SELECT COUNT(*) FROM raw_items").fetchone()[0]
            normalized_count = connection.execute(
                "SELECT COUNT(*) FROM normalized_items"
            ).fetchone()[0]
            signal_count = connection.execute(
                "SELECT COUNT(*) FROM official_signal_cards"
            ).fetchone()[0]
            latest_data_date = connection.execute(
                """
                SELECT MAX(NULLIF(data_date, 'UNKNOWN'))
                FROM normalized_items
                WHERE record_type IN (
                    'LISTED_SECURITY_DAILY_TRADING', 'MARKET_CLOSE_STATISTIC'
                )
                """
            ).fetchone()[0]
            latest = connection.execute(
                """
                SELECT batch_id, MAX(finished_at) AS finished_at,
                       CASE
                         WHEN SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) = 0 THEN 'SUCCESS'
                         WHEN SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) > 0 THEN 'PARTIAL_FAILED'
                         ELSE 'FAILED'
                       END AS status,
                       SUM(item_count) AS fetched_count,
                       SUM(new_item_count) AS new_count,
                       SUM(duplicate_item_count) AS duplicate_count
                FROM collection_runs
                WHERE batch_id = (
                    SELECT batch_id FROM collection_runs
                    WHERE batch_id IS NOT NULL
                    ORDER BY started_at DESC LIMIT 1
                )
                GROUP BY batch_id
                """
            ).fetchone()
            recent_runs = connection.execute(
                """
                SELECT cr.*, s.source_id AS registry_source_id
                FROM collection_runs cr JOIN sources s ON s.id = cr.source_id
                ORDER BY cr.started_at DESC LIMIT 6
                """
            ).fetchall()
        finally:
            connection.close()
        return render_template(
            "dashboard.html",
            counts=counts,
            raw_count=raw_count,
            normalized_count=normalized_count,
            signal_count=signal_count,
            freshness=_homepage_freshness(latest_data_date),
            latest=latest,
            recent_runs=recent_runs,
            sync=request.args,
        )

    @app.post("/sync")
    def sync_twse():
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            batch = make_collector(connection).collect_all(dataset_config["source_id"])
            normalized = make_normalizer(connection).normalize_all(dataset_config["source_id"])
            return redirect(
                url_for(
                    "dashboard",
                    sync_status=batch.status,
                    fetched=batch.fetched_count,
                    new=batch.new_count,
                    duplicate=batch.duplicate_count,
                    normalized=normalized.normalized_new_count,
                    signals=normalized.signal_new_count,
                )
            )
        except ValidationError as error:
            return redirect(url_for("dashboard", sync_status="FAILED", error=str(error)))
        finally:
            connection.close()

    @app.get("/sources")
    def sources():
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            rows = connection.execute(
                """
                SELECT s.* FROM sources s
                JOIN markets m ON m.id = s.market_id
                WHERE m.country_code = 'TW'
                ORDER BY s.reliability_level, s.source_id
                """
            ).fetchall()
        finally:
            connection.close()
        return render_template("sources.html", sources=rows)

    @app.get("/radar")
    def radar_health():
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            counts = connection.execute(
                """
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN monitoring_status = 'ACTIVE' THEN 1 ELSE 0 END) AS active,
                       SUM(CASE WHEN monitoring_status = 'NEEDS_VERIFICATION' THEN 1 ELSE 0 END) AS needs,
                       SUM(CASE WHEN monitoring_status = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked,
                       SUM(CASE WHEN platform = 'X' AND monitoring_status = 'ACTIVE' THEN 1 ELSE 0 END) AS x_active,
                       SUM(CASE WHEN platform = 'YOUTUBE' AND monitoring_status = 'ACTIVE' THEN 1 ELSE 0 END) AS youtube_active,
                       SUM(CASE WHEN terms_status = 'UNKNOWN' THEN 1 ELSE 0 END) AS terms_unknown,
                       SUM(CASE WHEN commercial_use_status = 'UNKNOWN' THEN 1 ELSE 0 END) AS commercial_unknown,
                       COUNT(DISTINCT CASE WHEN monitoring_status = 'ACTIVE'
                                           THEN publisher_group END) AS independent_groups,
                       MAX(last_success_at) AS last_success_at
                FROM realtime_sources
                """
            ).fetchone()
            rows = connection.execute(
                """
                SELECT rs.*,
                       (SELECT AVG(ri.detection_latency_minutes)
                        FROM radar_items ri WHERE ri.realtime_source_id = rs.id
                          AND ri.is_initial_backfill = 0) AS average_latency,
                       (SELECT rr.status FROM radar_runs rr
                        WHERE rr.realtime_source_id = rs.id
                        ORDER BY rr.started_at DESC LIMIT 1) AS latest_run_status
                FROM realtime_sources rs
                ORDER BY CASE rs.monitoring_status
                    WHEN 'ACTIVE' THEN 1
                    WHEN 'NEEDS_VERIFICATION' THEN 2
                    WHEN 'MANUAL_ONLY' THEN 3
                    WHEN 'BLOCKED' THEN 4 ELSE 5 END,
                    rs.platform, rs.registry_source_id
                """
            ).fetchall()
            cycles = connection.execute(
                """
                SELECT cycle_id, MIN(started_at) AS started_at, MAX(finished_at) AS finished_at,
                       COUNT(*) AS source_count,
                       SUM(CASE WHEN status = 'SUCCESS' THEN 1 ELSE 0 END) AS success_count,
                       SUM(new_count) AS new_count, SUM(duplicate_count) AS duplicate_count
                FROM radar_runs GROUP BY cycle_id ORDER BY started_at DESC LIMIT 10
                """
            ).fetchall()
            yahoo_diagnostics = connection.execute(
                """SELECT * FROM ben_endpoint_diagnostics WHERE source_key='yahoo_finance'
                   AND attempted_at=(SELECT MAX(attempted_at) FROM ben_endpoint_diagnostics WHERE source_key='yahoo_finance')
                   ORDER BY endpoint_url"""
            ).fetchall()
            ben_news_runs = connection.execute(
                """SELECT current.* FROM ben_news_runs current
                   WHERE current.attempted_at=(
                       SELECT MAX(candidate.attempted_at) FROM ben_news_runs candidate
                       WHERE candidate.source_key=current.source_key
                   ) ORDER BY current.source_name"""
            ).fetchall()
        finally:
            connection.close()
        return render_template(
            "radar_health.html", counts=counts, sources=rows, cycles=cycles,
            yahoo_diagnostics=yahoo_diagnostics, ben_news_runs=ben_news_runs,
        )

    @app.get("/radar/feed")
    def radar_feed():
        try:
            hours = min(72, max(1, int(request.args.get("hours", "2"))))
        except ValueError:
            hours = 2
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            rows = connection.execute(
                """
                SELECT ri.*, rs.platform, rs.registry_source_id,
                       raw.content_hash, raw.id AS evidence_id
                FROM radar_items ri
                JOIN realtime_sources rs ON rs.id = ri.realtime_source_id
                JOIN raw_items raw ON raw.id = ri.raw_item_id
                WHERE ri.discovered_at >= ?
                ORDER BY ri.discovered_at DESC, ri.published_at DESC
                LIMIT 500
                """,
                (cutoff,),
            ).fetchall()
        finally:
            connection.close()
        return render_template("radar_feed.html", items=rows, hours=hours)

    @app.get("/stock-radar")
    @app.get("/ai-radar")
    def ai_market_radar():
        window = request.args.get("window", "24")
        if window not in {"6", "12", "24"}:
            window = "24"
        language = "zh-cn" if request.args.get("lang") == "zh-cn" else "zh-tw"
        source_filter = request.args.get("source", "all")
        if source_filter not in {"all", "news", "x"}:
            source_filter = "all"
        category_filter = request.args.get("category", "all").upper()
        if category_filter not in {"ALL", "TW", "US", "AI", "MACRO", "OTHER"}:
            category_filter = "ALL"
        sort = request.args.get("sort", "heat")
        if sort not in {"heat", "growth", "discussion", "latest", "impact"}:
            sort = "heat"
        show_all = request.args.get("show") == "all"
        now = datetime.now(timezone.utc)
        cutoff_24 = (now - timedelta(hours=24)).isoformat()
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            all_news = [dict(row) for row in connection.execute(
                "SELECT * FROM ben_news_items WHERE published_at >= ? ORDER BY published_at DESC",
                (cutoff_24,),
            ).fetchall()]
            all_x = [dict(row) for row in connection.execute(
                """SELECT posts.*, accounts.market_scope, accounts.impact_path
                   FROM ben_x_posts posts JOIN ben_x_accounts accounts ON accounts.id=posts.account_id
                   WHERE posts.created_at >= ? ORDER BY posts.created_at DESC""",
                (cutoff_24,),
            ).fetchall()]
            news_24 = filter_time_window(all_news, now=now, hours=24, field="published_at")
            news_2 = filter_time_window(all_news, now=now, hours=2, field="published_at")
            x_24 = filter_time_window(all_x, now=now, hours=24, field="created_at")
            x_2 = filter_time_window(all_x, now=now, hours=2, field="created_at")
            anomalies, pool_count, history_valid_count = compute_anomalies(connection, news_24)
            snapshots: dict[str, list[dict]] = {}
            for snapshot in connection.execute(
                "SELECT * FROM ben_x_engagement_snapshots WHERE fetched_at >= ? ORDER BY fetched_at",
                (cutoff_24,),
            ).fetchall():
                snapshots.setdefault(str(snapshot["post_id"]), []).append(dict(snapshot))
            events_by_window: dict[str, list[dict]] = {}
            quality_by_window: dict[str, dict] = {}
            raw_by_window: dict[str, dict] = {}
            for hours in (6, 12, 24):
                news_window = filter_time_window(all_news, now=now, hours=hours, field="published_at")
                x_window = filter_time_window(all_x, now=now, hours=hours, field="created_at")
                events_window = build_unified_events(
                    news_window, x_window, now=now, engagement_snapshots=snapshots,
                    translation_adapter=TranslationSummaryAdapter(connection),
                    target_language=language,
                )
                attach_market_response(events_window, anomalies)
                events_by_window[str(hours)] = events_window
                quality_by_window[str(hours)] = cluster_quality_report(
                    events_window, raw_news_count=len(news_window), raw_x_count=len(x_window)
                )
                raw_by_window[str(hours)] = {"news": news_window, "x": x_window}
            events_24_all = events_by_window["24"]
            if "payload" not in stock_workbench_cache:
                try:
                    stock_workbench_cache["payload"] = build_stock_workbench(
                        connection, config_path=app.config["ANOMALY_CONFIG_PATH"]
                    )
                except (ValueError, sqlite3.OperationalError):
                    stock_workbench_cache["payload"] = {
                        "status": "UNAVAILABLE", "replay_date": "UNKNOWN", "data_status": "EOD",
                        "top20": [], "early_momentum": [], "persistent": [], "details": {},
                        "participating": {"TWSE": 0, "TPEX": 0}, "participating_total": 0,
                        "replay_dates": [], "rule_version": "UNKNOWN", "rule_labels": {},
                    }
            stock_workbench = stock_workbench_cache["payload"]
            latest_runs = connection.execute(
                """SELECT current.* FROM ben_news_runs current
                   WHERE current.attempted_at = (
                       SELECT MAX(candidate.attempted_at) FROM ben_news_runs candidate
                       WHERE candidate.source_key = current.source_key
                   ) ORDER BY current.source_name"""
            ).fetchall()
            usable_source_count = sum(1 for row in latest_runs if row["status"] == "SUCCESS" and row["valid_item_count"] > 0)
            x_account_counts = connection.execute(
                """SELECT COUNT(*) AS total,
                          SUM(CASE WHEN monitoring_status IN ('SUCCESS','NO_NEW') THEN 1 ELSE 0 END) AS successful
                   FROM ben_x_accounts"""
            ).fetchone()
            last_updated = connection.execute(
                """SELECT MAX(value) FROM (
                       SELECT MAX(fetched_at) AS value FROM ben_news_items
                       UNION ALL SELECT MAX(fetched_at) FROM ben_x_posts
                   )"""
            ).fetchone()[0] or "UNKNOWN"
            official_data_date = stock_workbench["replay_date"]
        finally:
            connection.close()
        selected_all = list(events_by_window[window])
        if source_filter == "news":
            selected_all = [event for event in selected_all if event["news_items"]]
        elif source_filter == "x":
            selected_all = [event for event in selected_all if event["x_items"]]
        if category_filter != "ALL":
            selected_all = [event for event in selected_all if category_filter in event["categories"]]
        if sort == "growth":
            selected_all.sort(key=lambda event: (event["acceleration_pct"] if event["acceleration_pct"] is not None else -10_000, event["score"]), reverse=True)
        elif sort == "discussion":
            selected_all.sort(key=lambda event: (event["independent_count"], len(event["items"]), event["score"]), reverse=True)
        elif sort == "latest":
            selected_all.sort(key=lambda event: event["latest_update_at"], reverse=True)
        elif sort == "impact":
            selected_all.sort(key=lambda event: (event["score_dimensions"]["market_response"], event["content_score"], event["score"]), reverse=True)
        else:
            selected_all.sort(key=lambda event: (event["score"], event["latest_update_at"]), reverse=True)
        category_counts = {key: 0 for key in ("ALL", "TW", "US", "AI", "MACRO", "OTHER")}
        for event in events_by_window[window]:
            category_counts["ALL"] += 1
            for key in event["categories"]:
                category_counts[key] += 1
        top_event = max(selected_all, key=lambda event: event["score"], default=None)
        fastest_event = max(
            (event for event in selected_all if event["acceleration_pct"] is not None),
            key=lambda event: event["acceleration_pct"], default=None,
        )
        broadest_event = max(selected_all, key=lambda event: event["independent_count"], default=None)
        default_limit = 16
        if show_all:
            selected_events = selected_all
        elif sort == "heat" and source_filter == "all" and category_filter == "ALL":
            selected_events = select_snapshot_events(selected_all, default_limit)
        else:
            selected_events = selected_all[:default_limit]
        snapshot_concentration = source_concentration(selected_events)
        full_concentration = source_concentration(events_by_window[window])
        source_coverage = {
            "window_hours": int(window),
            "news_items": len(raw_by_window[window]["news"]),
            "x_items": len(raw_by_window[window]["x"]),
            "news_events": sum(bool(event["news_items"]) for event in events_by_window[window]),
            "x_events": sum(bool(event["x_items"]) for event in events_by_window[window]),
            "cross_platform_events": sum(event["type"] == "NEWS_X" for event in events_by_window[window]),
            "stock_linked_events": sum(bool(event.get("entities")) for event in events_by_window[window]),
            "snapshot_concentration": snapshot_concentration,
            "full_window_concentration": full_concentration,
        }
        return render_template(
            "ai_market_radar.html", window=window, language=language,
            source_filter=source_filter, category_filter=category_filter, sort=sort,
            show_all=show_all, events=selected_events, events_total=len(selected_all),
            events_24_all=events_24_all, raw_window=raw_by_window[window],
            quality=quality_by_window[window], category_counts=category_counts,
            top_event=top_event, fastest_event=fastest_event, broadest_event=broadest_event,
            anomalies=anomalies, pool_count=pool_count, history_valid_count=history_valid_count,
            usable_source_count=usable_source_count, last_updated=last_updated,
            x_account_counts=x_account_counts, official_data_date=official_data_date,
            stock_workbench=stock_workbench, source_coverage=source_coverage,
            snapshot_metadata={
                "selection_method": "score_with_marginal_source_concentration_penalty_v1",
                "window_hours": int(window),
                "selected_count": len(selected_events),
                "source_concentration_status": snapshot_concentration["status"],
            },
            test_mode=request.args.get("test") == "ben",
        )

    @app.get("/stock-radar/cluster-diagnostics")
    def stock_radar_cluster_diagnostics():
        hours = request.args.get("hours", "24")
        if hours not in {"6", "12", "24", "72"}:
            hours = "24"
        now = datetime.now(timezone.utc)
        cutoff = (now - timedelta(hours=int(hours))).isoformat()
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            news = [dict(row) for row in connection.execute(
                "SELECT * FROM ben_news_items WHERE published_at >= ? ORDER BY published_at DESC", (cutoff,)
            )]
            x_rows = [dict(row) for row in connection.execute(
                """SELECT posts.*, accounts.market_scope, accounts.impact_path
                   FROM ben_x_posts posts JOIN ben_x_accounts accounts ON accounts.id=posts.account_id
                   WHERE posts.created_at >= ? ORDER BY posts.created_at DESC""", (cutoff,)
            )]
        finally:
            connection.close()
        diagnostics = cluster_diagnostic_report(news, x_rows, now=now)
        return render_template(
            "cluster_diagnostics.html", hours=hours, diagnostics=diagnostics,
            same_count=sum(row["decision"]["label"] == "SAME_EVENT" for row in diagnostics),
            related_count=sum(row["decision"]["label"] == "RELATED_BUT_DISTINCT" for row in diagnostics),
            different_count=sum(row["decision"]["label"] == "DIFFERENT_EVENT" for row in diagnostics),
        )

    @app.get("/runs")
    def runs():
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            rows = connection.execute(
                """
                SELECT cr.*, s.source_id AS registry_source_id, s.publisher
                FROM collection_runs cr JOIN sources s ON s.id = cr.source_id
                ORDER BY cr.started_at DESC LIMIT 100
                """
            ).fetchall()
        finally:
            connection.close()
        return render_template("runs.html", runs=rows)

    @app.get("/evidence")
    def evidence():
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            rows = connection.execute(
                """
                SELECT ri.*, s.source_id AS registry_source_id, s.publisher, s.publisher_group,
                       cr.dataset_name, cr.endpoint
                FROM raw_items ri
                JOIN sources s ON s.id = ri.source_id
                LEFT JOIN collection_runs cr ON cr.id = ri.collection_run_id
                ORDER BY ri.fetched_at DESC, ri.created_at DESC LIMIT 200
                """
            ).fetchall()
            evidence_rows = [
                {
                    **dict(row),
                    "summary": _summary(
                        row["raw_payload_json"], datasets_by_endpoint.get(row["endpoint"])
                    ),
                }
                for row in rows
            ]
        finally:
            connection.close()
        return render_template("evidence.html", evidence_rows=evidence_rows)

    @app.get("/evidence/<item_id>")
    def evidence_detail(item_id: str):
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            row = connection.execute(
                """
                SELECT ri.*, s.source_id AS registry_source_id, s.publisher, s.publisher_group,
                       cr.dataset_name, cr.endpoint, cr.status AS run_status,
                       cr.started_at AS run_started_at, cr.finished_at AS run_finished_at
                FROM raw_items ri
                JOIN sources s ON s.id = ri.source_id
                LEFT JOIN collection_runs cr ON cr.id = ri.collection_run_id
                WHERE ri.id = ?
                """,
                (item_id,),
            ).fetchone()
            if row is None:
                abort(404)
            try:
                pretty_json = json.dumps(
                    json.loads(row["raw_payload_json"]), ensure_ascii=False, indent=2
                )
            except json.JSONDecodeError:
                pretty_json = row["raw_payload_json"]
        finally:
            connection.close()
        return render_template("evidence_detail.html", item=row, pretty_json=pretty_json)

    @app.get("/compliance")
    def compliance():
        connection = _connection(app.config["DATABASE_PATH"])
        try:
            snapshot_count = connection.execute(
                "SELECT COUNT(*) FROM policy_snapshots"
            ).fetchone()[0]
            rule_count = connection.execute("SELECT COUNT(*) FROM policy_rules").fetchone()[0]
            last_verified_at = connection.execute(
                """
                SELECT MAX(fetched_at) FROM policy_snapshots
                WHERE verification_status = 'VERIFIED_OFFICIAL_HTTP_200'
                """
            ).fetchone()[0]
            snapshots = connection.execute(
                """
                SELECT current.*, previous.snapshot_version AS previous_version
                FROM policy_snapshots current
                LEFT JOIN policy_snapshots previous
                  ON previous.id = current.supersedes_snapshot_id
                ORDER BY current.fetched_at DESC, current.policy_name
                """
            ).fetchall()
            rules = connection.execute(
                """
                SELECT pr.* FROM policy_rules pr
                JOIN policy_snapshots ps ON ps.id = pr.snapshot_id
                WHERE ps.id IN (
                    SELECT latest.id FROM policy_snapshots latest
                    WHERE latest.fetched_at = (
                        SELECT MAX(candidate.fetched_at)
                        FROM policy_snapshots candidate
                        WHERE COALESCE(candidate.source_url, candidate.policy_url) =
                              COALESCE(latest.source_url, latest.policy_url)
                    )
                )
                ORDER BY CASE pr.country WHEN 'TW' THEN 1 WHEN 'US' THEN 2 ELSE 3 END,
                         pr.product_category, pr.rule_id
                """
            ).fetchall()
            checklist_rows = connection.execute(
                """
                SELECT * FROM policy_checklist_templates
                WHERE status = 'ACTIVE'
                ORDER BY country, product_category
                """
            ).fetchall()
            checklists = []
            for row in checklist_rows:
                facts = json.loads(row["fields_json"])
                outcome = run_financial_ads_precheck(connection, facts)
                checklists.append(
                    {
                        **dict(row),
                        "fields": facts,
                        "missing_fields": [
                            key for key, value in facts.items() if value == "UNKNOWN"
                        ],
                        "precheck": outcome,
                    }
                )
        finally:
            connection.close()
        return render_template(
            "compliance.html",
            snapshot_count=snapshot_count,
            rule_count=rule_count,
            last_verified_at=last_verified_at or "UNKNOWN",
            snapshots=snapshots,
            rules=rules,
            checklists=checklists,
        )

    @app.get("/signals")
    def signals():
        date_filter = request.args.get("date", "").strip()
        code_filter = request.args.get("stock_code", "").strip()[:32]
        try:
            page = max(1, int(request.args.get("page", "1")))
        except ValueError:
            page = 1
        per_page = 24
        where = ["sc.signal_label = 'RULE_BASED_OFFICIAL_SIGNAL'"]
        parameters: list[str] = []
        if date_filter:
            where.append("sc.data_date = ?")
            parameters.append(date_filter)
        if code_filter:
            where.append("ni.stock_code LIKE ?")
            parameters.append(f"%{code_filter}%")
        where_sql = " AND ".join(where)

        connection = _connection(app.config["DATABASE_PATH"])
        try:
            total = connection.execute(
                f"""
                SELECT COUNT(*)
                FROM official_signal_cards sc
                JOIN normalized_items ni ON ni.id = sc.normalized_item_id
                WHERE {where_sql}
                """,
                parameters,
            ).fetchone()[0]
            total_pages = max(1, (total + per_page - 1) // per_page)
            page = min(page, total_pages)
            rows = connection.execute(
                f"""
                SELECT sc.*, ni.stock_code, ni.company_name, ni.industry_category,
                       ni.record_type, ri.fetched_at, s.publisher
                FROM official_signal_cards sc
                JOIN normalized_items ni ON ni.id = sc.normalized_item_id
                JOIN raw_items ri ON ri.id = sc.evidence_raw_item_id
                JOIN sources s ON s.id = ri.source_id
                WHERE {where_sql}
                ORDER BY CASE WHEN sc.data_date = 'UNKNOWN' THEN 1 ELSE 0 END,
                         sc.data_date DESC, sc.signal_type, ni.stock_code, ni.industry_category
                LIMIT ? OFFSET ?
                """,
                (*parameters, per_page, (page - 1) * per_page),
            ).fetchall()
            dates = connection.execute(
                """
                SELECT DISTINCT data_date FROM official_signal_cards
                ORDER BY CASE WHEN data_date = 'UNKNOWN' THEN 1 ELSE 0 END, data_date DESC
                """
            ).fetchall()
        finally:
            connection.close()
        return render_template(
            "signals.html",
            cards=rows,
            dates=dates,
            date_filter=date_filter,
            code_filter=code_filter,
            page=page,
            total=total,
            total_pages=total_pages,
        )

    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Taiwan official data local demo")
    parser.add_argument("--db", default=str(PROJECT_ROOT / "data" / "taiwan-demo.db"))
    parser.add_argument(
        "--dataset-config", default=str(PROJECT_ROOT / "config" / "twse_openapi.datasets.json")
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open-browser", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    app = create_app(args.db, args.dataset_config)
    if args.open_browser:
        threading.Timer(
            1.0, lambda: webbrowser.open(f"http://{args.host}:{args.port}/stock-radar")
        ).start()
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
