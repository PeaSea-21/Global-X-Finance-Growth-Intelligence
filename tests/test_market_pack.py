from __future__ import annotations

from global_x_finance.market_pack import load_and_validate_market_pack

from conftest import INPUTS, SCHEMA


def test_tw_and_us_use_the_same_market_pack_loader():
    tw = load_and_validate_market_pack(INPUTS / "taiwan.market-pack.yaml", SCHEMA)
    us = load_and_validate_market_pack(INPUTS / "us.market-pack.template.yaml", SCHEMA)

    assert tw["country_code"] == "TW"
    assert us["country_code"] == "US"
    assert us["status"] == "DRAFT_MISSING_VERIFIED_SOURCES"
    assert us["source_registry_file"] is None
    assert us["official_sources"] == []
    assert us["financial_media"] == []
    assert us["local_kols"] == []


def test_unknown_and_needs_verification_states_are_preserved():
    tw = load_and_validate_market_pack(INPUTS / "taiwan.market-pack.yaml", SCHEMA)
    us = load_and_validate_market_pack(INPUTS / "us.market-pack.template.yaml", SCHEMA)

    assert tw["local_financial_marketing_rules"]["status"] == "UNKNOWN_NEEDS_LEGAL_VERIFICATION"
    assert tw["trending_keywords"]["status"] == "NEEDS_VALIDATION"
    assert us["commercial_topics"]["status"] == "PRODUCT_UNKNOWN"

