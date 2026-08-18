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
- Decision: Maintain a Taiwan realtime registry that records `identity_verified`, `endpoint_verified`, `monitoring_method_verified`, `terms_status`, `commercial_use_status`, and `monitoring_status` independently; restrict `monitoring_status` to `ACTIVE`, `MANUAL_ONLY`, `NEEDS_VERIFICATION`, or `BLOCKED`; reuse xHotTopic strictly as a read-only X discovery adapter; store X and YouTube material as immutable Raw Evidence and default it to `OPINION`.
- Reason: Identity, public reachability, technical collection feasibility, platform terms, suitability for commercial internal use, runtime operation, and sustained monitoring are different claims. A public endpoint or successful request cannot establish authorization or SLA.
- Impact: Only identity-, endpoint-, and method-verified configured sources with no explicit rights block enter the scheduler; unresolved terms and commercial-use states remain visibly `UNKNOWN` and are never inferred as allowed. Runtime success/failure is stored separately from governance. The dispatcher runs every 10 minutes, source-specific due state survives restarts, failures preserve the prior success state, publisher groups remain deduplicated, initial backfill is excluded from realtime latency, and no posting or interaction capability is introduced.
- Status: ACTIVE
- Basis: CODEX TASK P02 plus supplemental acceptance, `config/taiwan_realtime_sources.csv`, migrations `005`–`009`, `src/global_x_finance/realtime_radar.py`, and `tests/test_realtime_radar.py`.

## DEC-011 — Keep Ben Radar V2 bounded, evidence-linked, and rule-transparent

- Date: 2026-08-16
- Decision: Build the second Ben radar as a bounded demo from one real collection run, immutable source links, TWSE official daily history, deterministic title clustering, and explicit 20-day rules. A news endpoint is usable only when the actual run returns valid title/time/link rows; failed endpoints retain their real failure. The page shows at most 20 ranked event candidates and never labels rule output as model analysis or investment advice.
- Reason: Ben needs a readable evidence-first page today, while broad collectors, opaque scoring, fake fallback news, and new publishing paths would weaken traceability and exceed the lean scope.
- Impact: The four source candidates are Yahoo奇摩股市, Yahoo Finance, Investing.com, and CNBC. RVOL is current volume divided by the prior-20-session median; breakout/resonance labels remain transparent rules. K-line work is deferred until core coverage and anomaly quality are accepted.
- Status: ACTIVE
- Basis: CODEX TASK P03B-LEAN, `migrations/010_ben_radar_v2.sql`, `src/global_x_finance/ben_radar.py`, `src/global_x_finance/webapp.py`, and `tests/test_ai_market_radar.py`.

## DEC-012 — Use one incremental X pool and deterministic unified events

- Date: 2026-08-16
- Decision: Read the supplied 29-account CSV through one FxTwitter v2 incremental timeline collector, store UTC Evidence keyed by `platform + post_id`, reuse the existing P02 scheduler by account priority, and derive both 2H and 24H views from original publication time. Combine only financially relevant news/X items through deterministic company-plus-action or shared-link evidence; count each `publisher_group` once and never count a pure repost as an independent source.
- Reason: Two collectors or fetch-time windows would duplicate work and distort freshness; raw engagement, same-company mentions, reposts, and multiple handles owned by one publisher are not independent confirmation.
- Impact: The page is database-read-only, defaults to a 24H Traditional-Chinese view, preserves original titles/posts, converts supported UI text with OpenCC, and exposes truthful empty/zero states. Yahoo奇摩股市 and Yahoo Finance remain separate source IDs with one `yahoo` publisher group; repeated HTTP 429 results stay `DEGRADED_RATE_LIMITED` and are not counted as success. This remains a bounded prototype, not whole-X coverage, sustained SLA, or authorization for commercial monitoring.
- Status: ACTIVE
- Basis: CODEX TASK P03C-LEAN, `config/x_accounts.csv`, `migrations/011_ben_x_intelligence.sql`, `src/global_x_finance/x_intelligence.py`, `src/global_x_finance/webapp.py`, and `tests/test_x_intelligence.py`.

## DEC-013 — Make the radar a Chinese-first editorial opportunity workflow

- Date: 2026-08-16
- Decision: Keep the verified news/X/TWSE collection foundation, defer new Twelve Data and SEC integrations, and make the primary radar a Chinese-first topic opportunity workflow. Show rule-derived Chinese titles, stock relationships, evidence breadth, bounded market response, content angles, and a browser-local topic queue; keep original English and full URLs inside collapsed Evidence and move collection diagnostics to `/radar`.
- Reason: The prior page exposed collection output rather than helping a finance editor choose a verifiable topic. Its rolling-window audit also showed that the apparent 93-to-85 compression did not represent meaningful clustering, so adding sources or polishing the old three-column card would not resolve the product problem.
- Impact: `/ai-radar` and `/stock-radar` share 24H/12H/6H category/source/sort views. Event matching is tiered by normalized link, entity, action, topic, time, and text similarity; diagnostics distinguish eligible content, multi-item clusters, independent publisher groups, and cross-platform confirmation. LocalStorage key `ben-stock-radar.topic-queue.v1` supports queue/ignore/note/restore/JSON/CSV without server writes. The page does not claim AI translation, whole-market coverage, realtime行情, automated drafting/publishing, or investment advice.
- Status: ACTIVE
- Basis: current user product direction, `src/global_x_finance/x_intelligence.py`, `src/global_x_finance/webapp.py`, `src/global_x_finance/templates/ai_market_radar.html`, `src/global_x_finance/static/demo.css`, browser acceptance, and `deliverables/xgrowth.tools_股票方向横纵分析报告.md`.

## DEC-014 — Benchmark explainable event clustering and fail honestly on unavailable translation

- Date: 2026-08-16
- Decision: Evaluate event merging against a reviewed real-Evidence Gold set with three labels, use structured fingerprints plus an explainable candidate/recheck pipeline, and preserve merge/reject reasons. Localized title/summary generation is cache-first; original Chinese is reused, an explicitly configured model may be retried, and deterministic fallback must report `TRANSLATION_UNAVAILABLE` rather than claim an AI translation.
- Reason: Compression rate alone rewards unsafe merges, while a Chinese-first homepage cannot turn an unavailable translator into fabricated localized facts.
- Impact: `SAME_EVENT` is the only positive merge label; `RELATED_BUT_DISTINCT` remains a useful association but not one event. Heat and Evidence quality are separate. Homepage factual claims remain traceable to Evidence, market interpretation is labeled separately, and the browser-local Ben test records interaction timestamps without adding server writes.
- Status: ACTIVE
- Basis: BEN Radar P04, `research/ben_radar_p04/event_cluster_gold.jsonl`, `src/global_x_finance/event_clustering.py`, `src/global_x_finance/translation_summary.py`, `scripts/benchmark_ben_clusters.py`, and `scripts/validate_ben_p04.py`.

## DEC-015 — Publish external review as a read-only hosted snapshot

- Date: 2026-08-17
- Decision: Use a separately built HTTPS Sites snapshot for unauthenticated external BEN Radar review; do not treat local Flask plus random tunnel processes as a deliverable.
- Reason: Both Cloudflare Quick Tunnel and LocalTunnel links failed when their foreground/background processes were reclaimed, while external reviewers need an address independent of the operator's computer.
- Impact: The public site preserves the 16 ranked event cards, original Evidence links, transparent scores, local queue/notes, and JSON/CSV export, but it is an explicitly dated snapshot and must be republished to refresh data. Dynamic collection and diagnostics remain local.
- Status: ACTIVE
- Basis: `sites/ben-radar-public/`, `scripts/export_ben_public_site.py`, hosted Sites version 1, and the 2026-08-17 tunnel failure evidence.

## DEC-016 — Trace every news item and rank stock-linked editorial signals without future leakage

- Date: 2026-08-17
- Decision: Give every persisted BEN news item one structured pipeline trace and terminal outcome; qualify security IDs by market; derive Taiwan StockSignal components from the latest completed session plus only its prior 20 sessions; expose source-concentration warnings and use a bounded marginal publisher-concentration penalty when selecting the public 16-card snapshot.
- Reason: The pre-P05-A public export hid the distinction between stale input, ranking loss, and source exclusion, and it exposed no stock-centric path even though official history existed. A mechanical publisher cap or missing-as-zero market score would be equally misleading.
- Impact: Old news remains outside the current 24-hour view but can be audited at its original time. The public snapshot may retain lower-scoring independent Evidence when its marginal editorial value exceeds another repeated-publisher item, without inventing sources. HotScore is explainable editorial prioritization, not a buy/sell score.
- Status: ACTIVE
- Basis: BEN Radar P05-A, `src/global_x_finance/pipeline_trace.py`, `src/global_x_finance/radar_analytics.py`, `src/global_x_finance/stock_signals.py`, `research/ben_radar_p05a/`, and public Sites version 2.

## DEC-017 — Separate source reachability from production connection status

- Date: 2026-08-17
- Decision: For the first Taiwan source pack, classify TWSE, TPEx, and MOPS official OpenAPI routes as `P0_CONNECT`; classify CNA and Yahoo Taiwan RSS as `DISCOVERY_ONLY` until commercial/public-product permission exists; and classify UDN Money, MoneyDJ, and DIGITIMES as `DO_NOT_AUTOMATE` under their current public rules or failed feed state.
- Reason: A public page, HTTP 200, RSS directory, or prior prototype row does not establish stable parsing or commercial collection rights. The audit must require a real item-level fetch plus an independently recorded authorization/robots assessment.
- Impact: Future source work must use a separate authorized integration task. It may not convert the successful HTML probes or noncommercial RSS feeds into production collectors, and it must preserve explicit `FAILED` or discovery-only states instead of inventing replacement data.
- Status: ACTIVE
- Basis: `research/ben_radar_source_audit/source_audit.csv`, official TWSE/TPEx OpenAPI documentation, CNA/Yahoo RSS terms, and the live 2026-08-17 bounded fetch/robots checks.

## DEC-018 — Unify official Taiwan market data while keeping usage rights unknown

- Date: 2026-08-17
- Decision: Normalize TWSE and TPEx company securities into one market-qualified Security/MarketData schema, link MOPS material information to the same security IDs, preserve each source row as immutable Evidence, and store technical/internal/public-display/redistribution permission states independently.
- Reason: Endpoint reachability alone does not make two exchanges comparable and does not establish commercial display or redistribution rights. The anomaly engine needs one stable read model without losing official-source provenance or unit semantics.
- Impact: TWSE and TPEx daily records use the same date/OHLC/change/volume/value/transaction fields; TPEx historical values reported in thousands are converted to shares and New Taiwan dollars. MOPS supports security-to-recent-disclosure lookup. Technical access is verified, while all three nontechnical usage scopes remain `UNKNOWN`.
- Status: ACTIVE
- Basis: BEN RADAR Step 2 OFFICIAL DATA CONNECT, `migrations/013_official_data_connect.sql`, `config/official_data.sources.json`, `src/global_x_finance/official_data.py`, and the bounded 2026-08-17 live validation.

## DEC-019 — Backfill Taiwan history by official market/date batches

- Date: 2026-08-17
- Decision: Backfill the current TWSE and TPEx company-security universe from official whole-market daily endpoints, commit each market/date batch incrementally, retain one immutable full-response Evidence item per batch, and treat 20 valid OHLCV sessions as the minimum anomaly-engine eligibility threshold.
- Reason: Per-security requests are unnecessary and fragile when both exchanges expose daily market-wide data. Incremental date batches provide honest units, efficient coverage, resumability, and bounded loss on interruption without creating a parallel schema.
- Impact: `official_market_data_daily` remains the only MarketData store and keeps its `(security_id, trade_date)` uniqueness. Volume is stored as actual shares and turnover as New Taiwan dollars. Missing or incomplete official rows remain `UNKNOWN`; securities with fewer than 20 valid sessions remain `INSUFFICIENT_HISTORY`. Resume skips complete dates and retries recorded failures without replacing historical facts or using future data.
- Status: ACTIVE
- Basis: BEN RADAR Step 2.5, `migrations/014_market_history_backfill.sql`, `src/global_x_finance/market_history_backfill.py`, `scripts/backfill_market_history.py`, `tests/test_market_history_backfill.py`, and `research/ben_radar_market_history/backfill_status.json`.

## DEC-020 — Rank anomalies by disclosed prior-only rules, not a composite HotScore

- Date: 2026-08-17
- Decision: Replay TWSE and TPEx from one shared rule engine whose volume, range, quiet-state, and price-volatility baselines exclude the Replay day. Rank first by independent rule-hit count and then by explicitly ordered raw severities; do not create a 0–100 composite score.
- Reason: Content editors must be able to see why one stock ranks above another, and a large absolute-volume stock must not outrank a smaller stock solely due to company size. Current history also cannot honestly support a prior-40-session range for the TWSE universe.
- Impact: Thresholds and explanations live in `config/anomaly_rules.v0.1.json`. Close-confirmed breakouts are distinct from intraday-only breaks; price/volume breakout requires both a range break and 2x relative volume. Zero/nonpositive prices, more-than-30% prior unadjusted jumps, missing current rows, and insufficient history are excluded with explicit quality states. V0.1 output is `READY_FOR_HUMAN_REVIEW`, never `RULES_VERIFIED`.
- Status: ACTIVE
- Basis: BEN RADAR Step 3, `src/global_x_finance/anomaly_engine.py`, `tests/test_anomaly_engine.py`, and `research/ben_radar_anomaly/`.

## DEC-021 — Validate fixed anomaly rules across days and keep liquidity non-ranking

- Date: 2026-08-17
- Decision: Extend the bounded official history only to the latest 50 completed sessions needed for five prior Replay dates, preserve the exact V0.1 rule-config hash, and attach same-market current-volume percentile plus `LOW / MEDIUM / HIGH` liquidity context without adding either field to the ranking key.
- Reason: A single day cannot show repeated alerts, low-base RVOL noise, or cross-stock co-movement. Liquidity context helps human reviewers interpret these cases but changing rank would silently create a new algorithm.
- Impact: Each of the five prior dates exports one all-market Top20 CSV. Prior-40 coverage must be at least 95% for each market/date to pass; unavoidable new-listing, suspension, and no-trade gaps remain partial. Potential sector movement is only a ticker-prefix co-occurrence lead until an authorized security-to-industry mapping exists.
- Status: ACTIVE
- Basis: BEN RADAR Step 3.5, unchanged `config/anomaly_rules.v0.1.json`, `scripts/run_anomaly_validation.py`, and `research/ben_radar_anomaly_validation/validation_audit.json`.

## DEC-022 — Make the fixed-rule anomaly output the primary stock-workbench read model

- Date: 2026-08-18
- Decision: Build the stock workbench directly from Anomaly Engine V0.1 Replay output and unified official OHLCV. Remove the legacy StockSignal HotScore from the stock surface; use a read-only presentation adapter for Chinese rule labels, current streaks, early-momentum filtering, chart history, and MOPS reverse lookup.
- Reason: The prior page displayed an outdated 2026-08-14 signal layer and opaque stock score even though the verified prior-only engine had a newer 2026-08-17 Replay. Editors need actual volume, relative volume, rule hits, and chart evidence before content ranking.
- Impact: `/stock-radar` and the public snapshot show EOD rather than realtime status. Early momentum and persistence are display-only and cannot change V0.1 ranking. Missing MOPS Evidence remains `尚未確認`; the page does not infer a catalyst. The existing opportunity radar remains below the stock workbench.
- Status: ACTIVE
- Basis: BEN RADAR Step 4, `src/global_x_finance/stock_workbench.py`, `src/global_x_finance/templates/ai_market_radar.html`, `sites/ben-radar-public/`, and Sites version 4.
