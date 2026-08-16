# Project Context

## Identity and purpose

- Project name: Global X Finance Growth Intelligence.
- Current primary product direction: **财经账号实时内容供给工作台** for a content team of roughly 10–15 people.
- Purpose: combine auditable official/financial Evidence, monitored topic candidates, original account Style Packs, human review, manual publishing records, and 1H/6H/24H performance feedback.
- Existing foundation remains the source-of-truth layer: market-specific differences live in Market Packs while one core engine handles validation, storage, evidence, and rules.
- Current boundary: no automatic posting, no investment advice, no impersonation or line-by-line copying of creators, and no claim of whole-web or whole-X coverage.
- Advertising policy/precheck capability is preserved but is not the current product priority and should not be expanded without a new explicit task.
- Intended operator experience includes a local Windows demo that a non-programmer can start from `启动台湾Demo.bat`.

## Architecture

- Runtime: Python 3.11 or newer; package metadata is in `pyproject.toml`.
- Core package: `src/global_x_finance/`.
- Market configuration: `codex_mvp_inputs/taiwan.market-pack.yaml` and `codex_mvp_inputs/us.market-pack.template.yaml`, validated by `schemas/market-pack.schema.json` through the same code path.
- Persistence: SQLite migrations in `migrations/`; runtime databases under `data/` are ignored by Git.
- Normalization: `src/global_x_finance/normalization.py` maps the three audited TWSE datasets into exact, traceable fields while preserving missing fields as `UNKNOWN` and never modifying `raw_items`.
- Official signals: `official_signal_cards` stores versioned, rule-based daily research cards with explicit Evidence links, official URLs, freshness, calculation basis, and risk wording; these are not investment advice or two-hour live hotspots.
- X Ads policy evidence: `src/global_x_finance/policy.py` fetches only the six registered `business.x.com` pages, stores raw HTML and SHA-256 in append-only `policy_snapshots`, and links versioned `policy_rules` back to the exact snapshot and official URL.
- Financial ad precheck: `src/global_x_finance/compliance.py` supports separate Taiwan/United States and financial/crypto templates. It fails closed to `UNKNOWN`, `REVIEW_REQUIRED`, or `BLOCKED` unless every required fact is present; `PASS_PRECHECK` is only an internal result and never guaranteed approval or legal advice.
- Source governance: `codex_mvp_inputs/verified_source_registry.csv` is the supplied registry; collection permission is controlled separately from registry activation.
- Traceability: raw Evidence retains source URL, timestamps, content hash, and original payload; downstream data must preserve the link back to raw evidence.
- User-facing demo: Flask application in `src/global_x_finance/webapp.py`, with launch logic in `scripts/start_demo.ps1`.
- Current verified real-data snapshot: 1,681 raw records, 1,681 normalized records, 1,681 entity links, and 66 official rule cards from the existing TWSE collection.
- Current policy evidence: `data/mvp.db` has 6 official-page snapshots and 26 rules; the demo database has 12 append-only snapshots (two real fetches of six pages), 52 historical rule rows, and four active checklist templates. The latest six-page rule view contains 26 rules.
- Integration candidate: the separately located xHotTopic codebase already supplies X following-pool collection, immutable page snapshots, deterministic topic linking, heat scoring, coverage states, model cache, usage accounting, and a local dashboard. It should be reused as an X discovery adapter rather than rebuilt inside this repository.
- Current xHotTopic operating state as audited on 2026-08-14: code supports 30-minute refresh, but no matching Windows scheduled task or live snapshot is present; the latest complete local output is dated 2026-08-03 and marked `partial`.
- P02 realtime radar: `config/taiwan_realtime_sources.csv` governs 23 Taiwan-scope entries. Six are `VERIFIED_ACTIVE`: five explicitly listed X accounts through the separate xHotTopic read-only adapter and one TWSE official YouTube channel through its public Atom feed.
- Realtime persistence: migrations `005_realtime_radar.sql` through `007_radar_backfill_marker.sql` store source health, per-cycle results, unified feed rows, restart-safe due state, a cross-process runtime lock, and initial-backfill markers.
- Realtime schedule: the current-user Windows task `Global X Finance - Taiwan Realtime Radar` dispatches every 10 minutes; X is due every 10 minutes and YouTube every 30 minutes. This is local-machine monitoring, not a platform or 24/7 SLA.

## Durable rules and boundaries

- Taiwan and United States must use one core engine; do not fork business logic by market when a Market Pack can express the difference.
- `registry_status=ACTIVE` confirms a registered entry, not permission to collect it. Only an explicitly permitted `collection_status` may reach an automated collector.
- Do not bypass robots rules, logins, paywalls, terms, licenses, or other access restrictions.
- Deduplicate independent sources by `publisher_group`.
- Preserve unresolved states such as `UNKNOWN`, `NEEDS_VERIFICATION`, and `SOURCE_CONFLICT`; do not replace them with guesses.
- Test-generated finance data must be labeled `SYNTHETIC_TEST_DATA`.
- Commercial fit is predictive only. Promoted-content precheck cannot pass while required product or advertiser-license facts are absent.
- No automatic publishing, automatic interaction, account pools, proxy/IP rotation, device-fingerprint evasion, or investment recommendations are within the current foundation scope.
- KOL, X, YouTube, and forum material is `OPINION` unless independently supported by qualified Evidence; popularity or engagement cannot upgrade a statement into a financial fact.
- Initial discovery backfill must not be used to calculate realtime detection latency; only post-baseline newly discovered items qualify.
- Style Packs must express original positioning and structure without impersonating a named creator or reproducing their wording.

## Source-of-truth order

1. Current user instruction and current task specification.
2. Current code, schemas, configuration, and actual command/test output.
3. Supplied product and database contracts in `codex_mvp_inputs/`.
4. Project memory files.
5. Historical prose or chat context.

## Standard verification

- Full project tests and credential scan: `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`.
- Project Memory integrity check: `powershell -ExecutionPolicy Bypass -File scripts/project-memory-check.ps1`.
- Source registry validation only: `python -m global_x_finance.cli sources validate --registry codex_mvp_inputs/verified_source_registry.csv`.

## Stable unknowns

- United States verified sources: `UNKNOWN / NEEDS_CONFIRMATION` until a validated registry is supplied.
- Advertiser identity, product details, applicable licenses, X pre-authorization, account verification, disclosures, and landing-page checks required for promoted-content compliance: `UNKNOWN / NEEDS_CONFIRMATION`.
- X policy pages do not provide all Taiwan or United States legal requirements, and page-level `page_updated_at` is `UNKNOWN` where the official page does not state it; human legal/compliance review remains required.
- Collection rights for sources not marked `API_VERIFIED`: `UNKNOWN / NEEDS_CONFIRMATION` pending terms, license, robots, or permission review.
