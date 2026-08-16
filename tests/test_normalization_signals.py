from __future__ import annotations

import json

from global_x_finance.normalization import (
    SIGNAL_LABEL,
    TwseNormalizationService,
    freshness_status,
)
from global_x_finance.twse_collector import (
    HttpResponse,
    TwseOpenApiCollector,
    load_twse_config,
)
from global_x_finance.webapp import create_app


def _synthetic_transport(url: str, timeout: float) -> HttpResponse:
    assert timeout > 0
    if url.endswith("STOCK_DAY_ALL"):
        records = []
        for number in range(1, 31):
            record = {
                "Date": "1150813",
                "Code": f"SYNTHETIC_TEST_DATA_{number:04d}",
                "Name": f"SYNTHETIC_TEST_DATA_COMPANY_{number:04d}",
                "TradeVolume": str(1000 + number),
                "TradeValue": str(10000 + number),
                "OpeningPrice": f"{99 + number}.00",
                "HighestPrice": f"{102 + number}.00",
                "LowestPrice": f"{98 + number}.00",
                "ClosingPrice": f"{100 + number}.00",
                "Change": f"{number}.0000",
                "Transaction": str(100 + number),
            }
            if number == 1:
                record.pop("HighestPrice")
            records.append(record)
    elif url.endswith("MI_INDEX"):
        records = [
            {
                "日期": "1150813",
                "指數": "SYNTHETIC_TEST_DATA_INDEX",
                "收盤指數": "12345.67",
                "漲跌點數": "12.34",
            }
        ]
    else:
        records = [
            {
                "IndustryCat": "SYNTHETIC_TEST_DATA_INDUSTRY",
                "Numbers": "3",
                "ShareNumber": "1000",
                "ForeignMainlandAreaShare": "250",
                "Percentage": "25.00",
            }
        ]
    return HttpResponse(200, json.dumps(records, ensure_ascii=False).encode("utf-8"))


def _populate(database, root):
    config = load_twse_config(root / "config" / "twse_openapi.datasets.json")
    batch = TwseOpenApiCollector(
        database, config, transport=_synthetic_transport, test_mode=True
    ).collect_all()
    assert batch.status == "SUCCESS"
    result = TwseNormalizationService(database, config).normalize_all()
    return config, result


def test_twse_normalization_is_exact_traceable_and_unknown_safe(database, root):
    _, result = _populate(database, root)

    assert result.normalized_new_count == 32
    assert result.total_normalized_count == 32
    stock = database.execute(
        """
        SELECT ni.*, m.country_code, ri.raw_payload_json, ri.fetched_at
        FROM normalized_items ni
        JOIN markets m ON m.id = ni.market_id
        JOIN raw_items ri ON ri.id = ni.raw_item_id
        WHERE ni.stock_code = 'SYNTHETIC_TEST_DATA_0030'
        """
    ).fetchone()
    raw = json.loads(stock["raw_payload_json"])
    assert stock["country_code"] == "TW"
    assert stock["company_name"] == "SYNTHETIC_TEST_DATA_COMPANY_0030"
    assert stock["data_date"] == "2026-08-13"
    assert stock["normalized_published_at"] == "2026-08-13T00:00:00+08:00"
    assert stock["opening_price"] == raw["OpeningPrice"] == "129.00"
    assert stock["highest_price"] == raw["HighestPrice"] == "132.00"
    assert stock["lowest_price"] == raw["LowestPrice"] == "128.00"
    assert stock["closing_price"] == raw["ClosingPrice"] == "130.00"
    assert stock["trade_volume"] == raw["TradeVolume"] == "1030"
    assert stock["trade_value"] == raw["TradeValue"] == "10030"
    assert stock["price_change"] == raw["Change"] == "30.0000"
    assert stock["fetched_at"] != stock["normalized_published_at"]

    missing = database.execute(
        """
        SELECT highest_price FROM normalized_items
        WHERE stock_code = 'SYNTHETIC_TEST_DATA_0001'
        """
    ).fetchone()
    assert missing["highest_price"] == "UNKNOWN"

    foreign = database.execute(
        """
        SELECT data_date, normalized_published_at, foreign_holding_percentage
        FROM normalized_items WHERE record_type = 'FOREIGN_HOLDING_BY_INDUSTRY'
        """
    ).fetchone()
    assert foreign["data_date"] == "UNKNOWN"
    assert foreign["normalized_published_at"] is None
    assert foreign["foreign_holding_percentage"] == "25.00"

    entity = database.execute(
        """
        SELECT e.*, ie.confidence, ie.relation_type
        FROM entities e JOIN item_entities ie ON ie.entity_id = e.id
        JOIN normalized_items ni ON ni.id = ie.item_id
        WHERE ni.stock_code = 'SYNTHETIC_TEST_DATA_0030'
        """
    ).fetchone()
    assert entity["entity_key"] == "TW:LISTED_SECURITY:SYNTHETIC_TEST_DATA_0030"
    assert entity["canonical_name"] == "SYNTHETIC_TEST_DATA_COMPANY_0030"
    assert entity["relation_type"] == "ABOUT_SECURITY"
    assert entity["confidence"] == 1.0


def test_signal_cards_are_rule_based_traceable_and_idempotent(database, root):
    config, first = _populate(database, root)
    before_raw = [
        tuple(row)
        for row in database.execute(
            "SELECT id, original_content, raw_payload_json, content_hash FROM raw_items ORDER BY id"
        )
    ]
    second = TwseNormalizationService(database, config).normalize_all()
    after_raw = [
        tuple(row)
        for row in database.execute(
            "SELECT id, original_content, raw_payload_json, content_hash FROM raw_items ORDER BY id"
        )
    ]

    assert first.signal_new_count == 31
    assert first.total_signal_count == 31
    assert second.normalized_new_count == 0
    assert second.normalized_existing_count == 32
    assert second.signal_new_count == 0
    assert second.signal_existing_count == 31
    assert second.total_signal_count == 31
    assert after_raw == before_raw

    labels = database.execute(
        "SELECT DISTINCT signal_label FROM official_signal_cards"
    ).fetchall()
    assert [row[0] for row in labels] == [SIGNAL_LABEL]
    types = {
        row[0]
        for row in database.execute("SELECT DISTINCT signal_type FROM official_signal_cards")
    }
    assert types == {
        "HIGH_TRADE_VOLUME",
        "HIGH_TRADE_VALUE",
        "NOTABLE_DAILY_CHANGE",
        "FOREIGN_HOLDING_RATIO",
    }
    card = database.execute(
        """
        SELECT sc.*, ni.raw_item_id
        FROM official_signal_cards sc
        JOIN normalized_items ni ON ni.id = sc.normalized_item_id
        WHERE ni.stock_code = 'SYNTHETIC_TEST_DATA_0030'
          AND sc.signal_type = 'NOTABLE_DAILY_CHANGE'
        """
    ).fetchone()
    assert card["evidence_raw_item_id"] == card["raw_item_id"]
    assert card["official_url"].startswith("https://openapi.twse.com.tw/v1/")
    assert card["formula_version"] == "ABS_DAILY_CHANGE_RATE_RANK_TOP10_V1"
    assert "Change=30.0000" in card["calculation_basis"]
    assert card["freshness_status"] == "OFFICIAL_LATEST_AVAILABLE_DATA"


def test_freshness_status_uses_builtin_taiwan_offset_without_tzdata() -> None:
    assert freshness_status("UNKNOWN") == "UNKNOWN_DATA_DATE"


def test_signal_page_filters_searches_and_paginates(database, database_path, root):
    _populate(database, root)
    app = create_app(database_path, root / "config" / "twse_openapi.datasets.json")
    app.testing = True
    client = app.test_client()

    page_one = client.get("/signals").get_data(as_text=True)
    assert "RULE_BASED_OFFICIAL_SIGNAL" in page_one
    assert "共 31 張規則卡" in page_one
    assert "下一頁" in page_one
    assert "查看原始 Evidence" in page_one
    assert "開啟官方 URL" in page_one

    page_two = client.get("/signals?page=2").get_data(as_text=True)
    assert "第 2 / 2 頁" in page_two
    search = client.get(
        "/signals?stock_code=SYNTHETIC_TEST_DATA_0030"
    ).get_data(as_text=True)
    assert "SYNTHETIC_TEST_DATA_COMPANY_0030" in search
    assert "共 3 張規則卡" in search
    assert "SYNTHETIC_TEST_DATA_INDUSTRY" not in search

    dated = client.get("/signals?date=2026-08-13").get_data(as_text=True)
    assert "共 30 張規則卡" in dated
    unknown_date = client.get("/signals?date=UNKNOWN").get_data(as_text=True)
    assert "共 1 張規則卡" in unknown_date
    assert "官方未提供資料日期" in unknown_date

    dashboard = client.get("/").get_data(as_text=True)
    assert "官方最新可用資料：2026-08-13" in dashboard
    assert "兩小時即時熱點" in dashboard
    assert "標準化記錄" in dashboard
