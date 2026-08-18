from __future__ import annotations

from global_x_finance.event_clustering import (
    DIFFERENT_EVENT,
    RELATED_BUT_DISTINCT,
    SAME_EVENT,
    decide_event_pair,
    event_fingerprint,
)
from global_x_finance.translation_summary import TranslationSummaryAdapter


def _item(text, *, entities=(), actions=(), topics=(), at="2026-08-16T08:00:00+00:00", kind="NEWS"):
    return {
        "id": text[:8], "kind": kind, "text": text, "published_at": at,
        "entities": list(entities), "actions": list(actions), "topics": list(topics),
        "external_urls": [],
    }


def test_fingerprint_contains_p04_contract_fields():
    fingerprint = event_fingerprint(_item(
        "Nvidia weighs $3 billion investment in SB Energy for Ohio AI data center",
        entities=["NVDA"], actions=["investment"], topics=["半導體與AI"],
    ))
    assert set(fingerprint) == {
        "primary_entity", "ticker", "company", "actor", "action", "event_stage",
        "target", "object", "number", "currency", "percentage", "geography",
        "theme", "timestamp", "event_date", "source_type",
    }
    assert fingerprint["ticker"] == "NVDA"
    assert "USD:3billion" in fingerprint["number"]


def test_two_stage_merges_same_amount_and_target_but_not_same_company_other_event():
    left = _item("Nvidia weighs $3 bln in SB Energy for Ohio AI data center", entities=["NVDA"], actions=["investment", "partnership"], topics=["半導體與AI"])
    right = _item("Nvidia in talks to invest $3 billion in SB Energy data center", entities=["NVDA"], actions=["investment", "partnership"], topics=["半導體與AI"])
    other = _item("Nvidia reports quarterly earnings guidance", entities=["NVDA"], actions=["earnings"], topics=["財報與公司"])
    assert decide_event_pair(left, right).label == SAME_EVENT
    assert decide_event_pair(left, other).label in {RELATED_BUT_DISTINCT, DIFFERENT_EVENT}


def test_different_event_stage_does_not_blindly_merge():
    planned = _item("Acme is in talks to acquire TargetCo", entities=["ACME"], actions=["investment"])
    completed = _item("Acme completed acquisition of TargetCo", entities=["ACME"], actions=["investment"])
    decision = decide_event_pair(planned, completed)
    assert decision.label == RELATED_BUT_DISTINCT
    assert "不同事件阶段" in decision.reject_reason


def test_translation_adapter_cache_and_honest_fallback(database):
    adapter = TranslationSummaryAdapter(database)
    first = adapter.summarize(
        "Emergency services battle a large wildfire in Belgium",
        entities=[], actions=["security"], topics=["地緣政治"], source_language="en",
    )
    second = adapter.summarize(
        "Emergency services battle a large wildfire in Belgium",
        entities=[], actions=["security"], topics=["地緣政治"], source_language="en",
    )
    assert first == second
    assert first.status == "TRANSLATION_UNAVAILABLE"
    assert first.method == "RULE_FALLBACK"
    assert any("\u4e00" <= character <= "\u9fff" for character in first.title_zh)
    assert database.execute("SELECT COUNT(*) FROM ben_translation_summary_cache").fetchone()[0] == 1
