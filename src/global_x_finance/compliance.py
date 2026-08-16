from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


PRECHECK_RESULTS = {"PASS_PRECHECK", "REVIEW_REQUIRED", "BLOCKED", "UNKNOWN"}
PRODUCT_CATEGORIES = {"FINANCIAL_SERVICES", "CRYPTO"}
UNKNOWN_VALUES = {None, "", "UNKNOWN", "NEEDS_VERIFICATION"}
PROHIBITED_CLAIM_PATTERNS = (
    "保证翻倍",
    "保證翻倍",
    "保证盈利",
    "保證盈利",
    "稳赚",
    "穩賺",
    "固定时间致富",
    "固定時間致富",
    "快速致富",
    "guaranteed profit",
    "guaranteed return",
    "get rich quick",
)


@dataclass(frozen=True)
class PrecheckOutcome:
    result: str
    missing_fields: tuple[str, ...]
    reasons: tuple[str, ...]
    policy_snapshot_date: str
    disclaimer: str = (
        "PASS_PRECHECK仅代表内部预检查通过，不代表X批准，也不构成台湾或美国法律意见。"
    )


def _is_unknown(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().upper() in {"", "UNKNOWN", "NEEDS_VERIFICATION"}
    return value is None


def _as_bool(value: Any) -> bool | None:
    if value is True or (isinstance(value, str) and value.strip().upper() in {"YES", "TRUE", "PASS", "VALID", "ACCESSIBLE"}):
        return True
    if value is False or (isinstance(value, str) and value.strip().upper() in {"NO", "FALSE", "FAIL", "INVALID", "INACCESSIBLE"}):
        return False
    return None


def _policy_evidence_state(connection: sqlite3.Connection) -> tuple[int, str]:
    row = connection.execute(
        """
        SELECT COUNT(*) AS source_count, MIN(latest_fetched) AS oldest_current_fetch
        FROM (
            SELECT COALESCE(source_url, policy_url) AS source_url,
                   MAX(fetched_at) AS latest_fetched
            FROM policy_snapshots
            WHERE verification_status = 'VERIFIED_OFFICIAL_HTTP_200'
            GROUP BY COALESCE(source_url, policy_url)
        )
        """
    ).fetchone()
    fetched = row["oldest_current_fetch"] if row else None
    return int(row["source_count"] if row else 0), (fetched[:10] if fetched else "UNKNOWN")


def run_financial_ads_precheck(
    connection: sqlite3.Connection,
    facts: dict[str, Any],
    *,
    today: date | None = None,
    max_policy_age_days: int = 30,
) -> PrecheckOutcome:
    source_count, snapshot_date = _policy_evidence_state(connection)
    if source_count == 0:
        return PrecheckOutcome(
            "UNKNOWN", (), ("没有已核验的X官方政策快照。",), "UNKNOWN"
        )
    if source_count < 6:
        return PrecheckOutcome(
            "UNKNOWN",
            (),
            (f"X官方政策快照不完整：当前仅覆盖{source_count}/6个必需页面。",),
            snapshot_date,
        )

    ad_text = str(facts.get("ad_text", "")).casefold()
    claims_flag = _as_bool(facts.get("prohibited_claims_detected"))
    if claims_flag is True or any(pattern.casefold() in ad_text for pattern in PROHIBITED_CLAIM_PATTERNS):
        return PrecheckOutcome(
            "BLOCKED", (), ("检测到保证盈利、快速致富或不现实结果承诺。",), snapshot_date
        )
    if _as_bool(facts.get("review_evasion_detected")) is True:
        return PrecheckOutcome(
            "BLOCKED", (), ("检测到伪装页面、URL修改或其他规避审核迹象。",), snapshot_date
        )
    if _as_bool(facts.get("landing_page_accessible")) is False:
        return PrecheckOutcome(
            "BLOCKED", (), ("落地页不可访问。",), snapshot_date
        )
    if _as_bool(facts.get("landing_page_matches_ad")) is False:
        return PrecheckOutcome(
            "BLOCKED", (), ("落地页与广告内容不一致。",), snapshot_date
        )

    category = str(facts.get("product_category", "UNKNOWN")).upper()
    if category not in PRODUCT_CATEGORIES:
        return PrecheckOutcome(
            "UNKNOWN", ("product_category",), ("产品类别未知或不在本框架范围。",), snapshot_date
        )

    critical_text_fields = (
        "advertiser_legal_name",
        "advertiser_country",
        "target_country",
        "product_name",
        "landing_page",
    )
    missing = [field for field in critical_text_fields if _is_unknown(facts.get(field))]
    if missing:
        return PrecheckOutcome(
            "UNKNOWN", tuple(missing), ("广告主体、目标国家、产品或落地页资料不完整。",), snapshot_date
        )

    country = str(facts["target_country"]).upper()
    if country not in {"TW", "US"}:
        return PrecheckOutcome(
            "UNKNOWN", ("target_country",), ("本版本只覆盖台湾与美国。",), snapshot_date
        )

    license_status = str(facts.get("financial_license_status", "UNKNOWN")).upper()
    if license_status in {"UNKNOWN", "NEEDS_VERIFICATION", ""}:
        return PrecheckOutcome(
            "UNKNOWN",
            ("financial_license_status",),
            ("金融牌照状态未知，不得通过预检查。",),
            snapshot_date,
        )
    if license_status in {"NOT_LICENSED", "NONE", "NO"}:
        if country == "TW" or category == "CRYPTO":
            return PrecheckOutcome(
                "BLOCKED", (), ("该目标国家/产品类别的X政策要求牌照或注册证明，但广告主明确未持有。",), snapshot_date
            )
        return PrecheckOutcome(
            "REVIEW_REQUIRED", (), ("广告主明确无牌照；美国金融产品适用范围须人工法遵确认。",), snapshot_date
        )
    if license_status != "PROVIDED":
        return PrecheckOutcome(
            "UNKNOWN", ("financial_license_status",), ("无法识别金融牌照状态。",), snapshot_date
        )
    license_missing = [
        field for field in ("license_authority", "license_number") if _is_unknown(facts.get(field))
    ]
    if license_missing:
        return PrecheckOutcome(
            "UNKNOWN", tuple(license_missing), ("已称持牌但牌照机关或编号缺失。",), snapshot_date
        )

    preauth = str(facts.get("X_pre_authorization_status", "UNKNOWN")).upper()
    if preauth in {"UNKNOWN", "NEEDS_VERIFICATION", ""}:
        return PrecheckOutcome(
            "UNKNOWN", ("X_pre_authorization_status",), ("X预授权/认证状态未知。",), snapshot_date
        )
    if preauth != "APPROVED":
        return PrecheckOutcome(
            "BLOCKED", (), ("尚未取得对应金融或加密类别的X预授权/认证。",), snapshot_date
        )

    eligibility = _as_bool(facts.get("X_ads_account_eligible"))
    verified = _as_bool(facts.get("X_account_verified"))
    bio_valid = _as_bool(facts.get("bio_url_valid"))
    fees_disclosed = _as_bool(facts.get("fees_disclosed"))
    risk_disclosure = _as_bool(facts.get("risk_disclosure"))
    landing_accessible = _as_bool(facts.get("landing_page_accessible"))
    landing_matches = _as_bool(facts.get("landing_page_matches_ad"))
    boolean_values = {
        "X_ads_account_eligible": eligibility,
        "X_account_verified": verified,
        "bio_url_valid": bio_valid,
        "fees_disclosed": fees_disclosed,
        "risk_disclosure": risk_disclosure,
        "landing_page_accessible": landing_accessible,
        "landing_page_matches_ad": landing_matches,
        "prohibited_claims_detected": claims_flag,
    }
    boolean_missing = [field for field, value in boolean_values.items() if value is None]
    if boolean_missing:
        return PrecheckOutcome(
            "UNKNOWN", tuple(boolean_missing), ("账号、披露、落地页或禁止主张检查尚未完成。",), snapshot_date
        )
    if eligibility is False:
        return PrecheckOutcome("BLOCKED", (), ("X广告账号当前不具备投放资格。",), snapshot_date)
    review_reasons: list[str] = []
    if verified is False:
        review_reasons.append("X账号未按账号类型完成验证。")
    if bio_valid is False:
        review_reasons.append("Bio URL无效、受门控或未准确代表品牌/推广产品。")
    if fees_disclosed is False:
        review_reasons.append("费用或重要付款条件未完整披露。")
    if risk_disclosure is False:
        review_reasons.append("适用风险披露或强制警示尚未确认。")

    if snapshot_date != "UNKNOWN":
        age = ((today or date.today()) - datetime.fromisoformat(snapshot_date).date()).days
        if age > max_policy_age_days:
            review_reasons.append(
                f"政策快照已超过{max_policy_age_days}天，须重新核验X官方页面。"
            )
    if review_reasons:
        return PrecheckOutcome("REVIEW_REQUIRED", (), tuple(review_reasons), snapshot_date)
    return PrecheckOutcome(
        "PASS_PRECHECK",
        (),
        ("内部资料字段完整，未触发本版本X官方政策预检查阻塞规则。",),
        snapshot_date,
    )
