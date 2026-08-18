from __future__ import annotations

import json
from datetime import date, datetime, timedelta

import pytest

from global_x_finance.errors import ValidationError
from global_x_finance.market_history_backfill import MarketHistoryBackfillService
from global_x_finance.official_data import load_official_data_config
from global_x_finance.twse_collector import HttpResponse


NOW = datetime.fromisoformat("2026-08-17T17:00:00+08:00")


def _seed_securities(database):
    market_id = database.execute("SELECT id FROM markets WHERE country_code='TW'").fetchone()[0]
    source_ids = {
        row["source_id"]: row["id"]
        for row in database.execute(
            "SELECT id, source_id FROM sources WHERE source_id IN ('TW-A02','TW-A04')"
        )
    }
    for exchange, ticker, name, source_id in (
        ("TWSE", "2330", "台積電", source_ids["TW-A02"]),
        ("TWSE", "2317", "鴻海", source_ids["TW-A02"]),
        ("TPEX", "6488", "環球晶", source_ids["TW-A04"]),
        ("TPEX", "8299", "群聯", source_ids["TW-A04"]),
    ):
        database.execute(
            """
            INSERT INTO official_securities (
                id, market_id, exchange_code, ticker, company_name,
                mapping_status, first_source_id, first_seen_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, 'OFFICIAL_MARKET_DATA', ?, ?, ?)
            """,
            (
                f"{exchange}:{ticker}", market_id, exchange, ticker, name,
                source_id, NOW.isoformat(), NOW.isoformat(),
            ),
        )
    database.commit()


def _response_date(url: str) -> str:
    if "MI_INDEX" in url:
        compact = url.split("date=", 1)[1].split("&", 1)[0]
    else:
        value = url.split("date=", 1)[1].split("&", 1)[0]
        compact = value.replace("/", "")
    return compact


def _transport(counter: list[str]):
    def transport(url: str, timeout: float) -> HttpResponse:
        assert timeout == 60
        counter.append(url)
        compact = _response_date(url)
        if "MI_INDEX" in url:
            payload = {
                "stat": "OK",
                "date": compact,
                "tables": [{
                    "fields": [
                        "證券代號", "證券名稱", "成交股數", "成交筆數", "成交金額",
                        "開盤價", "最高價", "最低價", "收盤價", "漲跌(+/-)", "漲跌價差",
                    ],
                    "data": [[
                        "2330", "台積電", "1,000", "50", "2,000",
                        "10", "12", "9", "11", "+", "1",
                    ]],
                }],
            }
        else:
            payload = {
                "stat": "ok",
                "date": compact,
                "tables": [{
                    "fields": [
                        "代號", "名稱", "收盤", "漲跌", "開盤", "最高", "最低",
                        "成交股數", "成交金額(元)", "成交筆數",
                    ],
                    "data": [[
                        "6488", "環球晶", "101", "1", "100", "102", "99",
                        "3,000", "300,000", "70",
                    ]],
                }],
            }
        return HttpResponse(
            200,
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            "application/json",
        )

    return transport


def _service(database, root, tmp_path, calls, *, minimum_days=2):
    return MarketHistoryBackfillService(
        database,
        load_official_data_config(root / "config" / "official_data.sources.json"),
        status_path=tmp_path / "backfill_status.json",
        target_days=2,
        minimum_days=minimum_days,
        transport=_transport(calls),
        now=NOW,
    )


def test_batch_backfill_writes_shared_schema_ids_and_exact_units(database, root, tmp_path):
    _seed_securities(database)
    calls = []
    result = _service(database, root, tmp_path, calls).run()

    assert result["status"] == "COMPLETE"
    assert len(calls) == 4
    twse = database.execute(
        "SELECT * FROM official_market_data_daily WHERE security_id='TWSE:2330' ORDER BY trade_date"
    ).fetchall()
    tpex = database.execute(
        "SELECT * FROM official_market_data_daily WHERE security_id='TPEX:6488' ORDER BY trade_date"
    ).fetchall()
    assert len(twse) == len(tpex) == 2
    assert {row["security_id"] for row in twse + tpex} == {"TWSE:2330", "TPEX:6488"}
    assert {row["trade_volume"] for row in twse} == {1000}
    assert {row["trade_volume"] for row in tpex} == {3000}
    assert {row["trade_value"] for row in tpex} == {300000}
    assert all(row["opening_price"] and row["closing_price"] for row in twse + tpex)


def test_duplicate_protection_and_resume_skip_existing_batches(database, root, tmp_path):
    _seed_securities(database)
    calls = []
    first = _service(database, root, tmp_path, calls).run()
    row_count = database.execute("SELECT COUNT(*) FROM official_market_data_daily").fetchone()[0]
    raw_count = database.execute("SELECT COUNT(*) FROM raw_items").fetchone()[0]

    second_calls = []
    second = _service(database, root, tmp_path, second_calls).run()
    assert first["status"] == second["status"] == "COMPLETE"
    assert second_calls == []
    assert database.execute("SELECT COUNT(*) FROM official_market_data_daily").fetchone()[0] == row_count
    assert database.execute("SELECT COUNT(*) FROM raw_items").fetchone()[0] == raw_count
    assert second["audit"]["duplicate_security_dates"] == 0


def test_history_status_marks_ready_and_insufficient_without_fake_rows(database, root, tmp_path):
    _seed_securities(database)
    status = _service(database, root, tmp_path, []).run()
    states = {
        row["id"]: (row["history_status"], row["history_trade_days"])
        for row in database.execute(
            "SELECT id, history_status, history_trade_days FROM official_securities"
        )
    }
    assert states["TWSE:2330"] == ("READY", 2)
    assert states["TPEX:6488"] == ("READY", 2)
    assert states["TWSE:2317"] == ("INSUFFICIENT_HISTORY", 0)
    assert states["TPEX:8299"] == ("INSUFFICIENT_HISTORY", 0)
    assert status["audit"]["markets"]["TWSE"]["ge_minimum"] == 1
    assert status["audit"]["markets"]["TPEX"]["insufficient"] == 1


def test_future_dates_are_rejected_and_audit_has_no_future_leakage(database, root, tmp_path):
    _seed_securities(database)
    service = _service(database, root, tmp_path, [])
    with pytest.raises(ValidationError, match="Future trade dates"):
        service.collect_market_date("TWSE", NOW.date() + timedelta(days=1))
    status = service.run()
    assert status["audit"]["future_date"] == 0
    assert status["audit"]["invalid_date"] == 0
    assert status["audit"]["unmapped_security"] == 0
    assert status["audit"]["null_ohlcv_eod"] == 0
