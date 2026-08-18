from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .pipeline_trace import market_security_id


HOT_SCORE_WEIGHTS = {
    "price": 25,
    "volume": 25,
    "catalyst": 30,
    "breadth": 20,
}


def _float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _ratio(value: int | float | None, baseline: int | float | None) -> float | None:
    if value is None or baseline in (None, 0):
        return None
    return float(value) / float(baseline)


def _event_links(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    linked: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        for ticker in event.get("entities", []):
            linked[str(ticker)].append(event)
    return linked


def build_stock_signals(connection, events: list[dict[str, Any]], *, limit: int = 30) -> list[dict[str, Any]]:
    """Build Taiwan daily signals using only the latest row and its prior 20 sessions."""
    event_links = _event_links(events)
    codes = [
        str(row["stock_code"])
        for row in connection.execute(
            """SELECT stock_code FROM ben_stock_history
               GROUP BY stock_code ORDER BY MAX(trade_date) DESC, MAX(trade_volume) DESC LIMIT ?""",
            (limit,),
        )
    ]
    output: list[dict[str, Any]] = []
    for code in codes:
        rows = [dict(row) for row in connection.execute(
            "SELECT * FROM ben_stock_history WHERE stock_code=? ORDER BY trade_date", (code,)
        )]
        current = rows[-1] if rows else None
        prior = rows[-21:-1] if len(rows) >= 21 else []
        related_events = event_links.get(code, [])
        if current is None:
            continue
        close = _float(current.get("closing_price"))
        prior_close = _float(prior[-1].get("closing_price")) if prior else None
        change_pct = ((close / prior_close - 1) * 100) if close is not None and prior_close not in (None, 0) else None
        baseline_volume = statistics.median(row["trade_volume"] for row in prior) if prior else None
        turnover_values = [row["trade_value"] for row in prior if row.get("trade_value") is not None]
        baseline_turnover = statistics.median(turnover_values) if len(turnover_values) == len(prior) and prior else None
        volume_ratio = _ratio(current.get("trade_volume"), baseline_volume)
        turnover_ratio = _ratio(current.get("trade_value"), baseline_turnover)
        news_publishers = {
            item["publisher_group"] for event in related_events for item in event.get("news_items", [])
        }
        x_publishers = {
            item["publisher_group"] for event in related_events for item in event.get("x_items", []) if not item.get("is_repost")
        }
        all_publishers = news_publishers | x_publishers
        news_count = sum(len(event.get("news_items", [])) for event in related_events)
        x_count = sum(len(event.get("x_items", [])) for event in related_events)
        price_score = 0 if change_pct is None else min(HOT_SCORE_WEIGHTS["price"], round(abs(change_pct) / 6 * HOT_SCORE_WEIGHTS["price"]))
        volume_score = 0 if volume_ratio is None else min(HOT_SCORE_WEIGHTS["volume"], round(max(0, volume_ratio - 1) / 3 * HOT_SCORE_WEIGHTS["volume"]))
        catalyst_score = min(HOT_SCORE_WEIGHTS["catalyst"], news_count * 5 + x_count * 2 + len(related_events) * 3)
        breadth_score = min(HOT_SCORE_WEIGHTS["breadth"], len(all_publishers) * 4)
        hot_score = min(100, price_score + volume_score + catalyst_score + breadth_score)
        flags: list[str] = []
        if change_pct is not None and change_pct >= 3:
            flags.append("PRICE_SPIKE")
        if change_pct is not None and change_pct <= -3:
            flags.append("PRICE_DROP")
        if volume_ratio is not None and volume_ratio >= 2:
            flags.append("VOLUME_SPIKE")
        if turnover_ratio is not None and turnover_ratio >= 2:
            flags.append("TURNOVER_SPIKE")
        if news_count >= 2:
            flags.append("NEWS_SPIKE")
        if len(x_publishers) >= 2:
            flags.append("X_DISCUSSION_SPIKE")
        if len(flags) >= 2:
            flags.append("MULTI_SIGNAL")
        reasons = []
        if change_pct is not None:
            reasons.append(f"收盤日變動 {change_pct:+.2f}%")
        if volume_ratio is not None:
            reasons.append(f"成交量為前20日中位數 {volume_ratio:.2f} 倍")
        if related_events:
            reasons.append(f"關聯 {len(related_events)} 個事件、{len(all_publishers)} 個獨立發布方")
        if len(prior) < 20:
            data_quality = "UNAVAILABLE"
        elif turnover_ratio is None:
            data_quality = "PARTIAL"
        else:
            data_quality = "COMPLETE"
        output.append({
            "security_id": market_security_id(code),
            "ticker": code,
            "market": "TW",
            "company_name": str(current.get("company_name") or code),
            "data_date": str(current.get("trade_date") or "UNKNOWN"),
            "price": close,
            "change_pct": round(change_pct, 4) if change_pct is not None else None,
            "volume": current.get("trade_volume"),
            "volume_baseline_20d_median": baseline_volume,
            "volume_ratio": round(volume_ratio, 4) if volume_ratio is not None else None,
            "turnover": current.get("trade_value"),
            "turnover_baseline_20d_median": baseline_turnover,
            "turnover_ratio": round(turnover_ratio, 4) if turnover_ratio is not None else None,
            "news_count": news_count,
            "x_count": x_count,
            "publisher_count": len(all_publishers),
            "event_count": len(related_events),
            "related_event_ids": [str(event["event_id"]) for event in related_events],
            "component_scores": {
                "price": price_score,
                "volume": volume_score,
                "catalyst": catalyst_score,
                "breadth": breadth_score,
            },
            "hot_score": hot_score,
            "abnormal_flags": flags,
            "reasons": reasons or ["目前沒有足夠資料形成可解釋原因"],
            "data_quality": data_quality,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "source_url": str(current.get("source_url") or ""),
        })
    output.sort(key=lambda row: (row["hot_score"], row["event_count"], row["volume_ratio"] or -1), reverse=True)
    return output


def build_stock_detail(signal: dict[str, Any], events_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    return {
        **signal,
        "linked_events": [
            {
                "event_id": event_id,
                "title": events_by_id[event_id].get("display_title_zh"),
                "relationship": next(
                    (
                        row.get("relationship")
                        for row in events_by_id[event_id].get("related_stocks", [])
                        if row.get("ticker") == signal["ticker"]
                    ),
                    "DIRECT",
                ),
                "evidence_count": len(events_by_id[event_id].get("items", [])),
            }
            for event_id in signal.get("related_event_ids", [])
            if event_id in events_by_id
        ],
        "method": {
            "baseline": "latest completed session versus prior 20 trading-session median",
            "weights": HOT_SCORE_WEIGHTS,
            "future_leakage": False,
        },
    }

