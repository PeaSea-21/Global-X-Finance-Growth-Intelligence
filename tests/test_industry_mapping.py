from __future__ import annotations

import sqlite3

import pytest

from global_x_finance.industry_mapping import (
    BEN_NORMALIZED_SECTORS,
    EXCLUDED_ETF_FUND,
    EXCLUDED_NON_COMMON_STOCK,
    MAPPED_COMMON_STOCK,
    UNKNOWN,
    OFFICIAL_INDUSTRY_CLASSIFICATIONS,
    classify_security_industry,
    normalize_industry_code,
)


def test_official_industry_code_table_is_traceable_and_unique():
    keys = set()
    for row in OFFICIAL_INDUSTRY_CLASSIFICATIONS:
        key = (row.exchange_code, row.official_industry_code)
        assert key not in keys
        keys.add(key)
        assert row.official_industry_name
        assert row.source_endpoint.startswith("https://")
        assert row.source_field_code
        assert row.source_field_name
        if row.mapping_status == MAPPED_COMMON_STOCK:
            assert row.normalized_sector != UNKNOWN


def test_twse_and_tpex_payloads_map_to_ben_normalized_sector():
    twse = classify_security_industry(
        "TWSE", {"公司代號": "2330", "公司名稱": "台積電", "產業別": "24"}
    )
    tpex = classify_security_industry(
        "TPEX",
        {
            "SecuritiesCompanyCode": "6488",
            "CompanyName": "環球晶",
            "SecuritiesIndustryCode": "24",
        },
    )
    assert twse.normalized_sector == tpex.normalized_sector == "SEMICONDUCTORS"
    assert twse.official_industry_name == tpex.official_industry_name == "半導體業"
    assert twse.mapping_status == tpex.mapping_status == MAPPED_COMMON_STOCK


def test_unknown_and_excluded_security_types_are_explicit():
    unknown = classify_security_industry("TWSE", {"公司代號": "9999", "產業別": "77"})
    etf = classify_security_industry("TWSE", {"公司代號": "0050", "產業別": "98"})
    dr = classify_security_industry("TPEX", {"SecuritiesCompanyCode": "1234", "SecuritiesIndustryCode": "91"})
    assert unknown.mapping_status == UNKNOWN
    assert unknown.official_industry_name == UNKNOWN
    assert etf.mapping_status == EXCLUDED_ETF_FUND
    assert dr.mapping_status == EXCLUDED_NON_COMMON_STOCK
    assert etf.normalized_sector == dr.normalized_sector == UNKNOWN


def test_industry_code_normalization_and_sector_count_contract():
    assert normalize_industry_code(" 7 ") == "07"
    assert normalize_industry_code("SecuritiesIndustryCode=24") == "24"
    assert normalize_industry_code("") == UNKNOWN
    assert len(BEN_NORMALIZED_SECTORS) == 14


def test_all_official_industry_classifications_stay_in_ben_sector_contract():
    allowed_sectors = BEN_NORMALIZED_SECTORS | {UNKNOWN}
    assert len(BEN_NORMALIZED_SECTORS) == 14
    for row in OFFICIAL_INDUSTRY_CLASSIFICATIONS:
        assert row.normalized_sector in allowed_sectors


def _industry_parent_ids(database):
    market_id = database.execute(
        "SELECT id FROM markets WHERE country_code = 'TW'"
    ).fetchone()[0]
    source_id = database.execute(
        "SELECT id FROM sources WHERE source_id = 'TW-A01'"
    ).fetchone()[0]
    database.execute(
        """
        INSERT INTO collection_runs (
            id, market_id, source_id, started_at, finished_at, status,
            item_count, collector_version
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "run-industry-mapping-contract",
            market_id,
            source_id,
            "2026-01-01T00:00:00+08:00",
            "2026-01-01T00:00:01+08:00",
            "SUCCESS",
            1,
            "test",
        ),
    )
    database.execute(
        """
        INSERT INTO raw_items (
            id, collection_run_id, source_id, original_url, original_content,
            fetched_at, content_hash, mime_type, raw_payload_json, data_label
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "raw-industry-mapping-contract",
            "run-industry-mapping-contract",
            source_id,
            "https://example.test/industry-mapping-contract",
            "{}",
            "2026-01-01T00:00:01+08:00",
            "industry-mapping-contract-hash",
            "application/json",
            "{}",
            "OFFICIAL_TEST_FIXTURE",
        ),
    )
    database.execute(
        """
        INSERT INTO official_securities (
            id, market_id, exchange_code, ticker, company_name, security_type,
            mapping_status, first_source_id, latest_raw_item_id, first_seen_at, last_seen_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "security-industry-mapping-contract",
            market_id,
            "TWSE",
            "2330",
            "台積電",
            "COMMON_STOCK",
            "MAPPED_EXISTING_SECURITY",
            source_id,
            "raw-industry-mapping-contract",
            "2026-01-01T00:00:01+08:00",
            "2026-01-01T00:00:01+08:00",
        ),
    )
    return market_id, source_id, "raw-industry-mapping-contract", "security-industry-mapping-contract"


def _insert_industry_classification(
    database,
    row_id,
    market_id,
    code,
    name,
    sector,
    status,
    scheme="OFFICIAL_INDUSTRY_CODE",
):
    database.execute(
        """
        INSERT INTO industry_classifications (
            id, market_id, exchange_code, scheme, official_industry_code,
            official_industry_name, normalized_sector, mapping_status,
            source_authority, source_endpoint, source_field_code, source_field_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row_id,
            market_id,
            "TWSE",
            scheme,
            code,
            name,
            sector,
            status,
            "TWSE",
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
            "產業別",
            "官方上市公司產業別代碼表",
        ),
    )


def _insert_security_mapping(
    database,
    row_id,
    security_id,
    classification_id,
    source_id,
    raw_item_id,
    code,
    name,
    sector,
    status,
):
    database.execute(
        """
        INSERT INTO security_industry_mappings (
            id, security_id, industry_classification_id, exchange_code, ticker,
            company_name, official_industry_code, official_industry_name,
            normalized_sector, mapping_status, source_id, raw_item_id,
            source_endpoint, source_field_code, source_field_name, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            row_id,
            security_id,
            classification_id,
            "TWSE",
            "2330",
            "台積電",
            code,
            name,
            sector,
            status,
            source_id,
            raw_item_id,
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
            "產業別",
            "官方上市公司產業別代碼表",
            "2026-01-01T00:00:01+08:00",
        ),
    )


def test_industry_mapping_database_constraints(database):
    market_id, source_id, raw_item_id, security_id = _industry_parent_ids(database)
    _insert_industry_classification(
        database,
        "industry-classification-semiconductor",
        market_id,
        "24",
        "半導體業",
        "SEMICONDUCTORS",
        MAPPED_COMMON_STOCK,
    )

    _insert_industry_classification(
        database,
        "industry-classification-semiconductor-alt-scheme",
        market_id,
        "24",
        "半導體業",
        "SEMICONDUCTORS",
        MAPPED_COMMON_STOCK,
        scheme="ALTERNATE_SCHEME",
    )

    with pytest.raises(sqlite3.IntegrityError):
        _insert_industry_classification(
            database,
            "industry-classification-semiconductor-duplicate",
            market_id,
            "24",
            "半導體業",
            "SEMICONDUCTORS",
            MAPPED_COMMON_STOCK,
        )

    with pytest.raises(sqlite3.IntegrityError):
        _insert_security_mapping(
            database,
            "security-industry-invalid-security",
            "missing-security-id",
            "industry-classification-semiconductor",
            source_id,
            raw_item_id,
            "24",
            "半導體業",
            "SEMICONDUCTORS",
            MAPPED_COMMON_STOCK,
        )

    _insert_security_mapping(
        database,
        "security-industry-current",
        security_id,
        "industry-classification-semiconductor",
        source_id,
        raw_item_id,
        "24",
        "半導體業",
        "SEMICONDUCTORS",
        MAPPED_COMMON_STOCK,
    )
    with pytest.raises(sqlite3.IntegrityError):
        _insert_security_mapping(
            database,
            "security-industry-current-duplicate",
            security_id,
            "industry-classification-semiconductor",
            source_id,
            raw_item_id,
            "24",
            "半導體業",
            "SEMICONDUCTORS",
            MAPPED_COMMON_STOCK,
        )


def test_unknown_excluded_and_raw_official_fields_are_preserved(database):
    market_id, source_id, raw_item_id, security_id = _industry_parent_ids(database)
    _insert_industry_classification(
        database,
        "industry-classification-etf",
        market_id,
        "98",
        "ETF",
        UNKNOWN,
        EXCLUDED_ETF_FUND,
    )
    _insert_security_mapping(
        database,
        "security-industry-unknown",
        security_id,
        None,
        source_id,
        raw_item_id,
        "77",
        UNKNOWN,
        UNKNOWN,
        UNKNOWN,
    )
    saved = database.execute(
        """
        SELECT official_industry_code, official_industry_name, normalized_sector, mapping_status
        FROM security_industry_mappings
        WHERE id = 'security-industry-unknown'
        """
    ).fetchone()
    assert tuple(saved) == ("77", UNKNOWN, UNKNOWN, UNKNOWN)

    database.execute("DELETE FROM security_industry_mappings WHERE id = 'security-industry-unknown'")
    _insert_security_mapping(
        database,
        "security-industry-etf",
        security_id,
        "industry-classification-etf",
        source_id,
        raw_item_id,
        "98",
        "ETF",
        UNKNOWN,
        EXCLUDED_ETF_FUND,
    )
    saved = database.execute(
        """
        SELECT official_industry_code, official_industry_name, normalized_sector, mapping_status
        FROM security_industry_mappings
        WHERE id = 'security-industry-etf'
        """
    ).fetchone()
    assert tuple(saved) == ("98", "ETF", UNKNOWN, EXCLUDED_ETF_FUND)
