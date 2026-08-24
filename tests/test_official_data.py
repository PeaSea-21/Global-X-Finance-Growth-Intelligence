from __future__ import annotations

import copy
import json
from datetime import datetime

import pytest

from global_x_finance.errors import ValidationError
from global_x_finance.official_data import (
    OfficialDataService,
    load_official_data_config,
    official_data_status,
    recent_disclosures,
    volume_history,
)
from global_x_finance.twse_collector import HttpResponse


def _config(root):
    config = copy.deepcopy(
        load_official_data_config(root / "config" / "official_data.sources.json")
    )
    config["history_months"] = 1
    next(row for row in config["sources"] if row["source_key"] == "TWSE")[
        "history_tickers"
    ] = ["2330"]
    next(row for row in config["sources"] if row["source_key"] == "TPEX")[
        "history_tickers"
    ] = ["6488"]
    return config


def _transport(url: str, timeout: float) -> HttpResponse:
    assert timeout > 0
    if url.endswith("STOCK_DAY_ALL"):
        payload = [
            {
                "Date": "1150817",
                "Code": "2330",
                "Name": "台積電",
                "TradeVolume": "1000",
                "TradeValue": "2000",
                "OpeningPrice": "10",
                "HighestPrice": "12",
                "LowestPrice": "9",
                "ClosingPrice": "11",
                "Change": "1",
                "Transaction": "50",
            }
        ]
    elif "STOCK_DAY?" in url:
        payload = {
            "stat": "OK",
            "fields": [
                "日期",
                "成交股數",
                "成交金額",
                "開盤價",
                "最高價",
                "最低價",
                "收盤價",
                "漲跌價差",
                "成交筆數",
            ],
            "data": [
                ["115/08/14", "900", "1800", "9", "11", "8", "10", "1", "40"],
                ["115/08/17", "1000", "2000", "10", "12", "9", "11", "1", "50"],
            ],
        }
    elif "afterTrading/tradingStock?" in url:
        payload = {
            "stat": "ok",
            "code": "6488",
            "name": "環球晶",
            "tables": [{
                "data": [
                    ["115/08/14", "3", "300", "98", "101", "97", "100", "2", "60"],
                    ["115/08/17", "4", "350", "100", "102", "99", "101", "1", "70"],
                ]
            }],
        }
    elif url.endswith("tpex_mainboard_daily_close_quotes"):
        payload = [
            {
                "Date": "1150814",
                "SecuritiesCompanyCode": "6488",
                "CompanyName": "環球晶",
                "Close": "100",
                "Change": "2",
                "Open": "98",
                "High": "101",
                "Low": "97",
                "TradingShares": "3500",
                "TransactionAmount": "300000",
                "TransactionNumber": "70",
            },
        ]
    elif url.endswith("t187ap04_L"):
        payload = [
            {
                "出表日期": "1150817",
                "發言日期": "1150817",
                "發言時間": "93001",
                "公司代號": "2330",
                "公司名稱": "台積電",
                "主旨 ": "測試上市重大訊息",
                "符合條款": "第1款",
                "事實發生日": "1150817",
                "說明": "SYNTHETIC_TEST_DATA",
            }
        ]
    elif url.endswith("mopsfin_t187ap04_O"):
        payload = [
            {
                "Date": "1150817",
                "發言日期": "1150817",
                "發言時間": "100002",
                "SecuritiesCompanyCode": "6488",
                "CompanyName": "環球晶",
                "主旨": "測試上櫃重大訊息",
                "符合條款": "第2款",
                "事實發生日": "1150817",
                "說明": "SYNTHETIC_TEST_DATA",
            }
        ]
    else:
        raise AssertionError(url)
    return HttpResponse(200, json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def test_official_sources_share_security_market_data_and_disclosure_schema(database, root):
    result = OfficialDataService(
        database,
        _config(root),
        transport=_transport,
        now=datetime.fromisoformat("2026-08-17T12:00:00+08:00"),
        test_mode=True,
    ).sync_all()

    assert result.status == "PASS"
    assert result.twse_security_count == 1
    assert result.tpex_security_count == 1
    assert result.disclosure_count == result.disclosure_mapped_count == 2

    twse = volume_history(database, "TWSE:2330")
    tpex = volume_history(database, "TPEX:6488")
    assert [row["trade_volume"] for row in twse] == [1000, 900]
    assert [row["trade_volume"] for row in tpex] == [4000, 3000]
    assert set(twse[0]) == set(tpex[0])
    assert twse[0]["exchange_code"] == "TWSE"
    assert tpex[0]["exchange_code"] == "TPEX"

    listed_disclosures = recent_disclosures(database, "TWSE:2330")
    otc_disclosures = recent_disclosures(database, "TPEX:6488")
    assert listed_disclosures[0]["subject"] == "測試上市重大訊息"
    assert otc_disclosures[0]["subject"] == "測試上櫃重大訊息"
    assert all(row["raw_item_id"] for row in listed_disclosures + otc_disclosures)


def test_disclosure_only_sync_skips_daily_market_and_history_endpoints(database, root):
    result = OfficialDataService(
        database,
        _config(root),
        transport=_transport,
        now=datetime.fromisoformat("2026-08-17T12:00:00+08:00"),
        test_mode=True,
    ).sync_disclosures()

    assert result.status == "PASS"
    assert len(result.endpoint_results) == 2
    assert {row.source_key for row in result.endpoint_results} == {"MOPS"}
    assert result.twse_market_data_count == 0
    assert result.tpex_market_data_count == 0
    assert result.disclosure_count == result.disclosure_mapped_count == 2


def test_permissions_preserve_unverified_rights_as_unknown(database, root):
    OfficialDataService(
        database,
        _config(root),
        transport=_transport,
        now=datetime.fromisoformat("2026-08-17T12:00:00+08:00"),
        test_mode=True,
    ).sync_all()
    status = official_data_status(database)
    assert len(status["permissions"]) == 3
    assert {row["technical_status"] for row in status["permissions"]} == {
        "TECHNICALLY_VERIFIED"
    }
    for row in status["permissions"]:
        assert row["internal_use_status"] == "UNKNOWN"
        assert row["public_display_status"] == "UNKNOWN"
        assert row["redistribution_status"] == "UNKNOWN"


def test_second_sync_is_idempotent_and_keeps_raw_evidence_immutable(database, root):
    service = OfficialDataService(
        database,
        _config(root),
        transport=_transport,
        now=datetime.fromisoformat("2026-08-17T12:00:00+08:00"),
        test_mode=True,
    )
    first = service.sync_all()
    raw_before = [
        tuple(row)
        for row in database.execute(
            "SELECT id, original_content, raw_payload_json, content_hash FROM raw_items ORDER BY id"
        )
    ]
    second = service.sync_all()
    raw_after = [
        tuple(row)
        for row in database.execute(
            "SELECT id, original_content, raw_payload_json, content_hash FROM raw_items ORDER BY id"
        )
    ]
    assert first.status == second.status == "PASS"
    assert raw_after == raw_before
    assert database.execute("SELECT COUNT(*) FROM official_market_data_daily").fetchone()[0] == 4
    assert database.execute("SELECT COUNT(*) FROM official_disclosures").fetchone()[0] == 2


def test_collection_fails_closed_when_source_permission_is_not_api_verified(database, root):
    database.execute(
        "UPDATE sources SET collection_status='NEEDS_TECHNICAL_VALIDATION' WHERE source_id='TW-A04'"
    )
    with pytest.raises(ValidationError, match="Automatic collection denied"):
        OfficialDataService(database, _config(root), transport=_transport).sync_all()
    assert database.execute("SELECT COUNT(*) FROM collection_runs").fetchone()[0] == 0
