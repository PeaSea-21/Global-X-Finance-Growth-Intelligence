from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from global_x_finance.pipeline_trace import build_news_pipeline_trace, market_security_id
from global_x_finance.radar_analytics import select_snapshot_events, source_concentration
from global_x_finance.stock_signals import build_stock_signals


NOW = datetime(2026, 8, 17, 6, tzinfo=timezone.utc)


def _event(event_id: str, score: int, publisher: str, *, news: bool = False, ticker: str | None = None):
    item = {
        "kind": "NEWS" if news else "X",
        "id": event_id,
        "publisher": publisher,
        "publisher_group": publisher,
        "published_at": NOW.isoformat(),
        "is_repost": False,
    }
    return {
        "event_id": event_id,
        "score": score,
        "latest_update_at": NOW.isoformat(),
        "primary": item,
        "items": [item],
        "news_items": [item] if news else [],
        "x_items": [] if news else [item],
        "news_count": 1 if news else 0,
        "x_count": 0 if news else 1,
        "independent_count": 1,
        "entities": [ticker] if ticker else [],
        "related_stocks": [{"ticker": ticker, "relationship": "DIRECT"}] if ticker else [],
        "display_title_zh": "測試事件",
    }


def test_market_qualified_security_ids_do_not_collapse_cross_listings():
    assert market_security_id("2330") == "TWSE:2330"
    assert market_security_id("TSM") == "NYSE:TSM"
    assert market_security_id("2330") != market_security_id("TSM")


def test_trace_has_one_terminal_reason_per_news_item():
    current = {
        "id": "current", "source_key": "yahoo_tw", "source_name": "Yahoo奇摩股市",
        "original_title": "台積電發布最新財報", "published_at": (NOW - timedelta(hours=1)).isoformat(),
        "original_url": "https://example.test/current",
    }
    old = {**current, "id": "old", "published_at": (NOW - timedelta(hours=25)).isoformat(), "original_url": "https://example.test/old"}
    event = _event("evt-current", 60, "yahoo", news=True, ticker="2330")
    event["news_items"][0]["id"] = "current"
    rows = build_news_pipeline_trace([current, old], [event], now=NOW, snapshot_event_ids={"evt-current"})
    assert rows[0]["snapshot_status"] == "INCLUDED"
    assert rows[0]["drop_reason"] == ""
    assert rows[1]["drop_reason"] == "OUTSIDE_TIME_WINDOW"
    assert rows[1]["drop_stage"] == "TIME_WINDOW"


def test_source_concentration_warning_and_diversity_aware_selection():
    events = [_event(f"x-{index}", 70 - index, "dominant") for index in range(8)]
    events += [_event("news", 58, "independent-news", news=True)]
    concentration = source_concentration(events)
    assert concentration["status"] == "SOURCE_CONCENTRATION_WARNING"
    selected = select_snapshot_events(events, limit=5)
    assert any(event["event_id"] == "news" for event in selected)


def test_stock_signal_uses_only_prior_twenty_completed_sessions(database):
    start = date(2026, 7, 1)
    for index in range(22):
        trade_date = (start + timedelta(days=index)).isoformat()
        database.execute(
            """INSERT INTO ben_stock_history
               (id,stock_code,company_name,trade_date,opening_price,highest_price,lowest_price,
                closing_price,trade_volume,trade_value,source_url,fetched_at,raw_payload_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()), "2330", "台積電", trade_date, "100", "110", "90",
                "110" if index == 21 else "100", 3_000_000 if index == 21 else 1_000_000,
                330_000_000 if index == 21 else 100_000_000, "https://example.test/twse",
                NOW.isoformat(), "{}",
            ),
        )
    database.commit()
    signals = build_stock_signals(database, [_event("evt-tsmc", 80, "yahoo", news=True, ticker="2330")])
    signal = next(row for row in signals if row["ticker"] == "2330")
    assert signal["volume_baseline_20d_median"] == 1_000_000
    assert signal["volume_ratio"] == 3.0
    assert signal["turnover_ratio"] == 3.3
    assert signal["change_pct"] == 10.0
    assert "MULTI_SIGNAL" in signal["abnormal_flags"]
    assert signal["data_quality"] == "COMPLETE"

