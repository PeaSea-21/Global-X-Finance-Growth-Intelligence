from __future__ import annotations

import json
import sqlite3
from datetime import date, timedelta

from global_x_finance.anomaly_engine import AnomalyEngine, AnomalyRuleConfig


def _connection() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        CREATE TABLE official_securities (
            id TEXT PRIMARY KEY, exchange_code TEXT, ticker TEXT, company_name TEXT
        );
        CREATE TABLE official_market_data_daily (
            security_id TEXT, exchange_code TEXT, trade_date TEXT,
            opening_price TEXT, highest_price TEXT, lowest_price TEXT, closing_price TEXT,
            trade_volume INTEGER, trade_value INTEGER, data_status TEXT
        );
        """
    )
    return connection


def _config(tmp_path, **overrides) -> AnomalyRuleConfig:
    raw = {
        "version": "TEST",
        "minimum_prior_sessions": 20,
        "volume_baseline_sessions": 20,
        "volume_spike_ratio": 2.0,
        "range_breakout_sessions": [20, 40],
        "quiet_recent_sessions": 5,
        "quiet_recent_to_normal_max": 0.6,
        "quiet_current_to_normal_min": 2.0,
        "quiet_current_to_recent_min": 3.0,
        "price_return_sessions": 20,
        "price_anomaly_abs_zscore": 2.5,
        "extreme_prior_return_abs_pct": 30.0,
    }
    raw.update(overrides)
    path = tmp_path / "rules.json"
    path.write_text(json.dumps(raw), encoding="utf-8")
    return AnomalyRuleConfig.load(path)


def _seed(connection, *, security_id="TWSE:0001", volumes=None, closes=None, current_volume=3000, current_close=130):
    volumes = volumes or [1000] * 40
    closes = closes or [100 + index * 0.5 for index in range(40)]
    start = date(2026, 6, 1)
    connection.execute("INSERT INTO official_securities VALUES (?,?,?,?)", (security_id, "TWSE", "0001", "测试股"))
    for index, (volume, close) in enumerate(zip(volumes, closes)):
        day = (start + timedelta(days=index)).isoformat()
        connection.execute(
            "INSERT INTO official_market_data_daily VALUES (?,?,?,?,?,?,?,?,?,?)",
            (security_id, "TWSE", day, str(close), str(close + 1), str(close - 1), str(close), volume, volume * int(close), "EOD"),
        )
    replay_date = (start + timedelta(days=40)).isoformat()
    connection.execute(
        "INSERT INTO official_market_data_daily VALUES (?,?,?,?,?,?,?,?,?,?)",
        (security_id, "TWSE", replay_date, str(current_close - 1), str(current_close + 1), str(current_close - 2), str(current_close), current_volume, current_volume * current_close, "EOD"),
    )
    connection.commit()
    return replay_date


def test_prior_only_baseline_and_price_volume_breakout(tmp_path):
    connection = _connection()
    replay_date = _seed(connection)
    replay = AnomalyEngine(connection, _config(tmp_path)).replay(replay_date)
    row = replay["ranked"][0]
    assert row["raw_metrics"]["median_volume_20d"] == 1000
    assert row["raw_metrics"]["volume_ratio"] == 3
    assert row["raw_metrics"]["prior_20d_high"] == 120.5
    assert row["raw_metrics"]["prior_40d_high"] == 120.5
    assert "VOLUME_SPIKE" in row["matched_rules"]
    assert "RANGE_BREAKOUT_20D" in row["matched_rules"]
    assert "PRICE_VOLUME_BREAKOUT" in row["matched_rules"]


def test_quiet_to_spike_and_duplicate_free_single_security(tmp_path):
    connection = _connection()
    replay_date = _seed(connection, volumes=[1000] * 35 + [400] * 5, current_volume=3000)
    replay = AnomalyEngine(connection, _config(tmp_path)).replay(replay_date)
    row = replay["ranked"][0]
    assert row["raw_metrics"]["median_volume_20d"] == 1000
    assert row["raw_metrics"]["median_volume_recent5d"] == 400
    assert "QUIET_TO_VOLUME_SPIKE" in row["matched_rules"]
    assert len(replay["ranked"]) == 1


def test_price_move_without_volume_is_not_price_volume_breakout(tmp_path):
    connection = _connection()
    replay_date = _seed(connection, current_volume=1000, current_close=130)
    row = AnomalyEngine(connection, _config(tmp_path)).replay(replay_date)["ranked"][0]
    assert "RANGE_BREAKOUT_20D" in row["matched_rules"]
    assert "VOLUME_SPIKE" not in row["matched_rules"]
    assert "PRICE_VOLUME_BREAKOUT" not in row["matched_rules"]


def test_insufficient_and_extreme_history_are_excluded(tmp_path):
    connection = _connection()
    replay_date = _seed(connection, security_id="TWSE:0001")
    connection.execute("INSERT INTO official_securities VALUES (?,?,?,?)", ("TPEX:0002", "TPEX", "0002", "新股"))
    connection.execute(
        "INSERT INTO official_market_data_daily VALUES (?,?,?,?,?,?,?,?,?,?)",
        ("TPEX:0002", "TPEX", replay_date, "10", "10", "10", "10", 100, 1000, "EOD"),
    )
    connection.execute("UPDATE official_market_data_daily SET closing_price='0', opening_price='0', highest_price='0', lowest_price='0' WHERE security_id='TWSE:0001' AND trade_date=(SELECT MIN(trade_date) FROM official_market_data_daily WHERE security_id='TWSE:0001')")
    connection.commit()
    replay = AnomalyEngine(connection, _config(tmp_path)).replay(replay_date)
    qualities = {row["security_id"]: row["data_quality"] for row in replay["excluded"]}
    assert qualities["TWSE:0001"] == "EXTREME_OFFICIAL_DATA"
    assert qualities["TPEX:0002"] == "INSUFFICIENT_HISTORY"


def test_rule_count_precedes_severity_in_ranking(tmp_path):
    connection = _connection()
    replay_date = _seed(connection, security_id="TWSE:0001", current_volume=3000, current_close=130)
    _seed(connection, security_id="TWSE:0002", current_volume=10000, current_close=110)
    ranked = AnomalyEngine(connection, _config(tmp_path)).replay(replay_date)["ranked"]
    assert len(ranked[0]["matched_rules"]) > len(ranked[1]["matched_rules"])
    assert ranked[0]["security_id"] == "TWSE:0001"


def test_liquidity_context_is_market_relative_and_not_in_ranking_key(tmp_path):
    connection = _connection()
    replay_date = _seed(connection, security_id="TWSE:0001", current_volume=3000, current_close=130)
    _seed(connection, security_id="TWSE:0002", current_volume=300, current_close=110)
    engine = AnomalyEngine(connection, _config(tmp_path))
    ranked = engine.replay(replay_date)["ranked"]
    by_id = {row["security_id"]: row for row in ranked}
    assert by_id["TWSE:0001"]["liquidity_level"] == "HIGH"
    assert by_id["TWSE:0002"]["liquidity_level"] == "LOW"
    assert by_id["TWSE:0001"]["median_volume_20d"] == 1000
    before = engine._ranking_key(by_id["TWSE:0001"])
    by_id["TWSE:0001"]["market_volume_percentile"] = 0
    by_id["TWSE:0001"]["liquidity_level"] = "LOW"
    assert engine._ranking_key(by_id["TWSE:0001"]) == before
