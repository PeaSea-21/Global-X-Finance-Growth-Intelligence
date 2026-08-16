# Decisions

## DEC-001 — One core engine with Market Packs

- Date: 2026-08-14
- Decision: Use one core engine for Taiwan, United States, and future markets; express market differences in validated Market Pack configuration.
- Reason: Avoid duplicated market implementations and keep validation, evidence, and rule behavior consistent.
- Impact: Market-specific logic belongs in configuration unless current evidence proves a core extension is necessary.
- Status: ACTIVE
- Basis: `codex_mvp_inputs/product_definition.md`, `schemas/market-pack.schema.json`, `src/global_x_finance/market_pack.py`, and `tests/test_market_pack.py`.

## DEC-002 — Separate source registration from collection permission

- Date: 2026-08-14
- Decision: Treat `registry_status` and `collection_status` as distinct controls; only explicitly permitted sources may be collected automatically.
- Reason: A verified entry point does not establish terms, license, robots, or automation permission.
- Impact: Collectors must reject sources that are active but not collection-authorized and must not invent alternate endpoints.
- Status: ACTIVE
- Basis: `docs/INPUT_AUDIT.md`, `src/global_x_finance/source_registry.py`, `src/global_x_finance/twse_collector.py`, `tests/test_registry.py`, and `tests/test_twse_collector.py`.

## DEC-003 — Preserve raw Evidence and exact deduplication

- Date: 2026-08-14
- Decision: Preserve original content, payload, URL, timestamps, and content hash; deduplicate by original URL or content hash and prohibit overwriting protected Evidence fields.
- Reason: Finance-research claims must remain auditable back to immutable source material.
- Impact: Downstream normalization or AI processing cannot replace raw Evidence; duplicate collection attempts reuse existing records.
- Status: ACTIVE
- Basis: `migrations/001_initial.sql`, `src/global_x_finance/evidence.py`, and `tests/test_evidence.py`.

## DEC-004 — Preserve uncertainty and compliance limits

- Date: 2026-08-14
- Decision: Keep unresolved and conflicting states explicit; do not pass promoted-content precheck without required product and advertiser-license information.
- Reason: Guessing would turn missing evidence into unsupported financial or compliance conclusions.
- Impact: `UNKNOWN`, `NEEDS_VERIFICATION`, and `SOURCE_CONFLICT` remain valid states; Commercial Fit remains `PREDICTED`.
- Status: ACTIVE
- Basis: `codex_mvp_inputs/product_definition.md`, `migrations/001_initial.sql`, `src/global_x_finance/rules.py`, and `tests/test_rules.py`.

## DEC-005 — Keep Project Memory repository-local

- Date: 2026-08-14
- Decision: Store the Project Memory skill only at `.agents/skills/project-memory/` and keep memory in the six repository files governed by `AGENTS.md`.
- Reason: New chats need inspectable continuity without global installation, hidden state, or dependency on a chat transcript.
- Impact: Every task follows the start/end protocols; no Project Memory component is installed in a user or global skills directory.
- Status: ACTIVE
- Basis: CODEX TASK 00.5 requirements, `.agents/skills/project-memory/SKILL.md`, and `AGENTS.md`.

## DEC-006 — Treat memory and handoff as secondary evidence

- Date: 2026-08-14
- Decision: Use code, configuration, Git state, and actual tests to resolve conflicts with memory; never treat an outdated handoff as fact.
- Reason: Project memory can become stale between chats.
- Impact: Unconfirmed statements are labeled `UNKNOWN / NEEDS_CONFIRMATION`, and stale memory is corrected during task wrap-up.
- Status: ACTIVE
- Basis: CODEX TASK 00.5 requirements and `AGENTS.md`.

## DEC-007 — Preserve exact official values in normalization and label signals as rules

- Date: 2026-08-14
- Decision: Normalize audited TWSE fields as their exact official JSON strings, save absent values as `UNKNOWN`, and create only transparent daily cross-sectional cards labeled `RULE_BASED_OFFICIAL_SIGNAL` with versioned formulas and raw Evidence links.
- Reason: Numeric coercion, inferred values, or marketing-style labels would weaken traceability and could misrepresent daily official data as live market intelligence or investment guidance.
- Impact: Normalization is idempotent and cannot mutate `raw_items`; each normalized row links to one Raw Evidence record; signals expose their calculation basis, formula version, freshness, risk statement, and official URL.
- Status: ACTIVE
- Basis: CODEX TASK 03, `migrations/003_normalized_signals.sql`, `src/global_x_finance/normalization.py`, and `tests/test_normalization_signals.py`.

## DEC-008 — Keep X policy evidence official-only, append-only, and fail-closed

- Date: 2026-08-14
- Decision: Fetch policy facts only from the six explicitly registered X official pages, retain each raw HTML response and exact hash as an append-only snapshot, attach every structured rule to a snapshot, and restrict precheck output to `PASS_PRECHECK`, `REVIEW_REQUIRED`, `BLOCKED`, or `UNKNOWN`.
- Reason: Platform content and response bytes can change; a current account capable of buying ads is not evidence of financial licensing, X category pre-authorization, or legal compliance.
- Impact: New response hashes create new versions and never overwrite history. Missing policy evidence, product category, advertiser identity, licensing, pre-authorization, or critical checks cannot pass. `PASS_PRECHECK` never means guaranteed X approval or formal Taiwan/United States legal advice.
- Status: ACTIVE
- Basis: CODEX TASK C01, `migrations/004_x_ads_policy_precheck.sql`, `config/x_ads_policy.pages.json`, `config/x_ads_policy.rules.json`, `src/global_x_finance/policy.py`, `src/global_x_finance/compliance.py`, and `tests/test_policy_compliance.py`.

## DEC-009 — Pivot to a real-time finance content supply workbench

- Date: 2026-08-14
- Decision: Make the current product goal a human-operated finance content supply workbench for roughly 10–15 content staff. Reuse Global X Finance as the source/Evidence/governance foundation and xHotTopic as an X following-pool discovery adapter; add only the missing topic queue, original Style Packs, review workflow, manual-publish record, and 1H/6H/24H feedback layer.
- Reason: The existing projects already solve substantial portions of traceable finance data and X topic discovery. Rebuilding them would add conflicting collectors and Evidence stores without improving coverage or staff workflow.
- Impact: Advertising compliance work is preserved but deprioritized. No automatic posting is added. X/KOL/YouTube/forum material remains `OPINION` until corroborated. Heat and views measure attention, not financial truth. Integration starts through explicit data contracts rather than an immediate repository merge.
- Status: ACTIVE
- Basis: CODEX TASK P01, inspected Global X Finance code/data/tests, inspected local xHotTopic code and 2026-08-03 output, live remote repository audit, and `deliverables/产品方向切换与现有能力审计_P01.md`.

## DEC-010 — Govern realtime discovery separately and preserve opinion provenance

- Date: 2026-08-16
- Decision: Maintain a Taiwan realtime registry with `VERIFIED_ACTIVE`, `VERIFIED_MANUAL_ONLY`, `NEEDS_VERIFICATION`, `BLOCKED`, and `UNKNOWN`; reuse xHotTopic strictly as a read-only X discovery adapter; store X and YouTube material as immutable Raw Evidence and default it to `OPINION`.
- Reason: Candidate identity, entry-point existence, collection feasibility, short-term connectivity, and sustained monitoring are different claims and must not be collapsed into one ACTIVE flag or an unsupported SLA.
- Impact: Only individually verified and configured sources enter the scheduler. The dispatcher runs every 10 minutes, source-specific due state survives restarts, failures preserve the prior success state, publisher groups remain deduplicated, initial backfill is excluded from realtime latency, and no posting or interaction capability is introduced.
- Status: ACTIVE
- Basis: CODEX TASK P02, `config/taiwan_realtime_sources.csv`, migrations `005`–`007`, `src/global_x_finance/realtime_radar.py`, and `tests/test_realtime_radar.py`.
