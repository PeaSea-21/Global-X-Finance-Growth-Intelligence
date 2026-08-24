from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse


BANNED = ("加老師", "老師賴", "官方Line", "飆股名單", "進出場點位", "保證獲利", "穩賺")


def _fact_pack_evidence_ids(pack: dict) -> set[str]:
    ids = {
        f"OFFICIAL:{row['dataset_id']}:{pack['market_session_date']}"
        for row in pack["cash_market_source_pack"]["datasets"]
        if row["status"] == "READY"
    }
    ids.update(row["evidence_id"] for row in pack.get("market_activity_leaders", []))
    for field in ("news_leads", "x_attention_leads", "official_disclosure_leads"):
        ids.update(row["evidence_id"] for row in pack.get(field, []))
    for candidate in pack.get("candidate_leads", []):
        ids.update(row["evidence_id"] for row in candidate.get("evidence", []))
        ids.update(row["evidence_id"] for row in candidate.get("opinion_evidence", []))
    return ids


def audit_editorial(payload: dict, fact_pack: dict) -> list[str]:
    violations: list[str] = []
    if payload.get("market_session_date") != fact_pack.get("market_session_date"):
        violations.append("MARKET_SESSION_DATE_MISMATCH")
    if payload.get("status") != "DRAFT_FOR_HUMAN_REVIEW":
        violations.append("INVALID_EDITORIAL_STATUS")
    angles = payload.get("angles") or []
    if len(angles) != 5:
        violations.append("ANGLE_COUNT_NOT_FIVE")
    if [row.get("rank") for row in angles] != list(range(1, 6)):
        violations.append("RANKS_NOT_1_TO_5")
    allowed_ids = _fact_pack_evidence_ids(fact_pack)
    all_text = json.dumps(payload, ensure_ascii=False)
    for phrase in BANNED:
        if phrase.casefold() in all_text.casefold():
            violations.append(f"BANNED_PROMOTION:{phrase}")

    for angle in angles:
        rank = angle.get("rank", "UNKNOWN")
        titles = angle.get("title_options") or []
        if not 2 <= len(titles) <= 3 or any(not str(title).strip() for title in titles):
            violations.append(f"INVALID_TITLE_OPTIONS:{rank}")
        cards = angle.get("source_cards") or []
        if len(cards) < 2:
            violations.append(f"INSUFFICIENT_SOURCE_CARDS:{rank}")
        card_ids = {card.get("evidence_id") for card in cards}
        if not any(card.get("epistemic_status") in {"FACT", "REPORTED"} for card in cards):
            violations.append(f"NO_FACT_OR_REPORTED_SOURCE:{rank}")
        for card in cards:
            evidence_id = card.get("evidence_id")
            if evidence_id not in allowed_ids:
                violations.append(f"UNKNOWN_EVIDENCE_ID:{rank}:{evidence_id}")
            human_url = str(card.get("human_verification_url") or card.get("url") or "")
            if urlparse(human_url).scheme not in {"http", "https"}:
                violations.append(f"NON_CLICKABLE_SOURCE:{rank}:{evidence_id}")
            if "/rwd/" in human_url or "response=json" in human_url:
                violations.append(f"RAW_API_USED_AS_HUMAN_SOURCE:{rank}:{evidence_id}")
            raw_url = str(card.get("raw_api_url") or "")
            if raw_url and urlparse(raw_url).scheme not in {"http", "https"}:
                violations.append(f"NON_CLICKABLE_RAW_SOURCE:{rank}:{evidence_id}")
        for fact in angle.get("confirmed_facts") or []:
            evidence_ids = fact.get("evidence_ids") or []
            if not evidence_ids or any(value not in card_ids for value in evidence_ids):
                violations.append(f"FACT_WITHOUT_LOCAL_SOURCE_CARD:{rank}")
        if not angle.get("unknowns"):
            violations.append(f"MISSING_UNKNOWNS:{rank}")
        if not angle.get("tomorrow_checkpoints"):
            violations.append(f"MISSING_CHECKPOINTS:{rank}")
        script = angle.get("script")
        full_text = str(script.get("full_text") or "") if isinstance(script, dict) else ""
        actual_count = len("".join(full_text.split()))
        if not isinstance(script, dict) or actual_count < 3000:
            violations.append(f"FULL_SCRIPT_TOO_SHORT_OR_MISSING:{rank}")
        elif script.get("character_count") != actual_count:
            violations.append(f"INVALID_SCRIPT_CHARACTER_COUNT:{rank}")
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit 收盤夜話 generated editorial JSON.")
    parser.add_argument("--editorial", required=True)
    parser.add_argument("--fact-pack", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    payload = json.loads(Path(args.editorial).read_text(encoding="utf-8"))
    fact_pack = json.loads(Path(args.fact_pack).read_text(encoding="utf-8"))
    violations = audit_editorial(payload, fact_pack)
    result = {
        "status": "PASS" if not violations else "FAIL",
        "market_session_date": payload.get("market_session_date"),
        "angle_count": len(payload.get("angles") or []),
        "violation_count": len(violations),
        "violations": violations,
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not violations else 1


if __name__ == "__main__":
    raise SystemExit(main())
