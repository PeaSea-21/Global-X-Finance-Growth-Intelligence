from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol

from .anomaly_engine import AnomalyEngine, AnomalyRuleConfig, complete_replay_dates
from .x_intelligence import build_unified_events


TAIPEI = timezone(timedelta(hours=8))
PRIMARY_LIMIT = 5


@dataclass(frozen=True)
class ChannelProfile:
    channel_id: str
    channel_name: str
    channel_type: str
    profile_version: str
    profile_status: str
    daily_target: int
    summary: str
    fixed_boundary: str
    preferred_candidate_types: tuple[str, ...]
    required_fields: tuple[str, ...]
    market: str
    timezone: str
    primary_build_time: str


class ChannelRanker(Protocol):
    method: str
    detail: dict[str, Any]

    def rank(
        self, profile: ChannelProfile, candidates: list[dict[str, Any]]
    ) -> list[tuple[str, list[str]]]: ...


class RuleBasedChannelRanker:
    method = "RULE_BASED_FALLBACK"
    detail = {
        "reason": "NO_PRODUCTION_MODEL_PROVIDER",
        "version": "channel-rule-rank-v0.1",
    }

    def rank(
        self, profile: ChannelProfile, candidates: list[dict[str, Any]]
    ) -> list[tuple[str, list[str]]]:
        ordered = sorted(candidates, key=lambda row: self._key(profile, row))
        return [
            (row["candidate_id"], self._reasons(profile, row))
            for row in ordered
        ]

    @staticmethod
    def _key(profile: ChannelProfile, row: dict[str, Any]) -> tuple[Any, ...]:
        metrics = row.get("sort_metrics", {})
        if profile.channel_type == "SIGNAL_HEAVY":
            return (
                -int(metrics.get("rule_count", 0)),
                -int(metrics.get("price_volume", 0)),
                -float(metrics.get("volume_ratio", 0)),
                -float(metrics.get("abs_price_zscore", 0)),
                row["candidate_id"],
            )
        if profile.channel_type == "EVENT_HEAVY":
            type_priority = {"DISCLOSURE": 0, "NEWS_EVENT": 1, "X_EVENT": 2, "MARKET_SIGNAL": 3}
            return (
                type_priority.get(row["candidate_type"], 9),
                -int(metrics.get("official_evidence", 0)),
                -int(metrics.get("independent_sources", 0)),
                -float(metrics.get("abs_change_pct", 0)),
                -float(metrics.get("abs_price_zscore", 0)),
                -int(metrics.get("rule_count", 0)),
                -float(metrics.get("volume_ratio", 0)),
                row["candidate_id"],
            )
        return (
            -int(metrics.get("security_count", 0)),
            -int(metrics.get("total_rule_count", 0)),
            -float(metrics.get("average_volume_ratio", 0)),
            row["candidate_id"],
        )

    @staticmethod
    def _reasons(profile: ChannelProfile, row: dict[str, Any]) -> list[str]:
        metrics = row.get("sort_metrics", {})
        if profile.channel_type == "SIGNAL_HEAVY":
            return [
                f"命中{int(metrics.get('rule_count', 0))}项可解释价量规则",
                f"RVOL {float(metrics.get('volume_ratio', 0)):.2f}倍",
                "排序只使用当日EOD与此前历史基线",
            ]
        if profile.channel_type == "EVENT_HEAVY":
            return [
                f"候选类型为{row['candidate_type']}",
                f"可回链Evidence {len(row.get('evidence', [])) + len(row.get('opinion_evidence', []))}项",
                "公司事件优先于催化剂未确认的纯行情异常",
            ]
        return [
            f"同一官方产业内有{int(metrics.get('security_count', 0))}家公司出现异常",
            f"合计命中{int(metrics.get('total_rule_count', 0))}项价量规则",
            "产业共现仅用于选题召回，不作为因果证明",
        ]


def load_channel_pilot_config(path: str | Path) -> tuple[dict[str, Any], list[ChannelProfile]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {
        "config_version", "market", "timezone", "regular_close_time",
        "primary_build_time", "minimum_market_coverage", "profiles",
    }
    missing = sorted(required - set(raw))
    if missing:
        raise ValueError(f"Channel pilot config missing fields: {', '.join(missing)}")
    profiles = [
        ChannelProfile(
            channel_id=row["channel_id"],
            channel_name=row["channel_name"],
            channel_type=row["channel_type"],
            profile_version=row["profile_version"],
            profile_status=row["profile_status"],
            daily_target=int(row["daily_target"]),
            summary=row["summary"],
            fixed_boundary=row["fixed_boundary"],
            preferred_candidate_types=tuple(row["preferred_candidate_types"]),
            required_fields=tuple(row["required_fields"]),
            market=raw["market"],
            timezone=raw["timezone"],
            primary_build_time=raw["primary_build_time"],
        )
        for row in raw["profiles"]
    ]
    if {row.channel_type for row in profiles} != {
        "SIGNAL_HEAVY", "EVENT_HEAVY", "CROSS_ENTITY"
    }:
        raise ValueError("P06B config must contain exactly the three approved pilot types")
    return raw, profiles


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _as_of_for_session(session_date: str, build_time: str) -> datetime:
    hour, minute = (int(part) for part in build_time.split(":", 1))
    return datetime.combine(date.fromisoformat(session_date), time(hour, minute), TAIPEI)


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    return connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone() is not None


def _source_readiness(
    connection: sqlite3.Connection,
    *,
    replay_date: str,
    as_of: datetime,
    minimum_coverage: float,
    lookback_hours: int,
    include_x: bool = True,
) -> tuple[str, str, list[dict[str, Any]]]:
    totals = {
        row["exchange_code"]: int(row["count"])
        for row in connection.execute(
            """SELECT exchange_code, COUNT(*) AS count FROM official_securities
               WHERE exchange_code IN ('TWSE','TPEX') GROUP BY exchange_code"""
        )
    }
    eod_counts = {
        row["exchange_code"]: int(row["count"])
        for row in connection.execute(
            """SELECT exchange_code, COUNT(*) AS count FROM official_market_data_daily
               WHERE trade_date=? AND data_status='EOD' GROUP BY exchange_code""",
            (replay_date,),
        )
    }
    market_rows = []
    eod_ready = True
    for exchange in ("TWSE", "TPEX"):
        total = totals.get(exchange, 0)
        count = eod_counts.get(exchange, 0)
        ratio = count / total if total else 0.0
        ready = ratio >= minimum_coverage
        eod_ready = eod_ready and ready
        market_rows.append({
            "source": f"{exchange}_EOD",
            "required": True,
            "status": "READY" if ready else "SOURCE_PENDING",
            "data_as_of": replay_date,
            "record_count": count,
            "coverage_ratio": ratio,
        })

    window_start = as_of - timedelta(hours=lookback_hours)

    def within_window(value: Any) -> bool:
        parsed = _parse_datetime(value)
        return parsed is not None and window_start <= parsed.astimezone(TAIPEI) <= as_of

    news_count = sum(
        within_window(row["published_at"])
        for row in connection.execute("SELECT published_at FROM ben_news_items")
    )
    x_count = (
        sum(
            within_window(row["created_at"])
            for row in connection.execute("SELECT created_at FROM ben_x_posts")
        )
        if include_x else 0
    )
    disclosure_count = 0
    for row in connection.execute("SELECT announced_at FROM official_disclosures"):
        announced = _parse_datetime(row["announced_at"])
        if announced and window_start <= announced.astimezone(TAIPEI) <= as_of:
            disclosure_count += 1
    mapping_count = (
        connection.execute(
            """SELECT COUNT(*) FROM security_industry_mappings
               WHERE mapping_status='MAPPED_COMMON_STOCK'"""
        ).fetchone()[0]
        if _table_exists(connection, "security_industry_mappings") else 0
    )
    market_rows.extend((
        {"source": "MOPS", "required": False, "status": "AVAILABLE" if disclosure_count else "EMPTY", "data_as_of": as_of.isoformat(), "record_count": disclosure_count},
        {"source": "NEWS", "required": False, "status": "AVAILABLE" if news_count else "EMPTY", "data_as_of": as_of.isoformat(), "record_count": news_count},
        {"source": "X", "required": False, "status": "AVAILABLE" if x_count else "EMPTY" if include_x else "DISABLED", "data_as_of": as_of.isoformat(), "record_count": x_count},
        {"source": "INDUSTRY_MAPPING", "required": False, "status": "AVAILABLE" if mapping_count else "NOT_APPLIED", "data_as_of": as_of.isoformat(), "record_count": mapping_count},
    ))
    if not eod_ready:
        return "SOURCE_PENDING", "EOD_INCOMPLETE", market_rows
    optional_missing = [row["source"] for row in market_rows if not row["required"] and row["status"] not in {"AVAILABLE", "READY", "DISABLED"}]
    if optional_missing:
        return "DEGRADED", "OPTIONAL_SOURCE_GAPS", market_rows
    return "READY", "COMPLETE_FOR_PILOT", market_rows


def _industry_map(connection: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    if not _table_exists(connection, "security_industry_mappings"):
        return {}
    return {
        row["security_id"]: dict(row)
        for row in connection.execute(
            """SELECT security_id, official_industry_code, official_industry_name,
                      normalized_sector, mapping_status, raw_item_id
               FROM security_industry_mappings"""
        )
    }


def _market_evidence(
    connection: sqlite3.Connection, security_id: str, replay_date: str
) -> list[dict[str, Any]]:
    row = connection.execute(
        """SELECT md.raw_item_id, md.collected_at, raw.canonical_url, raw.original_url,
                  s.source_id AS registry_source_id
           FROM official_market_data_daily md
           JOIN raw_items raw ON raw.id=md.raw_item_id
           JOIN sources s ON s.id=md.source_id
           WHERE md.security_id=? AND md.trade_date=?""",
        (security_id, replay_date),
    ).fetchone()
    if row is None:
        return []
    return [{
        "evidence_id": row["raw_item_id"],
        "evidence_class": "OFFICIAL_EOD",
        "source_id": row["registry_source_id"],
        "url": row["canonical_url"] or row["original_url"],
        "trade_date": replay_date,
        "collected_at": row["collected_at"],
        "observed_at": row["collected_at"],
        "epistemic_status": "FACT",
    }]


def _stock_detail(row: dict[str, Any], industry: dict[str, Any] | None) -> dict[str, Any]:
    metrics = row["raw_metrics"]
    return {
        "security_id": row["security_id"],
        "name": row["name"],
        "ticker": row["ticker"],
        "market": row["market"],
        "close": metrics.get("close"),
        "change_pct": metrics.get("change_pct"),
        "current_volume": metrics.get("current_volume"),
        "median_volume_20d": metrics.get("median_volume_20d"),
        "volume_ratio": metrics.get("volume_ratio"),
        "matched_rules": list(row["matched_rules"]),
        "why_selected": row["why_selected"],
        "data_quality": row["data_quality"],
        "official_industry_name": industry.get("official_industry_name") if industry else None,
        "normalized_sector": industry.get("normalized_sector") if industry else None,
        "industry_mapping_status": industry.get("mapping_status") if industry else "UNKNOWN",
    }


def _signal_candidates(
    connection: sqlite3.Connection,
    replay: dict[str, Any],
    industries: dict[str, dict[str, Any]],
    as_of: datetime,
) -> list[dict[str, Any]]:
    output = []
    for row in replay["ranked"]:
        if not row["matched_rules"]:
            continue
        metrics = row["raw_metrics"]
        industry = industries.get(row["security_id"])
        detail = _stock_detail(row, industry)
        output.append({
            "candidate_id": f"signal:{replay['replay_date']}:{row['security_id']}",
            "candidate_type": "MARKET_SIGNAL",
            "title": f"{row['name']}收盘{metrics['change_pct']:+.2f}%，RVOL {metrics['volume_ratio']:.2f}倍",
            "market_session_date": replay["replay_date"],
            "data_as_of": as_of.isoformat(),
            "freshness_state": "CURRENT_SESSION_EOD",
            "security_ids": [row["security_id"]],
            "industry_keys": [industry["normalized_sector"]] if industry and industry["mapping_status"] == "MAPPED_COMMON_STOCK" else [],
            "facts": [
                f"收盘价 {metrics['close']:.2f}",
                f"涨跌幅 {metrics['change_pct']:+.2f}%",
                f"成交量 {int(metrics['current_volume']):,} 股，20日中位数 {int(metrics['median_volume_20d']):,} 股",
                f"RVOL {metrics['volume_ratio']:.2f}倍",
            ],
            "evidence": _market_evidence(connection, row["security_id"], replay["replay_date"]),
            "opinion_evidence": [],
            "unknowns": ["价格与成交异常的具体催化剂尚未确认"],
            "risk_flags": ["NOT_FUND_FLOW", "NOT_INVESTMENT_ADVICE"],
            "stock_details": [detail],
            "editorial_status": "READY_TO_PITCH" if len(row["matched_rules"]) >= 2 else "WATCH_ONLY",
            "catalyst_status": "UNCONFIRMED",
            "why_now": [row["why_selected"]],
            "sort_metrics": {
                "rule_count": len(row["matched_rules"]),
                "price_volume": int("PRICE_VOLUME_BREAKOUT" in row["matched_rules"]),
                "volume_ratio": metrics.get("volume_ratio") or 0,
                "abs_price_zscore": metrics.get("abs_price_zscore") or 0,
                "abs_change_pct": abs(metrics.get("change_pct") or 0),
                "base_rank": row["rank"],
            },
        })
    return output


def _event_rows(
    connection: sqlite3.Connection, *, as_of: datetime, lookback_hours: int,
    include_x: bool = True,
) -> list[dict[str, Any]]:
    lower = as_of - timedelta(hours=lookback_hours)

    def in_window(value: Any) -> bool:
        parsed = _parse_datetime(value)
        return parsed is not None and lower <= parsed.astimezone(TAIPEI) <= as_of

    # Timestamp offsets do not have chronological ordering as SQLite TEXT. Filter
    # parsed instants in Python so Replay cannot admit future evidence.
    news = [
        dict(row) for row in connection.execute(
            "SELECT * FROM ben_news_items ORDER BY published_at"
        ) if in_window(row["published_at"])
    ]
    x_rows = []
    if include_x:
        x_rows = [
            dict(row) for row in connection.execute(
                """SELECT posts.*, accounts.market_scope, accounts.impact_path
                   FROM ben_x_posts posts JOIN ben_x_accounts accounts ON accounts.id=posts.account_id
                   ORDER BY posts.created_at"""
            ) if in_window(row["created_at"])
        ]
    return build_unified_events(news, x_rows, now=as_of.astimezone(timezone.utc))


def _disclosure_candidates(
    connection: sqlite3.Connection,
    *,
    replay_date: str,
    as_of: datetime,
    lookback_hours: int,
    replay_rows: dict[str, dict[str, Any]],
    industries: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    lower = as_of - timedelta(hours=lookback_hours)
    output = []
    for disclosure in connection.execute(
        "SELECT * FROM official_disclosures ORDER BY announced_at DESC"
    ):
        row = dict(disclosure)
        announced = _parse_datetime(row.get("announced_at"))
        if announced is None or not (lower <= announced.astimezone(TAIPEI) <= as_of):
            continue
        security_id = row.get("security_id")
        replay_row = replay_rows.get(security_id) if security_id else None
        detail = _stock_detail(replay_row, industries.get(security_id)) if replay_row else None
        output.append({
            "candidate_id": f"disclosure:{row['id']}:{replay_date}",
            "candidate_type": "DISCLOSURE",
            "title": f"{row['company_name']}公告：{row['subject']}",
            "market_session_date": replay_date,
            "data_as_of": as_of.isoformat(),
            "freshness_state": "WITHIN_LOOKBACK_WINDOW",
            "security_ids": [security_id] if security_id else [],
            "industry_keys": [industries[security_id]["normalized_sector"]] if security_id in industries and industries[security_id]["mapping_status"] == "MAPPED_COMMON_STOCK" else [],
            "facts": [value for value in (
                f"公告时间 {row['announced_at']}",
                f"事实发生日 {row['event_date']}" if row.get("event_date") else None,
                row["subject"],
            ) if value],
            "evidence": [{
                "evidence_id": row["raw_item_id"],
                "evidence_class": "OFFICIAL_DISCLOSURE",
                "source_id": "TW-A03",
                "url": row["official_url"],
                "announced_at": row["announced_at"],
                "collected_at": row["collected_at"],
                "observed_at": row["collected_at"],
                "epistemic_status": "FACT",
            }],
            "opinion_evidence": [],
            "unknowns": [] if replay_row and replay_row["matched_rules"] else ["公告与当日股价变化之间的关系尚未确认"],
            "risk_flags": ["NO_CAUSAL_INFERENCE", "NOT_INVESTMENT_ADVICE"],
            "stock_details": [detail] if detail else [],
            "editorial_status": "READY_TO_PITCH",
            "catalyst_status": "MOPS_CONFIRMED",
            "why_now": [f"官方重大讯息在收盘简报截止前发布：{row['announced_at']}"],
            "sort_metrics": {
                "official_evidence": 1,
                "independent_sources": 1,
                "rule_count": len(replay_row["matched_rules"]) if replay_row else 0,
                "volume_ratio": replay_row["raw_metrics"].get("volume_ratio", 0) if replay_row else 0,
            },
        })
    return output


def _media_event_candidates(
    connection: sqlite3.Connection,
    *,
    replay_date: str,
    as_of: datetime,
    lookback_hours: int,
    replay_rows: dict[str, dict[str, Any]],
    industries: dict[str, dict[str, Any]],
    include_x: bool = True,
) -> list[dict[str, Any]]:
    output = []
    for event in _event_rows(
        connection, as_of=as_of, lookback_hours=lookback_hours, include_x=include_x
    ):
        security_ids = []
        for ticker in event["entities"]:
            for exchange in ("TWSE", "TPEX"):
                security_id = f"{exchange}:{ticker}"
                if security_id in replay_rows:
                    security_ids.append(security_id)
                    break
        if not security_ids:
            continue
        details = [
            _stock_detail(replay_rows[security_id], industries.get(security_id))
            for security_id in security_ids
        ]
        evidence = []
        opinions = []
        for item in event["items"]:
            target = opinions if item["kind"] == "X" else evidence
            target.append({
                "evidence_id": item["id"],
                "evidence_class": "OPINION" if item["kind"] == "X" else "MEDIA_REPORT",
                "source_id": item["publisher_group"],
                "url": item["url"],
                "published_at": item["published_at"],
                "observed_at": item["published_at"],
                "epistemic_status": "OPINION" if item["kind"] == "X" else "REPORTED",
            })
        candidate_type = "NEWS_EVENT" if event["news_items"] else "X_EVENT"
        output.append({
            "candidate_id": f"event:{event['event_id']}:{replay_date}",
            "candidate_type": candidate_type,
            "title": event["display_title_zh"],
            "market_session_date": replay_date,
            "data_as_of": as_of.isoformat(),
            "freshness_state": "WITHIN_LOOKBACK_WINDOW",
            "security_ids": security_ids,
            "industry_keys": sorted({
                industries[sid]["normalized_sector"] for sid in security_ids
                if sid in industries and industries[sid]["mapping_status"] == "MAPPED_COMMON_STOCK"
            }),
            "facts": [event["summary_zh"]],
            "evidence": evidence,
            "opinion_evidence": opinions,
            "unknowns": ["媒体或X讨论与公司财务影响尚未由官方资料确认"],
            "risk_flags": ["MEDIA_OR_OPINION_LEAD", "NO_CAUSAL_INFERENCE"],
            "stock_details": details,
            "editorial_status": "NEEDS_RESEARCH",
            "catalyst_status": "REPORTED_NOT_OFFICIAL",
            "why_now": [event["why_watch"]],
            "sort_metrics": {
                "official_evidence": 0,
                "independent_sources": event["independent_count"],
                "rule_count": sum(len(replay_rows[sid]["matched_rules"]) for sid in security_ids),
                "volume_ratio": max((replay_rows[sid]["raw_metrics"].get("volume_ratio") or 0 for sid in security_ids), default=0),
            },
        })
    return output


def _industry_candidates(
    signal_candidates: list[dict[str, Any]], industries: dict[str, dict[str, Any]], replay_date: str
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for candidate in signal_candidates:
        security_id = candidate["security_ids"][0]
        industry = industries.get(security_id)
        if not industry or industry["mapping_status"] != "MAPPED_COMMON_STOCK":
            continue
        grouped.setdefault(industry["normalized_sector"], []).append(candidate)
    output = []
    for sector, rows in grouped.items():
        if len(rows) < 2:
            continue
        rows.sort(key=lambda row: row["sort_metrics"]["base_rank"])
        industry = industries[rows[0]["security_ids"][0]]
        details = [row["stock_details"][0] for row in rows[:6]]
        evidence = [item for row in rows[:6] for item in row["evidence"]]
        security_ids = [row["security_ids"][0] for row in rows[:6]]
        average_rvol = sum(float(row["sort_metrics"]["volume_ratio"]) for row in rows) / len(rows)
        total_rules = sum(int(row["sort_metrics"]["rule_count"]) for row in rows)
        names = "、".join(detail["name"] for detail in details[:3])
        output.append({
            "candidate_id": f"industry:{replay_date}:{sector}",
            "candidate_type": "CROSS_ENTITY",
            "title": f"{industry['official_industry_name']}出现{len(rows)}家公司收盘异常：{names}",
            "market_session_date": replay_date,
            "data_as_of": rows[0]["data_as_of"],
            "freshness_state": "CURRENT_SESSION_EOD",
            "security_ids": security_ids,
            "industry_keys": [sector],
            "facts": [
                f"官方产业分类：{industry['official_industry_name']}",
                f"同产业共有{len(rows)}家公司命中异常规则",
                f"组内平均RVOL {average_rvol:.2f}倍",
            ],
            "evidence": evidence,
            "opinion_evidence": [],
            "unknowns": ["共同催化剂、订单关系与供应链传导均未确认"],
            "risk_flags": ["CO_OCCURRENCE_NOT_CAUSATION", "OFFICIAL_INDUSTRY_RECALL_ONLY"],
            "stock_details": details,
            "editorial_status": "NEEDS_RESEARCH",
            "catalyst_status": "UNCONFIRMED",
            "why_now": [f"{len(rows)}家同产业公司在同一完整交易日出现可解释价量异常"],
            "sort_metrics": {
                "security_count": len(rows),
                "total_rule_count": total_rules,
                "average_volume_ratio": average_rvol,
            },
        })
    return output


def _channel_reason(profile: ChannelProfile, candidate: dict[str, Any]) -> list[str]:
    if profile.channel_type == "SIGNAL_HEAVY":
        return ["候选来自完整收盘后的价量异常", profile.fixed_boundary]
    if profile.channel_type == "EVENT_HEAVY":
        if candidate["candidate_type"] == "DISCLOSURE":
            return ["官方公司事件与个股收盘表现可在同一张卡核验", profile.fixed_boundary]
        if candidate["candidate_type"] in {"NEWS_EVENT", "X_EVENT"}:
            return ["事件明确提及台股公司，可作为后续核验线索", profile.fixed_boundary]
        return ["个股收盘异常值得寻找公司层催化剂", profile.fixed_boundary]
    return ["同一官方产业内出现多个异常证券，适合跨公司比较", profile.fixed_boundary]


def _candidate_future_reason(candidate: dict[str, Any], as_of: datetime) -> str | None:
    candidate_as_of = _parse_datetime(candidate.get("data_as_of"))
    if candidate_as_of is None or candidate_as_of.astimezone(TAIPEI) != as_of:
        return "INVALID_DATA_AS_OF"
    for item in candidate.get("evidence", []) + candidate.get("opinion_evidence", []):
        trade_date = item.get("trade_date")
        if trade_date:
            try:
                if date.fromisoformat(str(trade_date)) > as_of.date():
                    return "FUTURE_TRADE_DATE"
            except ValueError:
                return "INVALID_EVIDENCE_TIME"
        for key in ("published_at", "announced_at"):
            if not item.get(key):
                continue
            parsed = _parse_datetime(item[key])
            if parsed is None:
                return "INVALID_EVIDENCE_TIME"
            if parsed.astimezone(TAIPEI) > as_of:
                return "FUTURE_EVIDENCE"
    return None


def _eligible_candidates(
    profile: ChannelProfile,
    candidates: list[dict[str, Any]],
    *,
    replay_date: str,
    as_of: datetime,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    eligible: list[dict[str, Any]] = []
    drops: dict[str, int] = {}
    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    allowed_types = set(profile.preferred_candidate_types)
    market_id = re.compile(r"^(TWSE|TPEX):[A-Z0-9]+$")

    def drop(reason: str) -> None:
        drops[reason] = drops.get(reason, 0) + 1

    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id") or "")
        if not candidate_id or candidate_id in seen_ids:
            drop("DUPLICATE_OR_MISSING_CANDIDATE_ID")
            continue
        if candidate.get("candidate_type") not in allowed_types:
            drop("CHANNEL_PROFILE_MISMATCH")
            continue
        if candidate.get("market_session_date") != replay_date:
            drop("SESSION_DATE_MISMATCH")
            continue
        future_reason = _candidate_future_reason(candidate, as_of)
        if future_reason:
            drop(future_reason)
            continue
        if not candidate.get("evidence") and not candidate.get("opinion_evidence"):
            drop("NO_TRACEABLE_EVIDENCE")
            continue
        security_ids = candidate.get("security_ids") or []
        if not security_ids or any(not market_id.fullmatch(str(value)) for value in security_ids):
            drop("INVALID_MARKET_SECURITY_ID")
            continue
        normalized_title = "".join(str(candidate.get("title") or "").casefold().split())
        if not normalized_title or normalized_title in seen_titles:
            drop("DUPLICATE_OR_MISSING_TITLE")
            continue
        seen_ids.add(candidate_id)
        seen_titles.add(normalized_title)
        eligible.append(candidate)
    return eligible, drops


def _rank_channel(
    profile: ChannelProfile,
    candidates: list[dict[str, Any]],
    ranker: ChannelRanker | None,
) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    fallback = RuleBasedChannelRanker()
    selected_ranker = ranker or fallback
    try:
        ranked_ids = selected_ranker.rank(profile, candidates)
        ids = [candidate_id for candidate_id, _ in ranked_ids]
        expected = {row["candidate_id"] for row in candidates}
        if len(ids) != len(set(ids)) or set(ids) != expected:
            raise ValueError("ranker must return every existing candidate ID exactly once")
        method = selected_ranker.method
        if method not in {"AI_RANKED", "RULE_BASED_FALLBACK"}:
            raise ValueError(f"unsupported ranking method: {method}")
        detail = dict(selected_ranker.detail)
    except Exception as error:
        ranked_ids = fallback.rank(profile, candidates)
        method = fallback.method
        detail = {**fallback.detail, "fallback_error": f"{type(error).__name__}: {error}"}
    by_id = {row["candidate_id"]: row for row in candidates}
    output = []
    for rank, (candidate_id, ranking_reasons) in enumerate(ranked_ids, start=1):
        row = dict(by_id[candidate_id])
        if profile.channel_type == "EVENT_HEAVY" and row["candidate_type"] == "MARKET_SIGNAL":
            row["editorial_status"] = "NEEDS_RESEARCH"
        row["candidate_rank"] = rank
        row["candidate_tier"] = "PRIMARY" if rank <= profile.daily_target else "BACKUP"
        row["why_channel"] = _channel_reason(profile, row)
        row["ranking_reasons"] = ranking_reasons
        output.append(row)
    return output, method, detail


def _shortage_reasons(
    profile: ChannelProfile,
    assignments: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
) -> list[str]:
    if len(assignments) >= profile.daily_target:
        return []
    reasons = ["QUALIFIED_CANDIDATES_BELOW_TARGET"]
    if profile.channel_type == "EVENT_HEAVY":
        reasons.append("MISSING_CORPORATE_DATA")
    if profile.channel_type == "CROSS_ENTITY":
        mapping = next(row for row in source_rows if row["source"] == "INDUSTRY_MAPPING")
        reasons.append("MISSING_INDUSTRY_MAPPING" if mapping["status"] != "AVAILABLE" else "INSUFFICIENT_CROSS_ENTITY_SIGNALS")
    if not assignments:
        reasons.append("NO_ELIGIBLE_CANDIDATES")
    return reasons


def build_channel_briefs(
    connection: sqlite3.Connection,
    *,
    config_path: str | Path,
    anomaly_config_path: str | Path,
    replay_date: str | None = None,
    generated_at: datetime | None = None,
    ranker: ChannelRanker | None = None,
) -> dict[str, Any]:
    config, profiles = load_channel_pilot_config(config_path)
    replay_date = replay_date or complete_replay_dates(
        connection, limit=1, minimum_market_coverage=float(config["minimum_market_coverage"])
    )[0]
    generated_at = generated_at or datetime.now(TAIPEI)
    if generated_at.tzinfo is None:
        generated_at = generated_at.replace(tzinfo=TAIPEI)
    generated_at = generated_at.astimezone(TAIPEI)
    scheduled_for = _as_of_for_session(replay_date, config["primary_build_time"])
    is_live_session = replay_date == generated_at.date().isoformat()
    as_of = generated_at if is_live_session else scheduled_for
    session_state, coverage_status, source_rows = _source_readiness(
        connection,
        replay_date=replay_date,
        as_of=as_of,
        minimum_coverage=float(config["minimum_market_coverage"]),
        lookback_hours=int(config.get("event_lookback_hours", 72)),
        include_x=bool(config.get("include_x", True)),
    )
    engine = AnomalyEngine(connection, AnomalyRuleConfig.load(anomaly_config_path))
    replay = engine.replay(replay_date)
    replay_rows = {row["security_id"]: row for row in replay["ranked"]}
    industries = _industry_map(connection)
    signals = _signal_candidates(connection, replay, industries, as_of)
    disclosures = _disclosure_candidates(
        connection, replay_date=replay_date, as_of=as_of,
        lookback_hours=int(config.get("event_lookback_hours", 72)),
        replay_rows=replay_rows, industries=industries,
    )
    media_events = _media_event_candidates(
        connection, replay_date=replay_date, as_of=as_of,
        lookback_hours=int(config.get("event_lookback_hours", 72)),
        replay_rows=replay_rows, industries=industries,
        include_x=bool(config.get("include_x", True)),
    )
    industry = _industry_candidates(signals, industries, replay_date)

    briefs = []
    ranking_details: dict[str, Any] = {}
    for profile in profiles:
        if profile.channel_type == "SIGNAL_HEAVY":
            pool = signals
        elif profile.channel_type == "EVENT_HEAVY":
            event_pool = disclosures + media_events
            covered = {sid for row in event_pool for sid in row["security_ids"]}
            pool = event_pool + [row for row in signals if row["security_ids"][0] not in covered]
        else:
            pool = industry
        eligible, qualification_drops = _eligible_candidates(
            profile, pool, replay_date=replay_date, as_of=as_of
        )
        ranked, method, detail = _rank_channel(profile, eligible, ranker)
        limit = profile.daily_target + int(config.get("backup_target", 3))
        assignments = ranked[:limit]
        shortage = _shortage_reasons(profile, assignments, source_rows)
        briefs.append({
            "channel_id": profile.channel_id,
            "channel_name": profile.channel_name,
            "channel_type": profile.channel_type,
            "profile_version": profile.profile_version,
            "profile_status": profile.profile_status,
            "summary": profile.summary,
            "fixed_boundary": profile.fixed_boundary,
            "target_count": profile.daily_target,
            "qualified_count": len(eligible),
            "qualification_drops": qualification_drops,
            "displayed_count": len(assignments),
            "status": "READY" if len(assignments) >= profile.daily_target else "HONEST_SHORTAGE",
            "shortage_reasons": shortage,
            "ranking_method": method,
            "assignments": assignments,
        })
        ranking_details[profile.channel_id] = detail

    ranking_methods = {row["ranking_method"] for row in briefs}
    run_method = "AI_RANKED" if ranking_methods == {"AI_RANKED"} else "RULE_BASED_FALLBACK"
    payload = {
        "artifact": "BEN_CHANNEL_DAILY_BRIEF",
        "artifact_version": "p06b-v0.1",
        "config_version": config["config_version"],
        "market": config["market"],
        "timezone": config["timezone"],
        "market_session_date": replay_date,
        "session_state": session_state,
        "scheduled_for": scheduled_for.isoformat(),
        "generated_at": generated_at.isoformat(),
        "data_as_of": as_of.isoformat(),
        "replay_mode": not is_live_session,
        "source_readiness": source_rows,
        "coverage_status": coverage_status,
        "ranking_method": run_method,
        "ranking_detail": ranking_details,
        "rule_version": replay["rule_version"],
        "candidate_pool_counts": {
            "market_signals": len(signals),
            "disclosures": len(disclosures),
            "media_events": len(media_events),
            "cross_entity": len(industry),
        },
        "briefs": briefs,
    }
    fingerprint_input = {
        key: payload[key]
        for key in (
            "artifact_version", "config_version", "market_session_date", "data_as_of",
            "source_readiness", "ranking_method", "rule_version", "candidate_pool_counts", "briefs",
        )
    }
    payload["input_fingerprint"] = hashlib.sha256(
        json.dumps(fingerprint_input, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return payload


def persist_channel_briefs(
    connection: sqlite3.Connection,
    payload: dict[str, Any],
    *,
    config_path: str | Path,
) -> tuple[dict[str, Any], bool]:
    existing = connection.execute(
        "SELECT payload_json FROM ben_channel_brief_runs WHERE input_fingerprint=?",
        (payload["input_fingerprint"],),
    ).fetchone()
    if existing:
        return json.loads(existing["payload_json"]), False
    _, profiles = load_channel_pilot_config(config_path)
    profiles_by_id = {row.channel_id: row for row in profiles}
    stored = json.loads(json.dumps(payload, ensure_ascii=False))
    run_id = "channel-run:" + payload["input_fingerprint"][:24]
    stored["run_id"] = run_id
    with connection:
        for profile in profiles:
            profile_id = f"{profile.channel_id}:{profile.profile_version}"
            connection.execute(
                """
                INSERT INTO ben_channel_profiles (
                    id, channel_id, channel_name, channel_type, profile_version,
                    profile_status, market, timezone, primary_build_time,
                    daily_target, profile_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(channel_id, profile_version) DO UPDATE SET
                    channel_name=excluded.channel_name,
                    channel_type=excluded.channel_type,
                    profile_status=excluded.profile_status,
                    profile_json=excluded.profile_json
                """,
                (
                    profile_id, profile.channel_id, profile.channel_name,
                    profile.channel_type, profile.profile_version, profile.profile_status,
                    profile.market, profile.timezone, profile.primary_build_time,
                    profile.daily_target,
                    json.dumps(asdict(profile), ensure_ascii=False, sort_keys=True),
                ),
            )
        for brief in stored["briefs"]:
            next_version = connection.execute(
                """SELECT COALESCE(MAX(brief_version), 0) + 1
                   FROM ben_channel_daily_briefs
                   WHERE channel_id=? AND market_session_date=?""",
                (brief["channel_id"], stored["market_session_date"]),
            ).fetchone()[0]
            brief["brief_version"] = int(next_version)
            brief["brief_id"] = f"brief:{brief['channel_id']}:{stored['market_session_date']}:v{next_version}"
        connection.execute(
            """
            INSERT INTO ben_channel_brief_runs (
                id, market, market_session_date, session_state, scheduled_for,
                generated_at, data_as_of, replay_mode, source_readiness_json,
                coverage_status, ranking_method, ranking_detail_json,
                config_version, input_fingerprint, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id, stored["market"], stored["market_session_date"],
                stored["session_state"], stored["scheduled_for"], stored["generated_at"],
                stored["data_as_of"], int(bool(stored["replay_mode"])),
                json.dumps(stored["source_readiness"], ensure_ascii=False, sort_keys=True),
                stored["coverage_status"], stored["ranking_method"],
                json.dumps(stored["ranking_detail"], ensure_ascii=False, sort_keys=True),
                stored["config_version"], stored["input_fingerprint"],
                json.dumps(stored, ensure_ascii=False, sort_keys=True),
            ),
        )
        for brief in stored["briefs"]:
            profile = profiles_by_id[brief["channel_id"]]
            connection.execute(
                """
                INSERT INTO ben_channel_daily_briefs (
                    id, run_id, profile_id, channel_id, market_session_date,
                    brief_version, status, target_count, qualified_count,
                    ranking_method, shortage_reasons_json, generated_at, data_as_of
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brief["brief_id"], run_id,
                    f"{profile.channel_id}:{profile.profile_version}",
                    brief["channel_id"], stored["market_session_date"],
                    brief["brief_version"], brief["status"], brief["target_count"],
                    brief["qualified_count"], brief["ranking_method"],
                    json.dumps(brief["shortage_reasons"], ensure_ascii=False),
                    stored["generated_at"], stored["data_as_of"],
                ),
            )
            for assignment in brief["assignments"]:
                connection.execute(
                    """
                    INSERT INTO ben_channel_topic_assignments (
                        id, brief_id, candidate_id, candidate_type, candidate_rank,
                        candidate_tier, editorial_status, title, why_now_json,
                        why_channel_json, facts_json, evidence_json,
                        opinion_evidence_json, security_ids_json, stock_details_json,
                        industry_keys_json, unknowns_json, risk_flags_json,
                        ranking_reasons_json, candidate_payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(uuid.uuid4()), brief["brief_id"], assignment["candidate_id"],
                        assignment["candidate_type"], assignment["candidate_rank"],
                        assignment["candidate_tier"], assignment["editorial_status"],
                        assignment["title"],
                        json.dumps(assignment["why_now"], ensure_ascii=False),
                        json.dumps(assignment["why_channel"], ensure_ascii=False),
                        json.dumps(assignment["facts"], ensure_ascii=False),
                        json.dumps(assignment["evidence"], ensure_ascii=False),
                        json.dumps(assignment["opinion_evidence"], ensure_ascii=False),
                        json.dumps(assignment["security_ids"], ensure_ascii=False),
                        json.dumps(assignment["stock_details"], ensure_ascii=False),
                        json.dumps(assignment["industry_keys"], ensure_ascii=False),
                        json.dumps(assignment["unknowns"], ensure_ascii=False),
                        json.dumps(assignment["risk_flags"], ensure_ascii=False),
                        json.dumps(assignment["ranking_reasons"], ensure_ascii=False),
                        json.dumps(assignment, ensure_ascii=False, sort_keys=True),
                    ),
                )
    return stored, True


def latest_channel_brief_payload(connection: sqlite3.Connection) -> dict[str, Any] | None:
    if not _table_exists(connection, "ben_channel_brief_runs"):
        return None
    row = connection.execute(
        """SELECT payload_json FROM ben_channel_brief_runs
           WHERE session_state IN ('READY','DEGRADED')
           ORDER BY market_session_date DESC, created_at DESC, rowid DESC LIMIT 1"""
    ).fetchone()
    return json.loads(row["payload_json"]) if row else None


def channel_brief_payload_for_date(
    connection: sqlite3.Connection, market_session_date: str
) -> dict[str, Any] | None:
    if not _table_exists(connection, "ben_channel_brief_runs"):
        return None
    row = connection.execute(
        """SELECT payload_json FROM ben_channel_brief_runs
           WHERE market_session_date=? AND session_state IN ('READY','DEGRADED')
           ORDER BY created_at DESC, rowid DESC LIMIT 1""",
        (market_session_date,),
    ).fetchone()
    return json.loads(row["payload_json"]) if row else None


def channel_brief_markdown(payload: dict[str, Any]) -> str:
    lines = [
        f"# BEN Radar 三频道收盘 Top 5｜{payload['market_session_date']}",
        "",
        f"- 状态：`{payload['session_state']}` / `{payload['coverage_status']}`",
        f"- 数据截至：`{payload['data_as_of']}`",
        f"- 排序：`{payload['ranking_method']}`",
        "",
    ]
    for brief in payload["briefs"]:
        lines.extend((
            f"## {brief['channel_name']}｜{brief['status']}｜{min(brief['displayed_count'], brief['target_count'])}/{brief['target_count']}",
            "",
            f"> {brief['fixed_boundary']}",
            "",
        ))
        for item in brief["assignments"][:brief["target_count"]]:
            lines.extend((
                f"### {item['candidate_rank']}. {item['title']}",
                "",
                f"- 类型：`{item['candidate_type']}` / `{item['editorial_status']}`",
                f"- Why Now：{'；'.join(item['why_now'])}",
                f"- Why Channel：{'；'.join(item['why_channel'])}",
                f"- 排名理由：{'；'.join(item['ranking_reasons'])}",
                f"- 股票：{', '.join(item['security_ids']) or '无'}",
                f"- Evidence：{len(item['evidence'])}；Opinion：{len(item['opinion_evidence'])}",
                f"- 未知：{'；'.join(item['unknowns']) or '无'}",
                "",
            ))
        if brief["shortage_reasons"]:
            lines.append(f"短缺原因：`{' / '.join(brief['shortage_reasons'])}`")
            lines.append("")
    return "\n".join(lines)
