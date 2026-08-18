from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from .anomaly_engine import AnomalyEngine, AnomalyRuleConfig, complete_replay_dates
from .official_data import recent_disclosures


RULE_LABELS = {
    "VOLUME_SPIKE": "異常放量",
    "RANGE_BREAKOUT_20D": "突破20日區間",
    "RANGE_BREAKOUT_40D": "突破40日區間",
    "PRICE_VOLUME_BREAKOUT": "量價共振",
    "QUIET_TO_VOLUME_SPIKE": "縮量後突然放量",
    "PRICE_ANOMALY": "價格異常",
    "MULTI_SIGNAL": "多重異動",
}


def _top20(replay: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in replay["ranked"] if row["matched_rules"]][:20]


def _streaks(tops: dict[str, list[dict[str, Any]]], dates: list[str]) -> tuple[dict[str, int], list[dict[str, Any]]]:
    chronological = list(reversed(dates))
    appearances: dict[str, list[str]] = defaultdict(list)
    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for date in chronological:
        for row in tops[date]:
            appearances[row["security_id"]].append(date)
            rows_by_key[(date, row["security_id"])] = row

    current: dict[str, int] = {}
    persistent: list[dict[str, Any]] = []
    for security_id, seen_dates in appearances.items():
        positions = sorted(chronological.index(date) for date in seen_dates)
        longest = run = 1
        for index in range(1, len(positions)):
            run = run + 1 if positions[index] == positions[index - 1] + 1 else 1
            longest = max(longest, run)
        ending = 0
        for date in dates:
            if security_id in {row["security_id"] for row in tops[date]}:
                ending += 1
            else:
                break
        current[security_id] = ending
        if longest >= 2:
            latest_seen = seen_dates[-1]
            row = rows_by_key[(latest_seen, security_id)]
            persistent.append({
                "security_id": security_id,
                "name": row["name"],
                "ticker": row["ticker"],
                "market": row["market"],
                "latest_seen": latest_seen,
                "appearance_count": len(seen_dates),
                "longest_consecutive": longest,
                "current_consecutive": ending,
                "dates": seen_dates,
            })
    persistent.sort(
        key=lambda row: (row["current_consecutive"], row["longest_consecutive"], row["appearance_count"]),
        reverse=True,
    )
    return current, persistent


def _card(row: dict[str, Any], *, consecutive_days: int = 0) -> dict[str, Any]:
    metrics = dict(row["raw_metrics"])
    rules = list(row["matched_rules"])
    display_rules = [RULE_LABELS.get(rule, rule) for rule in rules]
    if len(rules) >= 2:
        display_rules.append(RULE_LABELS["MULTI_SIGNAL"])
    return {
        "rank": row["rank"],
        "security_id": row["security_id"],
        "name": row["name"],
        "ticker": row["ticker"],
        "market": row["market"],
        "replay_date": row["replay_date"],
        "close": metrics.get("close"),
        "change_pct": metrics.get("change_pct"),
        "current_volume": metrics.get("current_volume"),
        "median_volume_20d": metrics.get("median_volume_20d"),
        "volume_ratio": metrics.get("volume_ratio"),
        "market_volume_percentile": row.get("market_volume_percentile"),
        "liquidity_level": row.get("liquidity_level", "UNKNOWN"),
        "matched_rules": rules,
        "display_rules": display_rules,
        "rule_severity": row["rule_severity"],
        "raw_metrics": metrics,
        "why_selected": row["why_selected"],
        "data_quality": row["data_quality"],
        "consecutive_days": consecutive_days,
        "data_status": "EOD",
    }


def _history(connection, security_id: str, *, limit: int = 66) -> list[dict[str, Any]]:
    rows = connection.execute(
        """SELECT trade_date, opening_price, highest_price, lowest_price,
                  closing_price, trade_volume, trade_value, data_status
           FROM official_market_data_daily
           WHERE security_id=? AND data_status='EOD'
           ORDER BY trade_date DESC LIMIT ?""",
        (security_id, limit),
    ).fetchall()
    return [
        {
            "date": row["trade_date"],
            "open": float(row["opening_price"]),
            "high": float(row["highest_price"]),
            "low": float(row["lowest_price"]),
            "close": float(row["closing_price"]),
            "volume": int(row["trade_volume"]),
            "turnover": int(row["trade_value"]) if row["trade_value"] is not None else None,
            "status": row["data_status"],
        }
        for row in reversed(rows)
        if all(row[key] is not None for key in ("opening_price", "highest_price", "lowest_price", "closing_price", "trade_volume"))
    ]


def build_stock_workbench(
    connection,
    *,
    config_path: str | Path,
    replay_limit: int = 6,
) -> dict[str, Any]:
    """Build a read-only presentation payload directly from Anomaly Engine output."""
    engine = AnomalyEngine(connection, AnomalyRuleConfig.load(config_path))
    dates = complete_replay_dates(connection, limit=replay_limit)
    replays = {date: engine.replay(date) for date in dates}
    tops = {date: _top20(replays[date]) for date in dates}
    streaks, persistent = _streaks(tops, dates)
    latest = replays[dates[0]]
    cards = [_card(row, consecutive_days=streaks.get(row["security_id"], 0)) for row in tops[dates[0]]]

    details: dict[str, Any] = {}
    for card in cards:
        disclosures = recent_disclosures(connection, card["security_id"], limit=5)
        details[card["security_id"]] = {
            **card,
            "history": _history(connection, card["security_id"]),
            "disclosures": disclosures,
            "catalyst_status": "MOPS_CONFIRMED" if disclosures else "UNCONFIRMED",
        }

    early_momentum = [
        card for card in cards
        if 0 < float(card["change_pct"] or 0) <= 3
        and "VOLUME_SPIKE" in card["matched_rules"]
        and (
            "RANGE_BREAKOUT_20D" in card["matched_rules"]
            or "RANGE_BREAKOUT_40D" in card["matched_rules"]
            or len(card["matched_rules"]) >= 3
        )
    ]

    return {
        "status": "READY",
        "rule_version": latest["rule_version"],
        "replay_date": dates[0],
        "data_status": "EOD",
        "participating": latest["participating"],
        "participating_total": latest["participating_total"],
        "top20": cards,
        "early_momentum": early_momentum,
        "persistent": persistent,
        "details": details,
        "replay_dates": dates,
        "rule_labels": RULE_LABELS,
    }
