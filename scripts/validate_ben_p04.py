from __future__ import annotations

import argparse
import itertools
import json
import re
import sqlite3
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from global_x_finance.event_clustering import SAME_EVENT, decide_event_pair
from global_x_finance.translation_summary import TranslationSummaryAdapter
from global_x_finance.x_intelligence import (
    _news_rows,
    _x_rows,
    build_unified_events,
    cluster_quality_report,
)


def cjk_ready(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or "")) and "中文摘要生成中" not in (text or "")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=Path("data/taiwan-demo.db"))
    args = parser.parse_args()
    connection = sqlite3.connect(args.db)
    connection.row_factory = sqlite3.Row
    now = datetime.now(timezone.utc)
    cutoff_24 = (now - timedelta(hours=24)).isoformat()
    cutoff_72 = (now - timedelta(hours=72)).isoformat()
    try:
        news_24 = [dict(row) for row in connection.execute(
            "SELECT * FROM ben_news_items WHERE published_at >= ? ORDER BY published_at DESC", (cutoff_24,)
        )]
        x_24 = [dict(row) for row in connection.execute(
            """SELECT posts.*,accounts.market_scope,accounts.impact_path FROM ben_x_posts posts
               JOIN ben_x_accounts accounts ON accounts.id=posts.account_id
               WHERE posts.created_at >= ? ORDER BY posts.created_at DESC""", (cutoff_24,)
        )]
        news_72 = [dict(row) for row in connection.execute(
            "SELECT * FROM ben_news_items WHERE published_at >= ? ORDER BY published_at DESC", (cutoff_72,)
        )]
        x_72 = [dict(row) for row in connection.execute(
            """SELECT posts.*,accounts.market_scope,accounts.impact_path FROM ben_x_posts posts
               JOIN ben_x_accounts accounts ON accounts.id=posts.account_id
               WHERE posts.created_at >= ? ORDER BY posts.created_at DESC""", (cutoff_72,)
        )]
        adapter = TranslationSummaryAdapter(connection)
        events = build_unified_events(news_24, x_24, now=now, translation_adapter=adapter)
        quality = cluster_quality_report(events, raw_news_count=len(news_24), raw_x_count=len(x_24))
        top = events[:20]

        prepared_news = _news_rows(news_72, now)
        prepared_x = _x_rows(x_72, now)
        cross_decisions = []
        outside_window = []
        for left, right in itertools.product(prepared_news, prepared_x):
            decision = decide_event_pair(left, right)
            if decision.candidate:
                cross_decisions.append((left, right, decision))
            if decision.time_delta_hours and decision.time_delta_hours > 36 and (decision.common_entities or decision.common_actors):
                outside_window.append((left, right, decision))
        shared_url_pairs = sum(bool(set(left["external_urls"]) & set(right["external_urls"])) for left, right in itertools.product(prepared_news, prepared_x))
        cross_labels = Counter(decision.label for _, _, decision in cross_decisions)
        fingerprint_gaps = Counter()
        for _, _, decision in cross_decisions:
            if not decision.common_entities:
                fingerprint_gaps["no_common_entity"] += 1
            if not decision.common_actors:
                fingerprint_gaps["no_common_actor"] += 1
            if not decision.common_actions:
                fingerprint_gaps["no_common_action"] += 1
            if not decision.common_targets:
                fingerprint_gaps["no_common_target"] += 1
            if not decision.common_numbers:
                fingerprint_gaps["no_common_number"] += 1
        cache_counts = {
            row["status"]: row["count"] for row in connection.execute(
                "SELECT status,COUNT(*) AS count FROM ben_translation_summary_cache GROUP BY status"
            )
        }
    finally:
        connection.close()

    result = {
        "measured_at": now.isoformat(), "quality": quality,
        "top20": {
            "count": len(top),
            "chinese_title_count": sum(cjk_ready(event["display_title_zh"]) for event in top),
            "chinese_summary_count": sum(cjk_ready(event["summary_zh"]) for event in top),
            "translation_statuses": dict(Counter(event["translation_status"] for event in top)),
        },
        "translation_cache": cache_counts,
        "cross_platform_analysis": {
            "news_72h": len(prepared_news), "x_72h": len(prepared_x),
            "candidate_pairs": len(cross_decisions), "decision_labels": dict(cross_labels),
            "shared_normalized_url_pairs": shared_url_pairs,
            "fingerprint_gaps": dict(fingerprint_gaps),
            "outside_36h_related_pairs": len(outside_window),
            "examples": [
                {
                    "news": left["text"], "x": right["text"][:180],
                    "label": decision.label,
                    "reason": decision.merge_reason or decision.reject_reason,
                }
                for left, right, decision in cross_decisions[:5]
            ],
        },
        "top20_titles": [event["display_title_zh"] for event in top],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
