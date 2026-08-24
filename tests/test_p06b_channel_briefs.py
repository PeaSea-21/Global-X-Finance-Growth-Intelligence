from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import global_x_finance.channel_briefs as channel_briefs
from global_x_finance.channel_briefs import (
    _eligible_candidates,
    _event_rows,
    _rank_channel,
    _source_readiness,
    build_channel_briefs,
    load_channel_pilot_config,
    persist_channel_briefs,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "channel_pilots.v0.1.json"
ANOMALY_CONFIG = ROOT / "config" / "anomaly_rules.v0.1.json"
AS_OF = datetime.fromisoformat("2026-08-17T15:05:00+08:00")
SCHEDULED_FOR = datetime.fromisoformat("2026-08-17T13:45:00+08:00")


def _replay_row(index: int) -> dict:
    ticker = f"10{index:02d}"
    return {
        "security_id": f"TWSE:{ticker}",
        "ticker": ticker,
        "name": f"测试股{index}",
        "market": "TWSE",
        "matched_rules": ["VOLUME_SPIKE", "PRICE_VOLUME_BREAKOUT"] if index < 3 else ["VOLUME_SPIKE"],
        "why_selected": "当日收盘价量异动",
        "data_quality": "COMPLETE",
        "rank": index,
        "raw_metrics": {
            "close": 100 + index,
            "change_pct": float(index),
            "current_volume": 3_000_000 + index,
            "median_volume_20d": 1_000_000,
            "volume_ratio": 3.0 - index / 10,
            "abs_price_zscore": 3.0 - index / 10,
        },
    }


def _patch_build_inputs(monkeypatch, *, rows: list[dict] | None = None) -> None:
    replay_rows = rows if rows is not None else [_replay_row(index) for index in range(1, 7)]

    class FakeEngine:
        def __init__(self, *_args, **_kwargs):
            pass

        def replay(self, replay_date):
            return {
                "rule_version": "TEST-P06B",
                "replay_date": replay_date,
                "ranked": replay_rows,
            }

    industries = {
        row["security_id"]: {
            "security_id": row["security_id"],
            "official_industry_code": "24" if index <= 2 else "25" if index <= 4 else "26",
            "official_industry_name": "半导体业" if index <= 2 else "电脑及周边设备业" if index <= 4 else "光电业",
            "normalized_sector": "SEMICONDUCTORS" if index <= 2 else "TECH_HARDWARE_A" if index <= 4 else "TECH_HARDWARE_B",
            "mapping_status": "MAPPED_COMMON_STOCK",
            "raw_item_id": f"industry-raw-{index}",
        }
        for index, row in enumerate(replay_rows, start=1)
    }
    evidence = lambda _connection, security_id, replay_date: [{
        "evidence_id": f"raw-{security_id}",
        "evidence_class": "OFFICIAL_EOD",
        "source_id": "TW-A01",
        "url": "https://example.test/eod",
        "trade_date": replay_date,
        "observed_at": f"{replay_date}T15:00:00+08:00",
        "epistemic_status": "FACT",
    }]
    disclosure = {
        "candidate_id": "disclosure:test",
        "candidate_type": "DISCLOSURE",
        "title": "测试股1公告重大讯息",
        "market_session_date": "2026-08-17",
        "data_as_of": AS_OF.isoformat(),
        "freshness_state": "WITHIN_LOOKBACK_WINDOW",
        "security_ids": [replay_rows[0]["security_id"]],
        "industry_keys": [industries[replay_rows[0]["security_id"]]["normalized_sector"]],
        "facts": ["官方重大讯息"],
        "evidence": [{
            "evidence_id": "mops-1",
            "evidence_class": "OFFICIAL_DISCLOSURE",
            "source_id": "TW-A03",
            "url": "https://example.test/mops",
            "announced_at": "2026-08-17T14:00:00+08:00",
            "observed_at": "2026-08-17T14:00:00+08:00",
            "epistemic_status": "FACT",
        }],
        "opinion_evidence": [],
        "unknowns": [],
        "risk_flags": ["NO_CAUSAL_INFERENCE"],
        "stock_details": [],
        "editorial_status": "READY_TO_PITCH",
        "catalyst_status": "MOPS_CONFIRMED",
        "why_now": ["收盘简报截止前发布"],
        "sort_metrics": {"official_evidence": 1, "independent_sources": 1, "rule_count": 2, "volume_ratio": 2.9},
    }
    source_rows = [
        {"source": "TWSE_EOD", "required": True, "status": "READY"},
        {"source": "TPEX_EOD", "required": True, "status": "READY"},
        {"source": "MOPS", "required": False, "status": "AVAILABLE"},
        {"source": "NEWS", "required": False, "status": "EMPTY"},
        {"source": "X", "required": False, "status": "EMPTY"},
        {"source": "INDUSTRY_MAPPING", "required": False, "status": "AVAILABLE"},
    ]
    monkeypatch.setattr(channel_briefs, "AnomalyEngine", FakeEngine)
    monkeypatch.setattr(channel_briefs, "_industry_map", lambda _connection: industries)
    monkeypatch.setattr(channel_briefs, "_market_evidence", evidence)
    monkeypatch.setattr(channel_briefs, "_source_readiness", lambda *_args, **_kwargs: ("DEGRADED", "OPTIONAL_SOURCE_GAPS", source_rows))
    def disclosures(
        _connection, *, replay_date, as_of, lookback_hours, replay_rows, industries
    ):
        return [disclosure]

    def media_events(
        _connection, *, replay_date, as_of, lookback_hours, replay_rows, industries,
        include_x=True,
    ):
        assert include_x is True
        return []

    monkeypatch.setattr(channel_briefs, "_disclosure_candidates", disclosures)
    monkeypatch.setattr(channel_briefs, "_media_event_candidates", media_events)


def test_three_channel_routes_are_distinct_and_shortage_is_honest(database, monkeypatch):
    _patch_build_inputs(monkeypatch)
    payload = build_channel_briefs(
        database,
        config_path=CONFIG,
        anomaly_config_path=ANOMALY_CONFIG,
        replay_date="2026-08-17",
        generated_at=AS_OF,
    )
    by_type = {brief["channel_type"]: brief for brief in payload["briefs"]}
    assert {row["candidate_type"] for row in by_type["SIGNAL_HEAVY"]["assignments"]} == {"MARKET_SIGNAL"}
    assert by_type["EVENT_HEAVY"]["assignments"][0]["candidate_type"] == "DISCLOSURE"
    assert all(row["candidate_type"] == "CROSS_ENTITY" for row in by_type["CROSS_ENTITY"]["assignments"])
    assert by_type["SIGNAL_HEAVY"]["status"] == "READY"
    assert by_type["CROSS_ENTITY"]["status"] == "HONEST_SHORTAGE"
    assert by_type["CROSS_ENTITY"]["qualified_count"] == 3
    assert "INSUFFICIENT_CROSS_ENTITY_SIGNALS" in by_type["CROSS_ENTITY"]["shortage_reasons"]
    signal_in_event = next(row for row in by_type["EVENT_HEAVY"]["assignments"] if row["candidate_type"] == "MARKET_SIGNAL")
    assert signal_in_event["editorial_status"] == "NEEDS_RESEARCH"
    signal_ids = [row["candidate_id"] for row in by_type["SIGNAL_HEAVY"]["assignments"][:5]]
    event_ids = [row["candidate_id"] for row in by_type["EVENT_HEAVY"]["assignments"][:5]]
    assert signal_ids != event_ids
    assert payload["ranking_method"] == "RULE_BASED_FALLBACK"


def test_live_session_uses_real_generation_cutoff_and_historical_replay_uses_schedule(
    database, monkeypatch
):
    _patch_build_inputs(monkeypatch)
    live_time = datetime.fromisoformat("2026-08-17T14:10:00+08:00")
    live = build_channel_briefs(
        database,
        config_path=CONFIG,
        anomaly_config_path=ANOMALY_CONFIG,
        replay_date="2026-08-17",
        generated_at=live_time,
    )
    assert live["data_as_of"] == live_time.isoformat()
    assert live["scheduled_for"] == SCHEDULED_FOR.isoformat()
    assert live["replay_mode"] is False

    historical = build_channel_briefs(
        database,
        config_path=CONFIG,
        anomaly_config_path=ANOMALY_CONFIG,
        replay_date="2026-08-17",
        generated_at=datetime.fromisoformat("2026-08-18T12:00:00+08:00"),
    )
    assert historical["data_as_of"] == SCHEDULED_FOR.isoformat()
    assert historical["replay_mode"] is True


def test_hard_gate_blocks_future_evidence_missing_evidence_and_bad_security_id():
    profile = load_channel_pilot_config(CONFIG)[1][0]
    base = {
        "candidate_id": "signal:base",
        "candidate_type": "MARKET_SIGNAL",
        "title": "可用候选",
        "market_session_date": "2026-08-17",
        "data_as_of": AS_OF.isoformat(),
        "security_ids": ["TWSE:2330"],
        "evidence": [{"trade_date": "2026-08-17"}],
        "opinion_evidence": [],
    }
    future = {**base, "candidate_id": "signal:future", "title": "未来候选", "evidence": [{"trade_date": "2026-08-18"}]}
    no_evidence = {**base, "candidate_id": "signal:none", "title": "无证据候选", "evidence": []}
    bad_id = {**base, "candidate_id": "signal:bad-id", "title": "坏ID候选", "security_ids": ["2330"]}
    eligible, drops = _eligible_candidates(
        profile, [base, future, no_evidence, bad_id], replay_date="2026-08-17", as_of=AS_OF
    )
    assert [row["candidate_id"] for row in eligible] == ["signal:base"]
    assert drops == {
        "FUTURE_TRADE_DATE": 1,
        "NO_TRACEABLE_EVIDENCE": 1,
        "INVALID_MARKET_SECURITY_ID": 1,
    }


def test_event_window_compares_real_instants_not_iso_text(monkeypatch):
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE ben_news_items (id TEXT, published_at TEXT);
        CREATE TABLE ben_x_accounts (id TEXT, market_scope TEXT, impact_path TEXT);
        CREATE TABLE ben_x_posts (id TEXT, account_id TEXT, created_at TEXT);
        INSERT INTO ben_news_items VALUES ('within', '2026-08-17T14:30:00+08:00');
        INSERT INTO ben_news_items VALUES ('future-offset', '2026-08-17T07:30:01+00:00');
        INSERT INTO ben_x_accounts VALUES ('account', 'TW', 'DIRECT');
        INSERT INTO ben_x_posts VALUES ('x-within', 'account', '2026-08-17T07:05:00+00:00');
        INSERT INTO ben_x_posts VALUES ('x-future', 'account', '2026-08-17T16:00:00+08:00');
        """
    )
    captured = {}

    def capture(news, x_rows, now):
        captured.update(news=news, x=x_rows, now=now)
        return []

    monkeypatch.setattr(channel_briefs, "build_unified_events", capture)
    assert _event_rows(connection, as_of=AS_OF, lookback_hours=72) == []
    assert [row["id"] for row in captured["news"]] == ["within"]
    assert [row["id"] for row in captured["x"]] == ["x-within"]

    assert _event_rows(
        connection, as_of=AS_OF, lookback_hours=72, include_x=False
    ) == []
    assert captured["x"] == []


def test_source_readiness_counts_real_instants_not_future_text_values():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE official_securities (id TEXT, exchange_code TEXT);
        CREATE TABLE official_market_data_daily (security_id TEXT, exchange_code TEXT, trade_date TEXT, data_status TEXT);
        CREATE TABLE ben_news_items (published_at TEXT);
        CREATE TABLE ben_x_posts (created_at TEXT);
        CREATE TABLE official_disclosures (announced_at TEXT);
        INSERT INTO official_securities VALUES ('TWSE:1','TWSE'),('TPEX:1','TPEX');
        INSERT INTO official_market_data_daily VALUES ('TWSE:1','TWSE','2026-08-17','EOD'),('TPEX:1','TPEX','2026-08-17','EOD');
        INSERT INTO ben_news_items VALUES ('2026-08-17T14:30:00+08:00'),('2026-08-17T07:30:01+00:00');
        INSERT INTO ben_x_posts VALUES ('2026-08-17T07:05:00+00:00'),('2026-08-17T16:00:00+08:00');
        """
    )
    state, coverage, sources = _source_readiness(
        connection, replay_date="2026-08-17", as_of=AS_OF,
        minimum_coverage=1.0, lookback_hours=72,
    )
    by_source = {row["source"]: row for row in sources}
    assert state == "DEGRADED"
    assert coverage == "OPTIONAL_SOURCE_GAPS"
    assert by_source["NEWS"]["record_count"] == 1
    assert by_source["X"]["record_count"] == 1

    state, coverage, sources = _source_readiness(
        connection, replay_date="2026-08-17", as_of=AS_OF,
        minimum_coverage=1.0, lookback_hours=72, include_x=False,
    )
    by_source = {row["source"]: row for row in sources}
    assert state == "DEGRADED"
    assert coverage == "OPTIONAL_SOURCE_GAPS"
    assert by_source["X"]["status"] == "DISABLED"
    assert by_source["X"]["record_count"] == 0


def test_invalid_ai_order_falls_back_without_fake_ai_label():
    profile = load_channel_pilot_config(CONFIG)[1][0]

    class InvalidAiRanker:
        method = "AI_RANKED"
        detail = {"provider": "test"}

        def rank(self, _profile, _candidates):
            return [("invented-candidate", ["模型生成"])]

    candidate = {
        "candidate_id": "signal:one",
        "candidate_type": "MARKET_SIGNAL",
        "sort_metrics": {"rule_count": 1, "volume_ratio": 2},
        "editorial_status": "WATCH_ONLY",
    }
    ranked, method, detail = _rank_channel(profile, [candidate], InvalidAiRanker())
    assert method == "RULE_BASED_FALLBACK"
    assert ranked[0]["candidate_id"] == "signal:one"
    assert "fallback_error" in detail


def test_same_input_is_idempotent_and_new_input_creates_new_versions(database, monkeypatch):
    _patch_build_inputs(monkeypatch)
    payload = build_channel_briefs(
        database, config_path=CONFIG, anomaly_config_path=ANOMALY_CONFIG,
        replay_date="2026-08-17", generated_at=AS_OF,
    )
    first, created_first = persist_channel_briefs(database, payload, config_path=CONFIG)
    second, created_second = persist_channel_briefs(database, payload, config_path=CONFIG)
    assert created_first is True
    assert created_second is False
    assert first["run_id"] == second["run_id"]
    assert database.execute("SELECT COUNT(*) FROM ben_channel_brief_runs").fetchone()[0] == 1
    assert database.execute("SELECT COUNT(*) FROM ben_channel_daily_briefs").fetchone()[0] == 3

    changed = {**payload, "input_fingerprint": "f" * 64, "generated_at": "2026-08-17T16:00:00+08:00"}
    third, created_third = persist_channel_briefs(database, changed, config_path=CONFIG)
    assert created_third is True
    assert all(brief["brief_version"] == 2 for brief in third["briefs"])
