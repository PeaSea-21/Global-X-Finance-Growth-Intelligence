from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest

from global_x_finance.weekend_crawl import build_weekend_snapshot, select_recent_news


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE ben_news_items (
            id TEXT PRIMARY KEY,
            source_key TEXT NOT NULL,
            source_name TEXT NOT NULL,
            original_title TEXT NOT NULL,
            published_at TEXT NOT NULL,
            original_url TEXT NOT NULL,
            public_summary TEXT,
            market TEXT,
            language TEXT
        )
        """
    )
    return connection


def test_recent_news_separates_24h_fresh_from_48h_context() -> None:
    connection = _connection()
    now = datetime(2026, 8, 23, 6, tzinfo=timezone.utc)
    rows = [
        ("1", "cna", "中央社", "fresh", now - timedelta(hours=2), "https://example.com/1"),
        ("2", "cnbc", "CNBC", "context", now - timedelta(hours=30), "https://example.com/2"),
        ("3", "old", "Old", "old", now - timedelta(hours=60), "https://example.com/3"),
    ]
    for row_id, source_key, source_name, title, published, url in rows:
        connection.execute(
            """INSERT INTO ben_news_items
               (id, source_key, source_name, original_title, published_at,
                original_url, public_summary, market, language)
               VALUES (?, ?, ?, ?, ?, ?, '', 'TW', 'zh-Hant')""",
            (row_id, source_key, source_name, title, published.isoformat(), url),
        )

    selected = select_recent_news(connection, as_of=now)

    assert [row["title"] for row in selected] == ["fresh", "context"]
    assert [row["freshness_bucket"] for row in selected] == ["FRESH_24H", "CONTEXT_48H"]
    assert all(row["human_verification_url"].startswith("https://") for row in selected)
    assert all(row["source_class"] == "REPORTED_MEDIA" for row in selected)
    assert all(row["coverage_tags"] == ["GENERAL_FINANCE"] for row in selected)


def test_recent_news_requires_timezone_aware_as_of() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        select_recent_news(_connection(), as_of=datetime(2026, 8, 23, 12))


def test_weekend_snapshot_never_claims_post_close_manuscript() -> None:
    snapshot = build_weekend_snapshot(
        as_of=datetime(2026, 8, 23, 6, tzinfo=timezone.utc),
        label="primary",
        news_results=[{"status": "SUCCESS"}],
        news_items=[{"source_key": "cna", "freshness_bucket": "FRESH_24H"}],
        x_status={"status": "X_DEGRADED"},
    )

    assert snapshot["status"] == "NEWS_CRAWL_PASS"
    assert snapshot["is_post_close_manuscript"] is False
    assert snapshot["market_session_status"] == "NO_SAME_DAY_TW_SESSION_EXPECTED_ON_SUNDAY"
    assert snapshot["structured_data_gaps"]["ETF_NET_FLOWS"] == "UNAVAILABLE"


def test_optional_feed_failure_does_not_block_the_nine_source_base() -> None:
    snapshot = build_weekend_snapshot(
        as_of=datetime(2026, 8, 23, 6, tzinfo=timezone.utc),
        label="enrichment",
        news_results=[
            {
                "source_key": "base",
                "source_name": "Base",
                "status": "SUCCESS",
                "required": True,
                "valid_item_count": 1,
            },
            {
                "source_key": "optional",
                "source_name": "Optional",
                "status": "FAILED",
                "required": False,
                "valid_item_count": 0,
                "source_class": "OFFICIAL_PRIMARY",
                "coverage_tags": ["MACRO"],
            },
        ],
        news_items=[
            {
                "source_key": "base",
                "freshness_bucket": "FRESH_24H",
                "source_class": "REPORTED_MEDIA",
                "coverage_tags": ["GENERAL_FINANCE"],
            }
        ],
        x_status={"status": "PASS"},
    )

    assert snapshot["status"] == "NEWS_CRAWL_PASS"
    assert snapshot["required_source_success_count"] == 1
    assert snapshot["required_source_count"] == 1
    assert snapshot["optional_source_failure_count"] == 1
    assert snapshot["source_coverage"][1]["source_class"] == "OFFICIAL_PRIMARY"
