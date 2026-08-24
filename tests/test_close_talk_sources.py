from global_x_finance.close_talk_sources import (
    _parse_twse_indices_rwd,
    _parse_tpex_institutional,
    _parse_twse_institutional,
    _parse_twse_margin,
    collect_close_talk_source_pack,
    market_breadth,
)


def test_market_breadth_keeps_missing_change_separate(database):
    market = database.execute("SELECT id FROM markets WHERE country_code='TW'").fetchone()["id"]
    source = database.execute("SELECT id FROM sources WHERE source_id='TW-A02'").fetchone()["id"]
    for index, change in enumerate(("1.5", "-0.5", "0", None), start=1):
        security_id = f"TWSE:10{index:02d}"
        raw_id = f"raw-{index}"
        database.execute(
            """INSERT INTO raw_items
               (id, source_id, original_url, original_content, fetched_at,
                content_hash, mime_type, raw_payload_json, data_label)
               VALUES (?, ?, ?, ?, ?, ?, 'application/json', '{}', 'SYNTHETIC_TEST_DATA')""",
            (raw_id, source, f"https://example.test/{raw_id}", raw_id,
             "2026-08-20", f"hash-{raw_id}"),
        )
        database.execute(
            """INSERT INTO official_securities
               (id, market_id, exchange_code, ticker, company_name, mapping_status,
                first_source_id, first_seen_at, last_seen_at)
               VALUES (?, ?, 'TWSE', ?, ?, 'OFFICIAL_MARKET_DATA', ?, ?, ?)""",
            (security_id, market, f"10{index:02d}", f"公司{index}", source, "2026-08-20", "2026-08-20"),
        )
        database.execute(
            """INSERT INTO official_market_data_daily
               (id, security_id, market_id, exchange_code, ticker, trade_date,
                closing_price, price_change, trade_value, data_status, source_id,
                raw_item_id, collected_at)
               VALUES (?, ?, ?, 'TWSE', ?, '2026-08-20', '100', ?, 1000,
                       'EOD', ?, ?, ?)""",
            (f"md-{index}", security_id, market, f"10{index:02d}", change, source, raw_id, "2026-08-20"),
        )
    tpex_source = database.execute("SELECT id FROM sources WHERE source_id='TW-A04'").fetchone()["id"]
    database.execute(
        """INSERT INTO raw_items
           (id, source_id, original_url, original_content, fetched_at,
            content_hash, mime_type, raw_payload_json, data_label)
           VALUES ('raw-tpex', ?, 'https://example.test/raw-tpex', 'raw-tpex', ?,
                   'hash-raw-tpex', 'application/json', '{}', 'SYNTHETIC_TEST_DATA')""",
        (tpex_source, "2026-08-20"),
    )
    database.execute(
        """INSERT INTO official_securities
           (id, market_id, exchange_code, ticker, company_name, mapping_status,
            first_source_id, first_seen_at, last_seen_at)
           VALUES ('TPEX:2001', ?, 'TPEX', '2001', '上櫃公司', 'OFFICIAL_MARKET_DATA', ?, ?, ?)""",
        (market, tpex_source, "2026-08-20", "2026-08-20"),
    )
    database.execute(
        """INSERT INTO official_market_data_daily
           (id, security_id, market_id, exchange_code, ticker, trade_date,
            closing_price, price_change, trade_value, data_status, source_id,
            raw_item_id, collected_at)
           VALUES ('md-tpex', 'TPEX:2001', ?, 'TPEX', '2001', '2026-08-20',
                   '50', '2', 2000, 'EOD', ?, 'raw-tpex', ?)""",
        (market, tpex_source, "2026-08-20"),
    )

    result = market_breadth(database, "2026-08-20")

    assert result["TWSE"] == {
        "advances": 1, "declines": 1, "unchanged": 1, "unknown_change": 1,
        "observed_securities": 4, "covered_security_trade_value": 4000,
        "trade_value_scope": "SUM_OF_STORED_EOD_SECURITY_ROWS_NOT_FULL_MARKET_TURNOVER",
    }
    assert result["TPEX"]["advances"] == 1


def test_official_parsers_require_exact_trade_date_and_expose_flows():
    twse = _parse_twse_institutional({
        "stat": "OK", "date": "20260820",
        "data": [
            ["投信", "0", "0", "-2,000"],
            ["外資及陸資(不含外資自營商)", "0", "0", "7,000"],
            ["合計", "0", "0", "5,000"],
        ],
    }, "2026-08-20")
    tpex = _parse_tpex_institutional([
        {"Date": "1150820", "Investor": "外資及陸資合計", "Net": "-3000"},
        {"Date": "1150820", "Investor": "三大法人合計*", "Net": "-4000"},
    ], "2026-08-20")

    assert twse["foreign_net"] == 7000
    assert twse["investment_trust_net"] == -2000
    assert tpex["foreign_net"] == -3000
    assert tpex["total_net"] == -4000


def test_twse_margin_summary_keeps_previous_and_current_balances():
    result = _parse_twse_margin({
        "stat": "OK", "date": "20260820", "tables": [{"data": [
            ["融資(交易單位)", "1", "2", "3", "100", "110"],
            ["融券(交易單位)", "1", "2", "3", "20", "25"],
            ["融資金額(仟元)", "1", "2", "3", "5000", "5200"],
        ]}],
    }, "2026-08-20")

    assert result["margin_balance_units_current"] == 110
    assert result["short_balance_units_current"] == 25
    assert result["margin_value_thousand_twd_current"] == 5200


def test_twse_dated_fallback_parser_reads_same_day_sector_rows():
    result = _parse_twse_indices_rwd({
        "date": "20260820",
        "tables": [{
            "fields": ["指數", "收盤指數", "漲跌(+/-)", "漲跌點數", "漲跌百分比(%)", "特殊處理註記"],
            "data": [
                ["發行量加權股價指數", "45000", "<p>+</p>", "200", "0.45", ""],
                ["半導體類指數", "1500", "<p>+</p>", "30", "2.04", ""],
                ["電腦及週邊設備類指數", "400", "<p>-</p>", "10", "-2.44", ""],
            ],
        }],
    }, "2026-08-20")

    assert result["weighted_index"]["close"] == 45000
    assert result["top_sectors"][0]["name"] == "半導體類指數"
    assert result["bottom_sectors"][0]["name"] == "電腦及週邊設備類指數"


def test_optional_late_sources_do_not_block_base_source_pack(database):
    market_id = database.execute("SELECT id FROM markets WHERE country_code='TW'").fetchone()["id"]
    source_id = database.execute("SELECT id FROM sources WHERE source_id='TW-A02'").fetchone()["id"]
    tpex_source_id = database.execute("SELECT id FROM sources WHERE source_id='TW-A04'").fetchone()["id"]
    for exchange, security_id, ticker, source in (
        ("TWSE", "TWSE:2330", "2330", source_id),
        ("TPEX", "TPEX:6488", "6488", tpex_source_id),
    ):
        database.execute(
            """INSERT INTO raw_items
               (id, source_id, original_url, original_content, fetched_at,
                content_hash, mime_type, raw_payload_json, data_label)
               VALUES (?, ?, ?, ?, ?, ?, 'application/json', '{}', 'SYNTHETIC_TEST_DATA')""",
            (f"raw-{security_id}", source, f"https://example.test/{security_id}", security_id,
             "2026-08-20", f"hash-{security_id}"),
        )
        database.execute(
            """INSERT INTO official_securities
               (id, market_id, exchange_code, ticker, company_name, mapping_status,
                first_source_id, first_seen_at, last_seen_at)
               VALUES (?, ?, ?, ?, ?, 'OFFICIAL_MARKET_DATA', ?, ?, ?)""",
            (security_id, market_id, exchange, ticker, ticker, source, "2026-08-20", "2026-08-20"),
        )
        database.execute(
            """INSERT INTO official_market_data_daily
               (id, security_id, market_id, exchange_code, ticker, trade_date,
                closing_price, price_change, trade_value, data_status, source_id,
                raw_item_id, collected_at)
               VALUES (?, ?, ?, ?, ?, '2026-08-20', '100', '1', 1000,
                       'EOD', ?, ?, ?)""",
            (f"md-{security_id}", security_id, market_id, exchange, ticker, source,
             f"raw-{security_id}", "2026-08-20"),
        )
    database.commit()

    def fetcher(url, timeout):
        if "openapi.twse.com.tw" in url:
            return [{"日期": "1150819", "指數": "發行量加權股價指數", "收盤指數": "1", "漲跌點數": "0", "漲跌百分比": "0"}]
        if "afterTrading/MI_INDEX" in url:
            return {"date": "20260820", "tables": [{
                "fields": ["指數", "收盤指數", "漲跌(+/-)", "漲跌點數", "漲跌百分比(%)"],
                "data": [["發行量加權股價指數", "45000", "<p>+</p>", "200", "0.45"]],
            }]}
        return []

    pack = collect_close_talk_source_pack(database, "2026-08-20", fetcher=fetcher)
    assert pack["status"] == "READY"
    assert pack["base_status"] == "READY"
    assert pack["generation_stage"] == "BASE_DRAFT_ALLOWED"
    twse = next(row for row in pack["datasets"] if row["dataset_id"] == "TWSE_INDEX_AND_SECTORS")
    assert twse["source_endpoint_role"] == "same_day_fallback"
    tpex = next(row for row in pack["datasets"] if row["dataset_id"] == "TPEX_INDEX")
    assert tpex["status"] in {"SOURCE_PENDING", "FAILED"}
