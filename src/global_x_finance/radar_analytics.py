from __future__ import annotations

from collections import Counter
from typing import Any


SOURCE_CONCENTRATION_TOP1_THRESHOLD = 0.50
SOURCE_CONCENTRATION_TOP3_THRESHOLD = 0.80
SOURCE_CONCENTRATION_MIN_PUBLISHERS = 5


def source_concentration(events: list[dict[str, Any]]) -> dict[str, Any]:
    groups: Counter[str] = Counter()
    news_groups: set[str] = set()
    x_groups: set[str] = set()
    for event in events:
        for item in event.get("items", []):
            if item.get("is_repost"):
                continue
            group = str(item.get("publisher_group") or item.get("publisher") or "UNKNOWN")
            groups[group] += 1
            (news_groups if item.get("kind") == "NEWS" else x_groups).add(group)
    total = sum(groups.values())
    ordered = groups.most_common()
    top1_share = ordered[0][1] / total if total else 0.0
    top3_share = sum(count for _, count in ordered[:3]) / total if total else 0.0
    warnings = []
    if total and top1_share > SOURCE_CONCENTRATION_TOP1_THRESHOLD:
        warnings.append("TOP1_OVER_50_PERCENT")
    if total and top3_share > SOURCE_CONCENTRATION_TOP3_THRESHOLD:
        warnings.append("TOP3_OVER_80_PERCENT")
    if total and len(groups) < SOURCE_CONCENTRATION_MIN_PUBLISHERS:
        warnings.append("FEWER_THAN_5_PUBLISHERS")
    return {
        "evidence_count": total,
        "unique_publishers": len(groups),
        "news_publishers": len(news_groups),
        "x_publishers": len(x_groups),
        "top1_share": round(top1_share, 4),
        "top3_share": round(top3_share, 4),
        "publisher_counts": dict(ordered),
        "status": "SOURCE_CONCENTRATION_WARNING" if warnings else "OK",
        "warnings": warnings,
        "thresholds": {
            "top1_share": SOURCE_CONCENTRATION_TOP1_THRESHOLD,
            "top3_share": SOURCE_CONCENTRATION_TOP3_THRESHOLD,
            "minimum_publishers": SOURCE_CONCENTRATION_MIN_PUBLISHERS,
        },
    }


def select_snapshot_events(events: list[dict[str, Any]], limit: int = 16) -> list[dict[str, Any]]:
    """Greedy relevance selection with a transparent marginal concentration penalty.

    It never removes a publisher mechanically. A repeated primary publisher loses four
    marginal points per prior selection (max 20), while news and multi-publisher events
    retain small evidence bonuses. The base opportunity score remains dominant.
    """
    remaining = list(events)
    selected: list[dict[str, Any]] = []
    primary_counts: Counter[str] = Counter()
    while remaining and len(selected) < limit:
        def marginal(event: dict[str, Any]) -> tuple[float, str]:
            primary = event.get("primary", {})
            group = str(primary.get("publisher_group") or primary.get("publisher") or "UNKNOWN")
            repetition_penalty = min(20, primary_counts[group] * 4)
            news_bonus = min(6, int(event.get("news_count") or 0) * 3)
            breadth_bonus = min(6, max(0, int(event.get("independent_count") or 0) - 1) * 2)
            linked_bonus = min(4, len(event.get("entities") or []))
            return float(event.get("score") or 0) + news_bonus + breadth_bonus + linked_bonus - repetition_penalty, str(event.get("latest_update_at") or "")

        chosen = max(remaining, key=marginal)
        selected.append(chosen)
        primary = chosen.get("primary", {})
        group = str(primary.get("publisher_group") or primary.get("publisher") or "UNKNOWN")
        primary_counts[group] += 1
        remaining.remove(chosen)
    return selected

