from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3

import pytest

from global_x_finance.realtime_radar import (
    RealtimeRadar,
    import_realtime_registry,
    load_realtime_registry,
    radar_summary,
)


NOW = datetime(2026, 8, 14, 12, 0, tzinfo=timezone.utc)


def source_row(source_id: str = "SYNTHETIC-X-001", **overrides):
    row = {
        "registry_source_id": source_id,
        "platform": "X",
        "source_type": "KOL_X_ACCOUNT",
        "account_handle": "synthetic_test_account",
        "profile_url": "https://x.com/synthetic_test_account",
        "channel_name": "",
        "channel_id": "",
        "channel_url": "",
        "publisher": "SYNTHETIC_TEST_DATA publisher",
        "publisher_group": "synthetic_test_group",
        "market": "TW",
        "language": "zh-Hant",
        "category": "SYNTHETIC_TEST_DATA",
        "verified_at": "2026-08-14T00:00:00Z",
        "verification_evidence_url": "https://example.invalid/synthetic-test",
        "monitoring_method": "SYNTHETIC_TEST_ADAPTER",
        "source_status": "VERIFIED_ACTIVE",
        "identity_verified": "VERIFIED",
        "endpoint_verified": "VERIFIED",
        "monitoring_method_verified": "VERIFIED",
        "terms_status": "UNKNOWN",
        "commercial_use_status": "UNKNOWN",
        "monitoring_status": "ACTIVE",
        "runtime_status": "SYNTHETIC_TEST_READY",
        "expected_interval_minutes": "10",
        "candidate_origin": "SYNTHETIC_TEST_DATA",
        "single_connectivity_verified": "true",
        "continuous_sla_verified": "false",
        "notes": "SYNTHETIC_TEST_DATA",
    }
    row.update(overrides)
    return row


def tweet():
    return {
        "id": "synthetic-001",
        "text": "SYNTHETIC_TEST_DATA only; not a real market statement",
        "url": "https://x.com/synthetic_test_account/status/synthetic-001",
        "created_at": "2026-08-14T11:55:00Z",
        "author": {"screen_name": "synthetic_test_account"},
    }


def test_same_tweet_three_cycles_creates_one_raw_opinion(database):
    import_realtime_registry(database, [source_row()], now=NOW)
    radar = RealtimeRadar(database, x_fetcher=lambda _: [tweet()], clock=lambda: NOW)

    results = [radar.run_cycle(force=True) for _ in range(3)]

    assert database.execute("SELECT COUNT(*) FROM raw_items WHERE original_url LIKE '%synthetic-001'").fetchone()[0] == 1
    item = database.execute(
        "SELECT fact_or_opinion, detection_latency_minutes FROM radar_items"
    ).fetchone()
    assert item["fact_or_opinion"] == "OPINION"
    assert item["detection_latency_minutes"] == 5.0
    assert [result.sources[0].new_count for result in results] == [1, 0, 0]
    assert [result.sources[0].duplicate_count for result in results] == [0, 1, 1]


def test_failure_preserves_last_success_and_records_real_error(database):
    import_realtime_registry(database, [source_row()], now=NOW)
    RealtimeRadar(database, x_fetcher=lambda _: [tweet()], clock=lambda: NOW).run_cycle(force=True)
    last_success = database.execute(
        "SELECT last_success_at FROM realtime_sources WHERE registry_source_id = 'SYNTHETIC-X-001'"
    ).fetchone()[0]

    def fail(_):
        raise RuntimeError("SYNTHETIC_TEST_DATA upstream unavailable")

    result = RealtimeRadar(database, x_fetcher=fail, clock=lambda: NOW).run_cycle(force=True)
    source = database.execute(
        "SELECT * FROM realtime_sources WHERE registry_source_id = 'SYNTHETIC-X-001'"
    ).fetchone()
    assert result.sources[0].status == "FAILED"
    assert source["last_success_at"] == last_success
    assert source["consecutive_failures"] == 1
    assert "upstream unavailable" in source["last_failure_reason"]
    assert source["monitoring_status"] == "ACTIVE"
    assert source["runtime_status"] == "CONTINUOUS_CYCLE_FAILED"


def test_same_publisher_group_counts_once(database):
    first = source_row("SYNTHETIC-X-001")
    second = source_row(
        "SYNTHETIC-X-002",
        account_handle="synthetic_test_account_2",
        profile_url="https://x.com/synthetic_test_account_2",
    )
    import_realtime_registry(database, [first, second], now=NOW)
    summary = radar_summary(database)
    assert summary["active"] == 2
    assert summary["independent_active_groups"] == 1


def test_youtube_video_fields_and_opinion_default(database):
    row = source_row(
        "SYNTHETIC-YT-001",
        platform="YOUTUBE",
        source_type="YOUTUBE_CHANNEL",
        account_handle="",
        profile_url="",
        channel_name="SYNTHETIC_TEST_DATA Channel",
        channel_id="synthetic-channel-id",
        channel_url="https://www.youtube.com/channel/synthetic-channel-id",
        monitoring_method="SYNTHETIC_TEST_ATOM",
        expected_interval_minutes="30",
    )
    import_realtime_registry(database, [row], now=NOW)
    video = {
        "id": "synthetic-video",
        "title": "SYNTHETIC_TEST_DATA video",
        "url": "https://www.youtube.com/watch?v=synthetic-video",
        "published_at": "2026-08-14T11:30:00Z",
    }
    RealtimeRadar(database, youtube_fetcher=lambda _: [video], clock=lambda: NOW).run_cycle(force=True)
    item = database.execute("SELECT * FROM radar_items").fetchone()
    assert item["source_account"] == "SYNTHETIC_TEST_DATA Channel"
    assert item["title_or_text"] == "SYNTHETIC_TEST_DATA video"
    assert item["published_at"] == "2026-08-14T11:30:00+00:00"
    assert item["evidence_url"].endswith("synthetic-video")
    assert item["fact_or_opinion"] == "OPINION"


def test_unverified_candidate_is_not_collected(database):
    row = source_row(
        source_status="NEEDS_VERIFICATION",
        identity_verified="UNKNOWN",
        endpoint_verified="UNKNOWN",
        monitoring_method_verified="NOT_VERIFIED",
        monitoring_status="NEEDS_VERIFICATION",
        verified_at="",
        verification_evidence_url="",
        expected_interval_minutes="",
    )
    import_realtime_registry(database, [row], now=NOW)
    result = RealtimeRadar(database, x_fetcher=lambda _: [tweet()], clock=lambda: NOW).run_cycle(force=True)
    assert result.sources == ()
    assert database.execute("SELECT monitoring_status FROM realtime_sources").fetchone()[0] == "NEEDS_VERIFICATION"


def test_public_endpoint_does_not_imply_terms_or_commercial_authorization(database):
    import_realtime_registry(database, [source_row()], now=NOW)
    source = database.execute("SELECT * FROM realtime_sources").fetchone()
    assert source["identity_verified"] == "VERIFIED"
    assert source["endpoint_verified"] == "VERIFIED"
    assert source["monitoring_method_verified"] == "VERIFIED"
    assert source["terms_status"] == "UNKNOWN"
    assert source["commercial_use_status"] == "UNKNOWN"
    assert source["monitoring_status"] == "ACTIVE"


def test_real_registry_keeps_governance_states_independent(root):
    rows = load_realtime_registry(root / "config" / "taiwan_realtime_sources.csv")
    active = [row for row in rows if row["monitoring_status"] == "ACTIVE"]
    youtube = [row for row in active if row["platform"] == "YOUTUBE"]

    assert len(rows) == 23
    assert len(active) == 6
    assert len(youtube) == 1
    assert all(row["identity_verified"] == "VERIFIED" for row in active)
    assert all(row["endpoint_verified"] == "VERIFIED" for row in active)
    assert all(row["monitoring_method_verified"] == "VERIFIED" for row in active)
    assert all(row["terms_status"] == "UNKNOWN" for row in active)
    assert all(row["commercial_use_status"] == "UNKNOWN" for row in active)
    assert "初始验证覆盖" in youtube[0]["notes"]
    assert "不是台湾YouTube覆盖完成" in youtube[0]["notes"]


def test_active_rejects_unverified_method_or_blocked_rights(database):
    with pytest.raises(sqlite3.IntegrityError):
        import_realtime_registry(
            database,
            [source_row(monitoring_method_verified="NOT_VERIFIED")],
            now=NOW,
        )
    with pytest.raises(sqlite3.IntegrityError):
        import_realtime_registry(
            database,
            [source_row(terms_status="BLOCKED")],
            now=NOW,
        )
    with pytest.raises(sqlite3.IntegrityError):
        import_realtime_registry(
            database,
            [source_row(commercial_use_status="MANUAL_ONLY")],
            now=NOW,
        )


def test_scheduler_state_survives_radar_restart(database):
    current = [NOW]
    import_realtime_registry(database, [source_row()], now=NOW)
    first = RealtimeRadar(database, x_fetcher=lambda _: [tweet()], clock=lambda: current[0])
    assert len(first.run_cycle().sources) == 1

    current[0] = NOW + timedelta(minutes=5)
    restarted = RealtimeRadar(database, x_fetcher=lambda _: [tweet()], clock=lambda: current[0])
    assert restarted.run_cycle().sources == ()

    current[0] = NOW + timedelta(minutes=10, seconds=1)
    assert len(restarted.run_cycle().sources) == 1


def test_cycle_schedule_anchor_prevents_sequential_source_minute_split(database):
    first = source_row("SYNTHETIC-X-001")
    second = source_row(
        "SYNTHETIC-X-002",
        account_handle="synthetic_test_account_2",
        profile_url="https://x.com/synthetic_test_account_2",
        publisher_group="synthetic_test_group_2",
    )
    import_realtime_registry(database, [first, second], now=NOW)
    ticks = [NOW.replace(second=58) + timedelta(seconds=2 * index) for index in range(20)]

    def advancing_clock():
        return ticks.pop(0)

    RealtimeRadar(
        database,
        x_fetcher=lambda _: [tweet()],
        clock=advancing_clock,
    ).run_cycle(force=True)

    next_due = database.execute(
        "SELECT next_due_at FROM radar_scheduler_state ORDER BY realtime_source_id"
    ).fetchall()
    assert {row["next_due_at"] for row in next_due} == {
        "2026-08-14T12:10:00+00:00"
    }


def test_overlapping_process_is_skipped_by_database_lock(database):
    import_realtime_registry(database, [source_row()], now=NOW)
    database.execute(
        """
        UPDATE radar_runtime_lock SET owner_id = 'another-process',
            locked_until = '2026-08-14T12:08:00+00:00'
        WHERE lock_name = 'taiwan_realtime_radar'
        """
    )
    database.commit()

    result = RealtimeRadar(
        database, x_fetcher=lambda _: [tweet()], clock=lambda: NOW
    ).run_cycle(force=True)

    assert result.sources == ()
    assert database.execute("SELECT COUNT(*) FROM radar_runs").fetchone()[0] == 0


def test_radar_health_and_recent_feed_pages(database, database_path, root):
    from global_x_finance.webapp import create_app

    import_realtime_registry(database, [source_row()], now=NOW)
    RealtimeRadar(database, x_fetcher=lambda _: [tweet()], clock=lambda: NOW).run_cycle(force=True)
    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.testing = True
    client = app.test_client()

    health = client.get("/radar").get_data(as_text=True)
    feed = client.get("/radar/feed?hours=72").get_data(as_text=True)
    assert "台灣來源健康" in health
    assert "SYNTHETIC-X-001" in health
    assert "CONTINUOUS_CYCLE_SUCCESS" in health
    assert "identity_verified" in health
    assert "terms_status" in health
    assert "commercial_use_status" in health
    assert "公開可存取不等於商業監控授權" in health
    # The fixed synthetic timestamp is outside the app's current 72-hour window.
    assert client.get("/radar/feed").status_code == 200
    assert "最近 72 小時內容流" in feed
