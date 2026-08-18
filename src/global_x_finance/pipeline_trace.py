from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlparse

from .ben_radar import detect_entities
from .realtime_radar import parse_datetime
from .x_intelligence import event_actions, event_topics


DROP_REASONS = {
    "NON_FINANCE",
    "DUPLICATE",
    "MISSING_TIMESTAMP",
    "INVALID_URL",
    "LOW_RELEVANCE",
    "ENTITY_EXTRACTION_FAILED",
    "NO_EVENT_ASSIGNMENT",
    "BELOW_RANKING_THRESHOLD",
    "OUTSIDE_TIME_WINDOW",
    "SOURCE_EXCLUDED",
    "SNAPSHOT_LIMIT",
    "PIPELINE_ERROR",
    "UNKNOWN",
}


def market_security_id(ticker: str) -> str:
    """Keep same-company listings distinct instead of collapsing TSM and 2330."""
    if ticker.isdigit():
        return f"TWSE:{ticker}"
    exchange = {
        "TSM": "NYSE",
        "ASML": "NASDAQ",
        "ARM": "NASDAQ",
        "COIN": "NASDAQ",
        "MSTR": "NASDAQ",
    }.get(ticker, "NASDAQ")
    return f"{exchange}:{ticker}"


def _valid_url(value: str | None) -> bool:
    parsed = urlparse(value or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_news_pipeline_trace(
    news_rows: list[dict[str, Any]],
    events: list[dict[str, Any]],
    *,
    now: datetime,
    snapshot_event_ids: set[str] | None = None,
    window_hours: int = 24,
) -> list[dict[str, Any]]:
    """Return one auditable terminal status for every persisted news item."""
    snapshot_event_ids = snapshot_event_ids or set()
    event_by_item: dict[str, dict[str, Any]] = {}
    for event in events:
        for item in event.get("news_items", []):
            event_by_item[str(item["id"])] = event

    traces: list[dict[str, Any]] = []
    for row in news_rows:
        content_id = str(row.get("id") or "UNKNOWN")
        timestamp = parse_datetime(row.get("published_at"))
        url = str(row.get("original_url") or "")
        title = str(row.get("original_title") or "")
        entities = detect_entities(title)
        actions = event_actions(title)
        topics = event_topics(title)
        finance_relevant = bool(entities or actions or topics)
        event = event_by_item.get(content_id)
        event_id = str(event["event_id"]) if event else ""
        in_snapshot = bool(event_id and event_id in snapshot_event_ids)

        drop_stage = ""
        drop_reason = ""
        if timestamp is None:
            drop_stage, drop_reason = "NORMALIZE", "MISSING_TIMESTAMP"
        elif not _valid_url(url):
            drop_stage, drop_reason = "NORMALIZE", "INVALID_URL"
        elif timestamp < now - timedelta(hours=window_hours) or timestamp > now:
            drop_stage, drop_reason = "TIME_WINDOW", "OUTSIDE_TIME_WINDOW"
        elif not finance_relevant:
            drop_stage, drop_reason = "FINANCE_GATE", "NON_FINANCE"
        elif event is None:
            drop_stage, drop_reason = "EVENT_ASSIGNMENT", "NO_EVENT_ASSIGNMENT"
        elif not in_snapshot:
            drop_stage, drop_reason = "SNAPSHOT", "SNAPSHOT_LIMIT"

        traces.append({
            "content_id": content_id,
            "source": str(row.get("source_name") or row.get("source_key") or "UNKNOWN"),
            "source_type": "NEWS",
            "source_item_id": content_id,
            "url": url,
            "published_at": str(row.get("published_at") or ""),
            "fetch_status": "PERSISTED",
            "normalize_status": "VALID" if timestamp is not None and _valid_url(url) and bool(title.strip()) else "FAILED",
            "finance_gate_status": "PASS" if finance_relevant else "REJECTED",
            "entity_status": "MATCHED" if entities else "NO_EXPLICIT_TICKER",
            "ticker_mapping_status": "MAPPED" if entities else "NOT_APPLICABLE",
            "event_assignment_status": "ASSIGNED" if event else "NOT_ASSIGNED",
            "ranking_status": "RANKED" if event else "NOT_RANKED",
            "snapshot_status": "INCLUDED" if in_snapshot else "EXCLUDED",
            "drop_stage": drop_stage,
            "drop_reason": drop_reason,
            "event_id": event_id,
            "related_tickers": "|".join(market_security_id(value) for value in entities),
        })
    return traces

