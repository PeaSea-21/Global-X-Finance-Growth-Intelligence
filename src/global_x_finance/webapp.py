from __future__ import annotations

import argparse
import json
import sqlite3
import threading
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

from .db import connect
from .errors import ValidationError
from .compliance import run_financial_ads_precheck
from .normalization import TwseNormalizationService
from .twse_collector import TwseOpenApiCollector, load_twse_config


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _connection(database_path: str | Path) -> sqlite3.Connection:
    return connect(database_path)


def _status_class(status: str | None) -> str:
    value = (status or "UNKNOWN").upper()
    if value in {"SUCCESS", "API_VERIFIED", "ACTIVE", "PASS_PRECHECK", "VERIFIED_OFFICIAL_HTTP_200"}:
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
    dataset_config = load_twse_config(app.config["DATASET_CONFIG_PATH"])
    datasets_by_endpoint = {dataset["endpoint"]: dataset for dataset in dataset_config["datasets"]}
    app.jinja_env.filters["status_class"] = _status_class
    app.jinja_env.filters["signal_title"] = _signal_title
    app.jinja_env.filters["freshness_label"] = _freshness_label

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
                       SUM(CASE WHEN source_status = 'VERIFIED_ACTIVE' THEN 1 ELSE 0 END) AS active,
                       SUM(CASE WHEN source_status = 'NEEDS_VERIFICATION' THEN 1 ELSE 0 END) AS needs,
                       SUM(CASE WHEN source_status = 'BLOCKED' THEN 1 ELSE 0 END) AS blocked,
                       COUNT(DISTINCT CASE WHEN source_status = 'VERIFIED_ACTIVE'
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
                ORDER BY CASE rs.source_status
                    WHEN 'VERIFIED_ACTIVE' THEN 1
                    WHEN 'NEEDS_VERIFICATION' THEN 2
                    WHEN 'VERIFIED_MANUAL_ONLY' THEN 3
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
        finally:
            connection.close()
        return render_template("radar_health.html", counts=counts, sources=rows, cycles=cycles)

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
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{args.host}:{args.port}/")).start()
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
