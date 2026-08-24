from __future__ import annotations

import json

from global_x_finance.industry_mapping_sync import HttpResponse, IndustryMappingSyncService


def _insert_security(database, *, security_id: str, exchange: str, ticker: str, name: str, source_key: str):
    market_id = database.execute(
        "SELECT id FROM markets WHERE country_code='TW'"
    ).fetchone()[0]
    source_id = database.execute(
        "SELECT id FROM sources WHERE source_id=?", (source_key,)
    ).fetchone()[0]
    database.execute(
        """
        INSERT INTO official_securities (
            id, market_id, exchange_code, ticker, company_name, security_type,
            mapping_status, first_source_id, first_seen_at, last_seen_at
        ) VALUES (?, ?, ?, ?, ?, 'COMMON_STOCK', 'MAPPED_EXISTING_SECURITY', ?, ?, ?)
        """,
        (
            security_id, market_id, exchange, ticker, name, source_id,
            "2026-08-17T15:00:00+08:00", "2026-08-17T15:00:00+08:00",
        ),
    )


def test_official_industry_sync_persists_record_evidence_and_is_idempotent(database):
    _insert_security(
        database, security_id="TWSE:2330", exchange="TWSE", ticker="2330",
        name="台积电", source_key="TW-A02",
    )
    _insert_security(
        database, security_id="TPEX:6488", exchange="TPEX", ticker="6488",
        name="环球晶", source_key="TW-A04",
    )
    database.commit()

    def transport(url, _timeout):
        if "twse" in url:
            payload = [{"公司代號": "2330", "公司名稱": "台积电", "產業別": "24", "出表日期": "1150817"}]
        else:
            payload = [{
                "SecuritiesCompanyCode": "6488", "CompanyName": "环球晶",
                "SecuritiesIndustryCode": "24", "Date": "1150817",
            }]
        return HttpResponse(200, json.dumps(payload, ensure_ascii=False).encode(), "application/json")

    service = IndustryMappingSyncService(database, transport=transport, test_mode=True)
    first = service.sync()
    assert first.status == "SUCCESS"
    assert sum(row.mapped_count for row in first.endpoints) == 2
    saved = database.execute(
        """SELECT security_id, normalized_sector, mapping_status
           FROM security_industry_mappings ORDER BY security_id"""
    ).fetchall()
    assert [tuple(row) for row in saved] == [
        ("TPEX:6488", "SEMICONDUCTORS", "MAPPED_COMMON_STOCK"),
        ("TWSE:2330", "SEMICONDUCTORS", "MAPPED_COMMON_STOCK"),
    ]
    assert database.execute(
        "SELECT COUNT(*) FROM raw_items WHERE data_label='SYNTHETIC_TEST_DATA'"
    ).fetchone()[0] == 2

    second = service.sync()
    assert second.status == "SUCCESS"
    assert sum(row.new_evidence_count for row in second.endpoints) == 0
    assert sum(row.duplicate_evidence_count for row in second.endpoints) == 2
    assert database.execute(
        "SELECT COUNT(*) FROM raw_items WHERE data_label='SYNTHETIC_TEST_DATA'"
    ).fetchone()[0] == 2
