from __future__ import annotations

from scripts.audit_close_talk_editorial import audit_editorial


def _fact_pack() -> dict:
    return {
        "market_session_date": "2026-08-24",
        "cash_market_source_pack": {
            "datasets": [{"dataset_id": "MARKET", "status": "READY"}]
        },
        "market_activity_leaders": [],
        "news_leads": [],
        "x_attention_leads": [],
        "official_disclosure_leads": [],
        "candidate_leads": [],
    }


def _editorial(script_length: int = 3000) -> dict:
    evidence_id = "OFFICIAL:MARKET:2026-08-24"
    return {
        "status": "DRAFT_FOR_HUMAN_REVIEW",
        "market_session_date": "2026-08-24",
        "angles": [
            {
                "rank": rank,
                "title_options": [f"標題{rank}A", f"標題{rank}B"],
                "confirmed_facts": [
                    {"text": f"事實{rank}", "evidence_ids": [evidence_id]}
                ],
                "unknowns": ["仍有未知資料"],
                "tomorrow_checkpoints": [{"metric": "下一交易日核對"}],
                "source_cards": [
                    {
                        "evidence_id": evidence_id,
                        "epistemic_status": "FACT",
                        "human_verification_url": "https://example.com/official",
                    },
                    {
                        "evidence_id": evidence_id,
                        "epistemic_status": "FACT",
                        "human_verification_url": "https://example.com/official",
                    },
                ],
                "script": {
                    "full_text": "稿" * script_length,
                    "character_count": script_length,
                },
            }
            for rank in range(1, 6)
        ],
    }


def test_audit_requires_five_duration_complete_manuscripts() -> None:
    assert audit_editorial(_editorial(), _fact_pack()) == []


def test_audit_rejects_short_fifth_manuscript() -> None:
    editorial = _editorial()
    editorial["angles"][4]["script"] = {
        "full_text": "稿" * 2999,
        "character_count": 2999,
    }

    assert "FULL_SCRIPT_TOO_SHORT_OR_MISSING:5" in audit_editorial(
        editorial,
        _fact_pack(),
    )
