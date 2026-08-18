# Project Context

## Identity and purpose

- Project name: Global X Finance Growth Intelligence.
- Current primary product direction: **财经账号实时内容供给工作台** for a content team of roughly 10–15 people.
- Purpose: combine auditable official/financial Evidence, monitored topic candidates, original account Style Packs, human review, manual publishing records, and 1H/6H/24H performance feedback.
- Existing foundation remains the source-of-truth layer: market-specific differences live in Market Packs while one core engine handles validation, storage, evidence, and rules.
- Current boundary: no automatic posting, no investment advice, no impersonation or line-by-line copying of creators, and no claim of whole-web or whole-X coverage.
- Advertising policy/precheck capability is preserved but is not the current product priority and should not be expanded without a new explicit task.
- Intended operator experience includes a local Windows demo that a non-programmer can start from `启动台湾Demo.bat`.
- The Windows launcher validates the current `/stock-radar` build marker before reusing a live process and falls back across ports 8765–8767 when a stale or unrelated service owns the preferred port. New launches open the primary stock radar directly.

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
- Official data connect: TWSE, TPEx, and MOPS share `official_securities`, `official_market_data_daily`, and `official_disclosures`. Market-qualified IDs (`TWSE:2330`, `TPEX:6488`) link daily OHLC/price change/volume/value/transactions and MOPS disclosures back to immutable Raw Evidence. The bounded 2026-08-17 market backfill stores 97,603 daily records across the most recent 50 completed market sessions from 2026-06-05 through 2026-08-17: all 1,087 TWSE and 889 TPEx company securities have real history, with 1,082 TWSE and 887 TPEx securities meeting the 20-session baseline.
- Anomaly Engine V0.1 replays one completed session over unified official history without database writes. All baselines use only `date < replay_date`; rules separately report relative-volume spikes, close-confirmed 20/40-session breakouts, price/volume co-signals, quiet-to-spike volume transitions, and own-history price Z-scores. Ranking is lexicographic by rule count and disclosed raw severity, not a 0–100 HotScore.
- Anomaly validation preserves the V0.1 rule-config hash across the latest session and five prior complete sessions. Same-market current-volume percentile plus `LOW / MEDIUM / HIGH` liquidity level is display/audit context only and is not present in the ranking key.
- Official source permission is four-dimensional. Technical access for TWSE, TPEx, and MOPS is `TECHNICALLY_VERIFIED`; internal use, public display, and redistribution remain `UNKNOWN` until endpoint-specific official terms or a license establish them.
- Traceability: raw Evidence retains source URL, timestamps, content hash, and original payload; downstream data must preserve the link back to raw evidence.
- User-facing demo: Flask application in `src/global_x_finance/webapp.py`, with launch logic in `scripts/start_demo.ps1`.
- Current verified real-data snapshot (2026-08-16): 3,468 raw records, 3,362 normalized records, 1,681 entities, 3,362 item/entity links, and 132 append-only official rule cards across two TWSE daily snapshots. The latest official trading date is 2026-08-14.
- Current policy evidence: `data/mvp.db` has 6 official-page snapshots and 26 rules; the demo database has 12 append-only snapshots (two real fetches of six pages), 52 historical rule rows, and four active checklist templates. The latest six-page rule view contains 26 rules.
- Integration candidate: the separately located xHotTopic codebase already supplies X following-pool collection, immutable page snapshots, deterministic topic linking, heat scoring, coverage states, model cache, usage accounting, and a local dashboard. It should be reused as an X discovery adapter rather than rebuilt inside this repository.
- Current xHotTopic operating state as audited on 2026-08-14: code supports 30-minute refresh, but no matching Windows scheduled task or live snapshot is present; the latest complete local output is dated 2026-08-03 and marked `partial`.
- P02 realtime radar: `config/taiwan_realtime_sources.csv` governs 23 Taiwan-scope entries. Six have `monitoring_status=ACTIVE`: five explicitly listed X accounts through the separate xHotTopic read-only adapter and one TWSE official YouTube channel through its public Atom feed. The single YouTube channel is only “初始验证覆盖”, not completed Taiwan YouTube coverage.
- Realtime source governance keeps `identity_verified`, `endpoint_verified`, `monitoring_method_verified`, `terms_status`, `commercial_use_status`, and `monitoring_status` independent. Public reachability never implies terms or commercial-use authorization; `UNKNOWN` remains unresolved. Runtime success/failure is held separately in `runtime_status`.
- Realtime persistence: migrations `005_realtime_radar.sql` through `009_realtime_active_rights_guard.sql` store source health, separated governance states, per-cycle results, unified feed rows, restart-safe due state, a cross-process runtime lock, initial-backfill markers, and ACTIVE-state guards.
- Realtime schedule: the current-user Windows task `Global X Finance - Taiwan Realtime Radar` dispatches every 10 minutes; X is due every 10 minutes and YouTube every 30 minutes. This is local-machine monitoring, not a platform or 24/7 SLA.
- Ben Radar V2: `/ai-radar` is a read-only Traditional-Chinese research page built from one bounded real-news collection run plus TWSE official daily history. It shows 2H/24H news, top-20 deduplicated event candidates, transparent rule analysis, and 20-day relative-volume/breakout/resonance anomalies for a 30-stock demo pool. It does not claim realtime行情, whole-market coverage, model analysis, investment advice, or publishing capability.
- Ben Radar V2 collection is deliberately bounded to four configured public feed candidates. The 2026-08-16 validation succeeded for Yahoo奇摩股市, Investing.com, and CNBC; Yahoo Finance returned HTTP 429. A failed endpoint remains failed and does not receive synthetic replacement data.
- Ben Radar X Intelligence (P03C): `config/x_accounts.csv` contains exactly 29 accounts (16 core, 12 watch, 1 low-confidence). FxTwitter v2 timeline collection is incremental, bounded to four concurrent requests, stores immutable X Evidence plus engagement snapshots, deduplicates by `platform + post_id`, and reuses the existing scheduler at 10/30/60-minute priority intervals. Low-confidence monitoring is disabled by default.
- `/ai-radar` uses one UTC-backed 24-hour pool and derives strict 2H/24H views from original publication timestamps; Taipei time is display-only. News and financially relevant X posts use deterministic cross-platform clustering, publisher-group deduplication, repost exclusion from independent-source counts, and transparent hot scores. Traditional Chinese is the default; OpenCC supplies the Simplified Chinese UI while original titles and posts remain unchanged.
- The 2026-08-16 P03C real run checked all 29 accounts: 11 returned eligible current content, 18 returned HTTP 204/no new content, and none failed. It stored 42 X posts, including 2 reposts retained as Evidence but excluded from independent-source counts. At 17:00 +08, the dynamic windows contained 4 X posts/0 news in 2H and 41 X posts/52 news in 24H; 85 unified events included 33 X events and 0 cross-platform-confirmed events.
- Yahoo奇摩股市 and Yahoo Finance remain distinct source IDs but share `publisher_group=yahoo`. A controlled 2026-08-16 diagnostic returned HTTP 429 (`DEGRADED_RATE_LIMITED`) for both exact Yahoo Finance endpoints; CNBC remains the working United States news source and Yahoo Finance is not counted as successful.

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
- `monitoring_status` is restricted to `ACTIVE`, `MANUAL_ONLY`, `NEEDS_VERIFICATION`, or `BLOCKED`; it describes local operational governance and cannot substitute for identity, endpoint, method, terms, commercial-use, or sustained-SLA evidence.
- Style Packs must express original positioning and structure without impersonating a named creator or reproducing their wording.
- Original news titles and X post text are immutable display evidence. Language localization applies only to interface text, rule summaries, and supported Chinese conversion; unavailable English translation must remain explicitly unavailable rather than invented.
- BEN Stock Content Radar is served at both `/ai-radar` and `/stock-radar`. Its primary surface is the fixed-rule Taiwan Stock Workbench: latest-complete EOD Top20, actual volume, prior-20 median, RVOL, liquidity, transparent anomaly rules, clickable OHLCV detail, and prior-range chart lines. The existing Chinese-first editorial opportunity radar and browser-local queue remain below it. It is not a trading terminal, realtime quote service, shared workspace, model writer, or publishing system.
- Unified events use shared normalized links or bounded semantic matching across entity, action, topic, time, and text similarity. Reposts and a repeated `publisher_group` do not increase independent confirmation. Cluster diagnostics separate raw input, eligible finance content, multi-item events, multi-publisher events, and cross-platform events; zero remains a valid result.
- Rule-generated Chinese titles are labeled as rule summaries. When no reliable deterministic title can be derived, the homepage shows `中文摘要生成中`; original English remains available only inside the collapsed Evidence section.
- P04 event clustering uses a structured fingerprint and an explainable two-stage decision. Only `SAME_EVENT` merges; `RELATED_BUT_DISTINCT` is retained as a diagnostic relationship. The reviewed 45-pair real-Evidence Gold set and repeatable benchmark are stored under `research/ben_radar_p04/`.
- Localized titles/summaries use `TranslationSummaryAdapter`: cache first, original Chinese second, an optional explicitly configured model with retry third, and honest `TRANSLATION_UNAVAILABLE / RULE_FALLBACK` last. The cache never replaces immutable original Evidence.
- `/stock-radar/cluster-diagnostics` exposes candidate fingerprints and merge/reject reasons. `?test=ben` enables browser-local 10/30/60-second interaction timestamps only; it does not write to the server or prove that a human test occurred.
- The public review surface is a separately built read-only Sites snapshot under `sites/ben-radar-public/`. It exports the current 20-stock anomaly-workbench payload plus 16 ranked opportunity events and their original Evidence links, preserves browser-local queue/JSON/CSV, and has no server write API. The hosted snapshot does not update until the exporter is rerun and a new Sites version is published.
- BEN Radar P05-A adds item-level news trace, structured terminal drop reasons, a diversity-aware snapshot selector, explicit source-concentration metrics, and a Taiwan `StockSignal` layer. Stock IDs are market-qualified (`TWSE:2330` is distinct from `NYSE:TSM`); daily price/volume/turnover signals use the latest completed session against only the prior 20 sessions, preserve nulls, and link back to event IDs and Evidence.
- Public Sites version 4 exports the 2026-08-17 fixed-rule Top20, real bounded EOD OHLCV detail, 16 current opportunity events, original Evidence, source coverage, and snapshot-selection metadata. It remains read-only and manually refreshed; it is not a realtime quote service or investment signal.

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
