from __future__ import annotations

import re
from dataclasses import dataclass


UNKNOWN = "UNKNOWN"
MAPPED_COMMON_STOCK = "MAPPED_COMMON_STOCK"
EXCLUDED_ETF_FUND = "EXCLUDED_ETF_FUND"
EXCLUDED_NON_COMMON_STOCK = "EXCLUDED_NON_COMMON_STOCK"

TWSE_COMPANY_ENDPOINT = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_COMPANY_ENDPOINT = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"

TWSE_CODE_FIELD = "產業別"
TWSE_NAME_FIELD = "官方上市公司產業別代碼表"
TPEX_CODE_FIELD = "SecuritiesIndustryCode"
TPEX_NAME_FIELD = "官方上櫃公司產業別代碼表"


@dataclass(frozen=True)
class IndustryClassification:
    exchange_code: str
    official_industry_code: str
    official_industry_name: str
    normalized_sector: str
    mapping_status: str
    source_authority: str
    source_endpoint: str
    source_field_code: str
    source_field_name: str
    notes: str = ""


@dataclass(frozen=True)
class SecurityIndustryMapping:
    exchange_code: str
    ticker: str
    company_name: str
    official_industry_code: str
    official_industry_name: str
    normalized_sector: str
    mapping_status: str
    source_endpoint: str
    source_field_code: str
    source_field_name: str
    notes: str = ""


# Official names are from TWSE/TPEx official industry-code tables used with
# t187ap03_L / mopsfin_t187ap03_O company-profile payloads. Unknown or excluded
# rows are preserved explicitly and are not inferred by model text.
OFFICIAL_INDUSTRY_CLASSIFICATIONS: tuple[IndustryClassification, ...] = (
    IndustryClassification("TWSE", "01", "水泥工業", "MATERIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "02", "食品工業", "CONSUMER_STAPLES", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "03", "塑膠工業", "MATERIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "04", "紡織纖維", "CONSUMER_DISCRETIONARY", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "05", "電機機械", "INDUSTRIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "06", "電器電纜", "INDUSTRIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "07", "化學生技醫療", "HEALTHCARE", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "08", "玻璃陶瓷", "MATERIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "09", "造紙工業", "MATERIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "10", "鋼鐵工業", "MATERIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "11", "橡膠工業", "MATERIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "12", "汽車工業", "CONSUMER_DISCRETIONARY", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "14", "建材營造", "REAL_ESTATE", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "15", "航運業", "INDUSTRIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "16", "觀光事業", "CONSUMER_DISCRETIONARY", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "17", "金融保險", "FINANCIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "18", "貿易百貨", "CONSUMER_DISCRETIONARY", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "20", "其他", "OTHER", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "21", "化學工業", "MATERIALS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "22", "生技醫療業", "HEALTHCARE", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "23", "油電燃氣業", "UTILITIES", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "24", "半導體業", "SEMICONDUCTORS", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "25", "電腦及週邊設備業", "TECH_HARDWARE", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "26", "光電業", "TECH_HARDWARE", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "27", "通信網路業", "COMMUNICATION_SERVICES", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "28", "電子零組件業", "TECH_HARDWARE", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "29", "電子通路業", "TECH_DISTRIBUTION", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "30", "資訊服務業", "SOFTWARE_SERVICES", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "31", "其他電子業", "TECH_HARDWARE", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "32", "文化創意業", "COMMUNICATION_SERVICES", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "33", "農業科技", "CONSUMER_STAPLES", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "34", "電子商務", "CONSUMER_DISCRETIONARY", MAPPED_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "80", "管理股票", UNKNOWN, EXCLUDED_NON_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "91", "存託憑證", UNKNOWN, EXCLUDED_NON_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "97", "受益證券", UNKNOWN, EXCLUDED_NON_COMMON_STOCK, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "98", "ETF", UNKNOWN, EXCLUDED_ETF_FUND, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
    IndustryClassification("TWSE", "99", "其他", UNKNOWN, UNKNOWN, "TWSE", TWSE_COMPANY_ENDPOINT, TWSE_CODE_FIELD, TWSE_NAME_FIELD),
)

_SHARED_TPEX_CODES = tuple(
    IndustryClassification("TPEX", row.official_industry_code, row.official_industry_name, row.normalized_sector, row.mapping_status, "TPEx", TPEX_COMPANY_ENDPOINT, TPEX_CODE_FIELD, TPEX_NAME_FIELD, row.notes)
    for row in OFFICIAL_INDUSTRY_CLASSIFICATIONS
    if row.exchange_code == "TWSE" and row.official_industry_code not in {"80", "91", "97", "98", "99"}
)

OFFICIAL_INDUSTRY_CLASSIFICATIONS = OFFICIAL_INDUSTRY_CLASSIFICATIONS + _SHARED_TPEX_CODES + (
    IndustryClassification("TPEX", "80", "管理股票", UNKNOWN, EXCLUDED_NON_COMMON_STOCK, "TPEx", TPEX_COMPANY_ENDPOINT, TPEX_CODE_FIELD, TPEX_NAME_FIELD),
    IndustryClassification("TPEX", "91", "存託憑證", UNKNOWN, EXCLUDED_NON_COMMON_STOCK, "TPEx", TPEX_COMPANY_ENDPOINT, TPEX_CODE_FIELD, TPEX_NAME_FIELD),
    IndustryClassification("TPEX", "97", "受益證券", UNKNOWN, EXCLUDED_NON_COMMON_STOCK, "TPEx", TPEX_COMPANY_ENDPOINT, TPEX_CODE_FIELD, TPEX_NAME_FIELD),
    IndustryClassification("TPEX", "98", "ETF", UNKNOWN, EXCLUDED_ETF_FUND, "TPEx", TPEX_COMPANY_ENDPOINT, TPEX_CODE_FIELD, TPEX_NAME_FIELD),
    IndustryClassification("TPEX", "99", "其他", UNKNOWN, UNKNOWN, "TPEx", TPEX_COMPANY_ENDPOINT, TPEX_CODE_FIELD, TPEX_NAME_FIELD),
)

_CLASSIFICATIONS = {
    (row.exchange_code, row.official_industry_code): row
    for row in OFFICIAL_INDUSTRY_CLASSIFICATIONS
}
BEN_NORMALIZED_SECTORS = frozenset(
    row.normalized_sector
    for row in OFFICIAL_INDUSTRY_CLASSIFICATIONS
    if row.mapping_status == MAPPED_COMMON_STOCK and row.normalized_sector != UNKNOWN
)


def normalize_industry_code(value: object) -> str:
    cleaned = str(value or "").strip()
    digits = re.sub(r"\D", "", cleaned)
    if not digits:
        return UNKNOWN
    return digits.zfill(2)[-2:]


def classify_security_industry(exchange_code: str, payload: dict) -> SecurityIndustryMapping:
    exchange = exchange_code.upper()
    if exchange == "TWSE":
        ticker = str(payload.get("公司代號") or "").strip()
        company_name = str(payload.get("公司名稱") or payload.get("公司簡稱") or "").strip() or UNKNOWN
        code = normalize_industry_code(payload.get("產業別"))
        endpoint = TWSE_COMPANY_ENDPOINT
        code_field = TWSE_CODE_FIELD
        name_field = TWSE_NAME_FIELD
    elif exchange == "TPEX":
        ticker = str(payload.get("SecuritiesCompanyCode") or "").strip()
        company_name = str(payload.get("CompanyName") or payload.get("CompanyAbbreviation") or "").strip() or UNKNOWN
        code = normalize_industry_code(payload.get("SecuritiesIndustryCode"))
        endpoint = TPEX_COMPANY_ENDPOINT
        code_field = TPEX_CODE_FIELD
        name_field = TPEX_NAME_FIELD
    else:
        raise ValueError(f"Unsupported exchange_code: {exchange_code}")

    classification = _CLASSIFICATIONS.get((exchange, code))
    if classification is None:
        return SecurityIndustryMapping(
            exchange,
            ticker or UNKNOWN,
            company_name,
            code,
            UNKNOWN,
            UNKNOWN,
            UNKNOWN,
            endpoint,
            code_field,
            name_field,
            "Official industry code was preserved but is not present in the audited code table.",
        )
    return SecurityIndustryMapping(
        exchange,
        ticker or UNKNOWN,
        company_name,
        classification.official_industry_code,
        classification.official_industry_name,
        classification.normalized_sector,
        classification.mapping_status,
        classification.source_endpoint,
        classification.source_field_code,
        classification.source_field_name,
        classification.notes,
    )
