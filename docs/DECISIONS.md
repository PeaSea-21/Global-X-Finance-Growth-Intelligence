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

## DEC-023 — Approve three Channel-driven pilots and a post-close channel brief

- Date: 2026-08-19
- Decision: Approve `資金雷達 / SIGNAL_HEAVY`, `個股顯微鏡 / EVENT_HEAVY`, and `產業透視鏡 / CROSS_ENTITY` for P06B. Replace the earlier `12:05` assumption with a Taiwan post-close brief: after the regular session closes, poll each approved source according to its actual EOD readiness and target the primary brief for approximately `15:00–15:15 Asia/Taipei`. After the three-channel pilot passes, the product target is a ranked Top 5 for each of all 20 channels on that channel's configured market clock and daily cutoff; the Taiwan post-close schedule must not be imposed on United States, global-macro, or 24/7 crypto channels.
- Reason: The team needs today's completed Taiwan session, not the prior session while today's market is still open. Different official and media pages finalize their daily rows at different times, so a source-readiness gate is more truthful and reliable than one universal fetch timestamp.
- Impact: Eligible news, company events, market topics, and stock signals enter one evidence-gated candidate pool. AI may order qualified channel assignments `1–5` and explain Why Now and Why Channel, but it may not invent facts, securities, causal links, or missing market values. Every ranked item must expose Evidence, `market_session_date`, `data_as_of`, and relevant stock detail. The system should retry late sources and version the brief; if fewer than five candidates pass, it must show the shortage instead of padding with stale or weak material. `資金雷達` may use explainable EOD price/volume anomalies but may not label them as institutional or ETF net inflow. `個股顯微鏡` starts with limited MOPS + EOD. `產業透視鏡` may use separately reviewed official-industry mapping for candidate recall only; co-occurrence cannot establish supply-chain causality. No realtime-data purchase is approved.
- Status: ACTIVE
- Basis: User clarification on 2026-08-19, P06A recommendation, current read-only capability audit, existing EOD Anomaly Engine, and the absence of a current Channel Daily Brief implementation.

## DEC-024 — Route YouTube narrative inputs through visible, minimized evidence paths

- Date: 2026-08-19
- Decision: Acquire YouTube narrative text through a fail-closed router: user/channel-provided text first, a visible YouTube transcript panel second, and user-provided local media only under an approved transcription path. Keep complete text temporary; persist only source status, URL, method, hash, timestamps, structural features, and short evidence pointers. Do not use login bypass, cookie export, undocumented endpoints, `yt-dlp`, or an unreviewed third-party transcript service.
- Reason: Codex can automate UI checks and downstream analysis, but it cannot make missing captions exist. Persisting full creator transcripts or silently switching to unsupported acquisition would weaken rights governance, originality controls, and the distinction between creator Style Evidence and financial FactPack evidence.
- Impact: Transcript automation is conditional per video. `UI_PRESENT_BUT_UNAVAILABLE` and `NO_TRANSCRIPT_CONTROL` remain valid terminal states. Hook, copy structure, viewpoint, rhythm, and ending can become `OBSERVED` only after lawful text is actually read. Three repeated source observations are required before a narrative mechanism is promoted beyond a single-video hypothesis.
- Status: ACTIVE
- Basis: User authorization on 2026-08-19, the four-video P07 visible-UI pilot, `research/youtube_benchmark_p03/p07/`, and the existing `finance-youtube-inspiration` governance contract.

## DEC-025 — Ship P06B with evidence gates and an explicit ranking fallback

- Date: 2026-08-19
- Decision: Implement the three approved Taiwan channel pilots at configurable `15:05 Asia/Taipei` with source-readiness states, versioned Briefs, prior-only Replay, hard Evidence/as-of/security-ID/channel gates, and `HONEST_SHORTAGE`. Use official TWSE/TPEx Industry Mapping only for cross-entity recall. Expose a pluggable ranker, but label every current run `RULE_BASED_FALLBACK` until a real production model call succeeds.
- Reason: The content team needs a usable daily shortlist now, while model availability, additional corporate datasets, and live editorial feedback remain incomplete. Deterministic ranking is auditable and must not be presented as AI.
- Impact: `/channel-radar` and the generation/audit commands support the three-channel human pilot and five historical Replays. Same-input runs are idempotent and late evidence creates a new version. No system schedule, automatic publishing, paid/realtime data purchase, or all-20 expansion is authorized by this decision.
- Status: ACTIVE
- Basis: P06B execution contract, real 2026-08-11 through 2026-08-17 Replay artifacts, `acceptance_report.json`, browser verification, and full project checks.

## DEC-026 — Publish the first P06B business review as an honest static Replay

- Date: 2026-08-19
- Decision: Under the user's explicit authorization to share with Ben, publish a separate unauthenticated GitHub Pages review surface from a dedicated `gh-pages` branch. Show the 2026-08-17 three-channel Replay as historical, replace technical `READY` and `READY_TO_PITCH` wording with human-review states, and keep feedback browser-local with a downloadable CSV.
- Reason: Ben needs a stable link that does not depend on the user's computer, but the current system does not have today's data, production source coverage, production AI ranking, or a feedback backend.
- Impact: The review URL may be emailed to Ben and displays five candidates for each approved pilot. It does not update automatically, expose server writes, imply that catalysts are confirmed, or upgrade unknown source/public-display rights. Future snapshots require an explicit refresh and deployment.
- Status: ACTIVE
- Basis: User authorization on 2026-08-19, `sites/ben-channel-review/`, public anonymous/browser acceptance, and GitHub Pages commit `aa30bb1`.

## DEC-027 — Run the Taiwan daily pilot at 15:05 with a 24-hour window and no X dependency

- Date: 2026-08-19
- Decision: Run the three Taiwan pilot channels on weekdays at `15:05 Asia/Taipei`. The job must gate on complete TWSE/TPEx EOD coverage, retry late market sources, sync the two official MOPS daily feeds, collect the four bounded public RSS candidates, and admit only items published within the prior 24 hours. Disable the 29-account X path for this daily job. Keep public GitHub Pages publication as a reviewed manual step rather than pushing automatically.
- Reason: Live checks showed both official EOD datasets were available shortly after 14:00 on 2026-08-19, while one MOPS request had a transient SSL failure that succeeded on retry. The user accepts dropping unreliable X collection and wants the team to see current, compact results rather than stale material. Automatic public publication would expand operational and source-rights risk beyond the evidence currently approved.
- Impact: `scripts/run_daily_channel_brief.py` writes one dated output directory, preserves source failures, uses the actual generation time for same-day live runs, uses the configured cutoff for historical Replays, and fails rather than presenting incomplete EOD as current. Items older than 24 hours remain in immutable Evidence storage but cannot enter the daily shortlist. United States scheduling, all-20 expansion, production AI ranking, full copy generation, and automatic public deployment remain unimplemented.
- Status: SUPERSEDED_IN_PART_BY_DEC-029
- Basis: User instruction on 2026-08-19, live TWSE/TPEx/MOPS/RSS checks, `config/channel_pilots.v0.1.json`, `scripts/run_daily_channel_brief.py`, the 2026-08-19 passing preview audit, and Codex automation `ben-radar`.

## DEC-028 — Gate Channel Top 5 on editorial heat, not market abnormality alone

- Date: 2026-08-19
- Decision: Treat EOD price/volume anomalies as candidate discovery rather than proof of a hotspot. A topic may enter a channel Top 5 through either a confirmed-hot path (material event plus independent attention and/or market confirmation) or an early-breaking path (high-materiality new fact before broad discussion). Pure unexplained anomalies remain research leads or backups. Rank qualified topics on disclosed dimensions covering materiality, attention level and acceleration, novelty, market confirmation, Evidence strength, and channel fit. Use attention indexes only after candidate keywords exist. Keep the factual FactPack separate from creator-neutral Channel Reasoning/Style Packs used for titles and scripts.
- Reason: Daily gainers, routine disclosures, and same-industry co-movement occur every session but are not automatically useful content. The business needs to distinguish ordinary market activity from events people are discussing or should discuss, then generate a defensible channel-specific angle.
- Impact: The current `RULE_BASED_FALLBACK` output remains a market/event lead list and must not be relabeled as validated hotspots. WeChat Index or similar third-party attention data can corroborate attention but cannot establish finance truth; X remains optional rather than a blocking dependency. YouTube and authorized channel text may teach recurring reasoning, structure, and tone without cloning a named creator or replacing primary-source facts. Production weights require Ben adoption/rejection examples and a measured pilot before implementation.
- Status: ACTIVE
- Basis: User product clarification and supplied WeChat Index screenshots on 2026-08-19, current `RuleBasedChannelRanker` behavior, Devnors WeChat Index v2/pricing documentation, and the official Jin10 MCP access guide.

## DEC-029 — Collect and explicitly report the 67-account X pool before the Taiwan brief

- Date: 2026-08-20
- Decision: Move the expanded BEN X pool out of the ten-minute realtime dispatcher and collect all 67 configured accounts at 14:35 +08 through a dedicated local Windows task. Retry failed accounts within the same run, require item-level timestamps and Evidence, and expose batch completeness before the weekday 15:20 channel build. The final brief must always include a separate X account report: batch status, completed accounts, completion ratio, new and prior-24-hour post counts, the five most active accounts, and any X-supported final topics with original links. If X has data but none enters the Top 5, say why. If today's batch is absent or incomplete, wait for the already-running task or make at most one bounded supplemental run; continuing after that requires `X_DEGRADED`, with no stale substitution.
- Reason: The user wants a low-cost daily editorial input, not thousands of repeated third-party requests. Controlled testing showed the no-key FxTwitter adapter is currently reachable but has variable latency and no production SLA; high-frequency media also require cursor pagination beyond the first 20 posts.
- Impact: `@ChatGPTapp` is corrected to `@ChatGPT`; `since` is sent in milliseconds; pagination is bounded to ten pages per account; all posts remain `OPINION`; 24-hour filtering and `platform + post_id` deduplication remain mandatory. X failure is a separately reported source degradation and does not convert a complete official EOD brief into a total failure. FxTwitter terms, commercial-use rights, and continuity stay `UNKNOWN`.
- Status: ACTIVE
- Basis: User instruction on 2026-08-20, controlled 67-account FxTwitter probe, two real full-pool runs, Windows Task Scheduler acceptance, `config/x_accounts.csv`, `src/global_x_finance/x_intelligence.py`, and `outputs/x_daily/`.

## DEC-030 — Automatically refresh the read-only BEN page only after a passing daily gate

- Date: 2026-08-20
- Decision: At the weekday 15:20 `ben-radar` run, build and publish the five-channel GitHub Pages payload only when the run is same-day Taipei `PASS`, `replay_mode=false`, and has zero violations. The browser refresh button rereads the latest published JSON with cache busting; it does not trigger collection. Failed, pending, holiday, incomplete, or replay runs retain the previous public date.
- Reason: Ben needs one stable link that changes daily without exposing partial or stale output as current.
- Impact: `權值旗艦` is generated from five fixed weight-stock observations using current official EOD and trade-value ordering; it does not claim complete index contribution. The publisher stages exact page assets in an isolated temporary worktree and may push only `gh-pages`, never `main`, databases, credentials, caches, or unrelated changes. Social posting remains manual.
- Status: ACTIVE; supersedes the manual-publication parts of DEC-026 and DEC-027, with the preview exception in DEC-033.
- Basis: User authorization on 2026-08-20, `scripts/build_ben_content_studio_data.py`, `scripts/publish_ben_content_studio.ps1`, public commit `8ccf53a`, browser acceptance, and Codex automation `ben-radar`.

## DEC-031 — Make `收盤夜話` the first single-channel writing pilot

- Date: 2026-08-21
- Decision: Replace `產業透視鏡` with `收盤夜話` as the first writing-generation pilot without changing the existing three-channel P06B runtime. Use one complete and one metadata-only new-channel sample as a `PROVISIONAL` identity anchor, use the three supplied old-account corpora only for creator-neutral structure, and require five distinct daily episode angles, 2–3 titles per angle, and full cited scripts for the top three.
- Reason: The user can supply this channel's real published material now, and a daily post-close program directly tests whether the system can save Ben's market-review and topic-selection time. The current derived preview is incomplete because it lacks market breadth, three-institution cash flow, margin/short, and TAIFEX futures/options.
- Impact: Production implementation must first connect and validate those official post-close fields and route news/X/YouTube attention into one market-level episode question. Facts, interpretations, and unknowns remain separate; old scripts cannot become current finance facts or named-persona imitation. Existing public pages, the 15:20 job, and the approved P06B channels remain unchanged until a separately verified implementation.
- Status: ACTIVE
- Basis: User instruction and supplied `收盤夜話` samples on 2026-08-21, `research/ben_radar_close_talk/style_pack_v0.1.json`, and `deliverables/BEN_收盤夜話单频道与信源扩充执行方案_2026-08-21.md`.

## DEC-032 — Gate the 13:35 `收盤夜話` editorial build on same-session evidence

- Date: 2026-08-21
- Decision: Keep the existing single-process post-close collection as the first gate, then build a 48-hour `close_talk_fact_pack.json` with 40 official same-session market-activity leaders, generate five ranked angles with 2–3 titles each, write only the top three full drafts, render a readable Markdown handoff, and run `audit_close_talk_editorial.py`. Report editorial success only when the collection, source pack, and editorial audit all pass. The active Codex automation starts at 13:35 Asia/Taipei; the Windows X batch is configured for 13:05 and remains optional `OPINION` input.
- Reason: Ben needs a compact post-close package around 14:00 with actual stock details and clickable evidence, while a stale or incomplete EOD result would make an apparently polished script unsafe to review. The prior FactPack lacked a direct market-activity table for news-selected stocks.
- Impact: Local dated JSON and Markdown are now the verified single-channel deliverables. TAIFEX futures/options, securities lending, public publication of the editorial, production LLM ranking weights, and named-creator imitation remain out of scope. Existing five-channel GitHub Pages publication rules remain unchanged.
- Status: ACTIVE; supersedes the single-channel timing and output-plumbing parts of DEC-031.
- Basis: User request on 2026-08-21, `src/global_x_finance/close_talk_fact_pack.py`, `outputs/ben_channel_daily/2026-08-20/close_talk_fact_pack.json`, `outputs/ben_channel_daily/2026-08-20/close_talk_editorial_audit.json`, and the updated `ben-radar` automation.

## DEC-033 — Publish a clearly labelled same-day preview when the full 收盤夜話 gate is pending

- Date: 2026-08-21
- Decision: Allow the read-only five-channel content studio to publish the same-day `channel_brief` preview when its date, EOD gate, and zero-violation checks pass, even if `close_talk_source_pack` is `SOURCE_PENDING`. The page must keep `收盤夜話` labelled as a preview with data gaps; the full FactPack, titles, and scripts remain unpublished until DEC-032 passes.
- Reason: Ben needs to see today's current EOD/topic direction even when official index, flow, or margin endpoints lag or fail. Showing a labelled preview is useful; presenting an incomplete script as complete is not.
- Impact: The public page may advance to today's date without claiming full 收盤夜話 completion. The stable link remains the same, and a later full editorial publication requires a separate passing source-pack and editorial audit.
- Status: ACTIVE
- Basis: User request after the stale public page was observed, 2026-08-21 `run_summary.json`/`close_talk_source_pack.json`, publisher validation, public commit `647bde0`, and anonymous remote `data.json` verification.

## DEC-034 — Make the public content studio single-channel and manuscript-first

- Date: 2026-08-21
- Decision: The public `/ben-content-studio/` page presents only `收盤夜話`. Its primary deliverable is the complete manuscript for each generated angle, with the title, reason, confirmed facts, unknowns, and clickable Evidence alongside it. Other channel cards and their previews are not rendered on this page. If today's same-session editorial is unavailable, show the explicit unavailable state instead of reusing another channel or an older script.
- Reason: Ben's current review task is to judge whether the `收盤夜話` manuscript is useful; extra channels dilute that review and can make an incomplete day look complete.
- Impact: The page is a focused single-channel review surface. The daily 13:35 source-pack and audit gates remain authoritative; a refresh rereads the latest published JSON but does not trigger collection or create a manuscript.
- Status: ACTIVE; supersedes the display-scope part of DEC-030 and DEC-033.
- Basis: User clarification on 2026-08-21, `sites/ben-content-studio/index.html`, `sites/ben-content-studio/app.js`, `src/global_x_finance/content_studio.py`, and the single-channel page tests.

## DEC-035 — Separate the hard same-day gate from optional close-talk fields

- Date: 2026-08-21
- Decision: Treat current TWSE/TPEx EOD coverage and the current-session TWSE/TPEx index rows as the hard source gate for starting the `收盤夜話` FactPack. Treat TWSE/TPEx institutional flow and margin/short rows as optional enhancement datasets: if they are late or fail, the editorial may proceed only with explicit `UNKNOWN` fields and no stale substitution. The source pack must preserve each endpoint's status, date, URL, and error.
- Reason: Official endpoints settle at different times. Blocking every manuscript on optional flow or margin data would make the delivery time unnecessarily unpredictable, while silently filling those fields would make the script misleading.
- Impact: The active schedule remains 13:35 polling, 13:50 primary build, and an expected 13:50–14:10 delivery on normal days. A missing required index/EOD row keeps the source pack `SOURCE_PENDING`; missing optional rows produce a degraded-but-auditable pack.
- Status: SUPERSEDED_BY_DEC-036.
- Basis: `config/channel_pilots.v0.1.json`, `src/global_x_finance/close_talk_sources.py`, the 2026-08-21 source pack, and the user's timing question.

## DEC-036 — Ship a base manuscript first and enrich it in a second scheduled pass

- Date: 2026-08-21
- Decision: Split `收盤夜話` into two scheduled passes. The 13:35 weekday pass may generate a `BASE_DRAFT` once same-session TWSE/TPEx EOD coverage and derived breadth are ready. Current-session index, institutional flow, margin/short, and other late official rows are enhancement data and must remain `UNKNOWN` until their own endpoint returns the requested date. A separate 14:45 pass reruns the 48-hour news search and late official endpoints; only a fully current enhancement pack may replace the base manuscript as `ENRICHED_DRAFT`, preserving the base files.
- Reason: Official feeds settle at different times and a missing optional row should not erase the day's usable editorial work. A staged delivery gives Ben something reviewable around 14:00 while retaining an auditable path to a stronger revision.
- Impact: The source pack exposes `base_status`, `enhancement_status`, `generation_stage`, per-endpoint attempts, and the source schedule. The TWSE index collector uses the dated `afterTrading/MI_INDEX` fallback when its OpenAPI is stale. No prior-session substitution, automatic posting, or unreviewed public publication is allowed.
- Status: ACTIVE; supersedes the all-fields blocking behavior in DEC-035.
- Basis: Live 2026-08-21 source recheck, `src/global_x_finance/close_talk_sources.py`, `scripts/run_close_talk_enrichment.py`, the two active Codex automations, and targeted source/fact-pack tests.

## DEC-037 — Publish the audited 2026-08-21 `收盤夜話` base manuscript for Ben review

- Date: 2026-08-21
- Decision: Publish the same-day `BASE_DRAFT` to the existing read-only `/ben-content-studio/` GitHub Pages URL after `audit_close_talk_editorial.py` passes. Keep the page single-channel, label the artifact `DRAFT_FOR_HUMAN_REVIEW`, show explicit unknowns for late or unconnected sources, and do not publish other channels or auto-post social content.
- Reason: The 2026-08-21 base FactPack had current TWSE/TPEx EOD rows, breadth, current TWSE institutional flow, 48-hour news, and enough Evidence to produce useful scripts. Waiting for late TPEx/margin/options rows would unnecessarily hide a reviewable manuscript; the audit and source cards preserve the remaining limits.
- Impact: Ben can review five ranked angles, 2–3 title options per angle, three complete scripts, and clickable source cards at the stable public URL. The 14:45 enrichment pass may later replace this file only after a fully current enhancement pack and editorial audit pass. The public page remains a draft-review surface, not investment advice or a production publishing system.
- Status: ACTIVE
- Basis: 2026-08-21 FactPack `status=READY`, editorial audit `PASS` with zero violations, publisher validation `PASS`, GitHub Pages commit `d416696`, and anonymous remote HTTP 200 verification.

## DEC-038 — Make channel identity and human-verifiable source links production requirements

- Date: 2026-08-21
- Decision: Every channel output must use its own versioned, provenance-bounded Style Pack covering language, audience, opening hook, narrative order, fact/opinion balance, stock-detail depth, title syntax, ending pattern, and exclusions. A generic finance script cannot be reused across channels. Every factual source card must open a human-readable official/news page or an exact item-level evidence view; a raw API endpoint alone is not an acceptable Ben-facing link. The daily candidate pool uses the prior 24 hours for fresh events and up to 48 hours for context, then ranks materiality, independent attention, novelty/change, market confirmation, Evidence strength, and channel fit. Display the script body character count at the top of each draft.
- Reason: Ben's review confirms that the business value is not just finding a market move. The useful product is `channel × date × topic × ready-to-record script`, written in the channel's own language and reasoning, with sources that can be checked in one click.
- Impact: New channels stay `PROVISIONAL` until enough real transcripts and Ben keep/reject feedback exist. Source cards need deep-link/row-mapping work before the next public UI iteration. A high price/volume move without event attention or channel fit remains a lead, not a finished topic.
- Status: ACTIVE
- Basis: Ben feedback after reviewing the 2026-08-21 public `收盤夜話` draft, the supplied 2026-08-21 TWSE official index payload, `research/ben_radar_close_talk/style_pack_v0.1.json`, and the current FactPack/editorial contract.

## DEC-039 — Separate Sunday evidence collection from trading-day manuscript generation

- Date: 2026-08-23
- Decision: Run BEN collection Sunday through Friday and exclude Saturday. Monday through Friday keep the 13:35 base and 14:45 enrichment post-close workflow. Sunday uses two source-only `run_ben_weekend_crawl.py` passes that collect the newest 24-hour events plus 24–48-hour context and same-day X status, but never require same-day Taiwan EOD or produce a Sunday `收盤夜話` manuscript. Treat the first-ten channel Style Packs as evidence-bounded: seven channels are `PROVISIONAL`, three channels with no transcripts remain `NO_TRANSCRIPT_NEEDS_SAMPLES`, and profile/sample mismatches remain visible rather than being normalized away.
- Reason: Sunday is a working and research day for the content team but not a regular Taiwan cash-market session. Running the weekday EOD gate on Sunday yields false failures, while pretending the prior Friday is current would violate same-session evidence rules. Sparse samples are useful for provisional identity but cannot justify invented channel voice.
- Impact: Codex automations `ben-radar` and `ben-radar-14-45`, plus the Windows 13:05 X task, run on `SU,MO,TU,WE,TH,FR`; Saturday is excluded. Sunday outputs live under `outputs/ben_weekend_crawl/YYYY-MM-DD/` and are explicitly source snapshots. Manuscripts require an actual body character count, human-readable primary verification links, and raw API URLs only as secondary evidence. No publication or investment advice is added.
- Status: ACTIVE
- Basis: User instruction on 2026-08-23, `research/ben_radar_first10_style_packs/`, `scripts/run_ben_weekend_crawl.py`, the passing 2026-08-23 primary/enrichment snapshots, passing 67/67 X collection, and the updated automation/task definitions.

## DEC-040 — Make the public studio a first-ten-channel review workbench

- Date: 2026-08-23
- Decision: Present all first ten channels on `/ben-content-studio/`. Channels with transcript-backed Style Packs may expose clearly labelled `PROVISIONAL` titles and full drafts; channels without transcripts remain visible but contain no generated topics or scripts. Keep the 2026-08-23 Sunday 24/48-hour research snapshot distinct from the latest successful 2026-08-21 Taiwan close. Preserve actual body character counts, human-readable primary verification links, secondary raw-data links, and explicit missing derivatives evidence.
- Reason: The user clarified that Ben needs to review the broader first-ten-channel system rather than only `收盤夜話`. Hiding channels made completed Style Pack research look absent, while inventing voices for the three sample-free channels would weaken the evidence boundary.
- Impact: The public workbench contains ten ordered channel cards, seven draft-ready channels, three waiting-sample channels, and nine full scripts in the current dated snapshot. `暗池雷達` and `期權守門人` cannot claim institutional direction without original dark-pool/options-chain data. Daily close-talk rebuilds preserve the separately dated first-ten workbench until a newer audited version replaces it. Social posting and `main` publication remain out of scope.
- Status: ACTIVE; supersedes DEC-034 and DEC-037 only for public display scope.
- Basis: User instruction on 2026-08-23, `research/ben_radar_first10_style_packs/style_packs_v0.1.json`, `outputs/ben_weekend_crawl/2026-08-23/latest.json`, `scripts/build_first10_content_studio.py`, passing first-ten audit, browser acceptance, and public `gh-pages` commit `6ec0877`.

## DEC-041 — Expand the public manuscript workbench to all 20 channels

- Date: 2026-08-23
- Decision: Present all 20 ordered channels on `/ben-content-studio/`. A channel may expose titles and a full draft only when at least one user-supplied transcript supports a provenance-bounded `PROVISIONAL` Style Pack; a profile-only channel remains visible with `WAITING_FOR_TRANSCRIPT_SAMPLES` and no invented voice. Preserve the Sunday 2026-08-23 research date separately from the latest successful 2026-08-21 Taiwan market session, and retain profile/sample mismatch warnings in the channel detail.
- Reason: Ben needs one public link for the complete channel matrix. Channel descriptions establish positioning and evidence needs, but they do not establish spoken rhythm, hook, narrative order, or ending voice when no manuscript has been published.
- Impact: The current public workbench has 20 cards, 11 draft-ready channels, nine waiting-sample channels, 15 topics, 13 full manuscripts, 19 transcript samples, and 62 human-verifiable source cards. `全球資金地圖`, `鏈上顯微鏡`, `中概風向球`, and `財商拆彈組` are provisional; their sample/profile boundary notes remain visible. Social posting, automatic approval, and `main` publication remain out of scope.
- Status: SUPERSEDED by DEC-042 for public display scope.
- Basis: User-supplied channel 11–20 descriptions and seven transcripts, `research/ben_radar_second10_style_packs/style_packs_v0.1.json`, `scripts/build_all20_content_studio.py`, passing all-20 audit, desktop/mobile browser acceptance, and public `gh-pages` commit `f57968b`.

## DEC-042 — Show only transcript-backed channels and require five differentiated topics

- Date: 2026-08-23
- Decision: Keep all 20 channel configurations in the generated workbench, but render only channels whose Style Pack is supported by at least one user-supplied manuscript sample. Every publicly visible channel must expose exactly five topics. The same fresh event may be assigned to multiple channels when the channel angle is materially different, but every public title option must remain globally unique. Expand discovery with Federal Reserve, SEC, EIA, ECB, and CoinDesk as optional enhancement sources while preserving the original nine sources as the required base; an optional-source failure cannot invalidate an otherwise passing base crawl.
- Reason: The earlier one-topic result was caused by hardcoded builders, not a shortage in the original source pool. Showing empty channels distracted Ben from reviewable work, while banning shared events would waste strong hotspots that legitimately support different channel theses. Optional official/specialist sources improve cross-market coverage without creating a new single point of failure.
- Impact: The current artifact retains 20 channel records but the page renders 11 transcript-backed channels, each with five topics: 55 topics total, 13 full manuscripts, 40 explicitly labelled outlines, and 134 source cards. Nine sample-free channels remain available for future activation after manuscripts arrive but are absent from the public UI. The audit rejects duplicate public title options and any ready channel with other than five topics. Sunday remains source-only and never masquerades as a Taiwan close.
- Status: ACTIVE; supersedes DEC-041 for public display scope.
- Basis: User instruction on 2026-08-23, live 14-source weekend crawl, `scripts/build_all20_content_studio.py`, `scripts/audit_all20_content_studio.py`, passing 55-topic audit, desktop/mobile browser acceptance, and full project check.

## DEC-043 — Require a complete manuscript for every publicly visible topic

- Date: 2026-08-23
- Decision: Every topic rendered on `/ben-content-studio/` must include a complete human-review manuscript that meets its channel duration: `收盤夜話` at least 3,000 non-whitespace characters; 5–8 minute channels at least 2,000; 3–5 minute channels at least 1,500; and 3-minute channels at least 1,200. All existing and generated bodies pass through the same gate. The audit rejects any outline placeholder, missing/short/duplicate body, internal production wording, duplicate public title option, or ready channel with other than five topics.
- Reason: The former 600-character floor only proved that a body existed; it did not produce a complete recordable program. Ben needs mechanism explanation, competing interpretations, explicit missing-data boundaries, scenario checks, and an audience takeaway without unsupported financial facts.
- Impact: The public surface remains 11 visible channels, 55 topics, 55 unique manuscript bodies, and 134 source cards. Each topic records target duration, minimum characters, actual characters, and pass state. The nine sample-free channels remain hidden, all output remains `DRAFT_FOR_HUMAN_REVIEW`, and missing dark-pool, options, on-chain, ETF-flow, TAIFEX, lending, or company-file data is never invented to extend a script.
- Status: ACTIVE; narrows DEC-042 by removing public outline-only states.
- Basis: User rejection of the 600-character drafts on 2026-08-23, duration-based 55/55 audit, page/publisher gates, 138-test project check, desktop/mobile browser acceptance, and anonymous public verification at `f80a5fa`.

## DEC-044 — Automatically publish passing weekday BEN manuscripts

- Date: 2026-08-24
- Decision: Weekday automations may update only isolated `gh-pages` after same-day, non-replay, zero-violation source/editorial gates, five complete `收盤夜話` scripts, the 55-script audit, and remote-date verification. Social posting and `main` pushes remain forbidden.
- Reason: Advance Ben's stable link only for complete audited daily drafts.
- Impact: Stale dates or failed gates preserve the last public version; Sunday remains source-only.
- Status: ACTIVE; supersedes the no-auto-publication limitation of DEC-036/DEC-037 while preserving their source and review boundaries.
- Basis: 2026-08-24 user authorization, updated automations, publisher gates, and passing checks.

## DEC-045 — Bind manuscripts to topics and preserve outcome history

- Date: 2026-08-24
- Decision: Bind title, question, five-part reason, thesis/counter-thesis, claims, Evidence IDs, and three checkpoints to each manuscript. Archive before replacement; append only dated, evidenced outcomes. Put source cards before manuscripts with original title/link and real source time; new collection preserves `fetched_at`.
- Reason: Prevent generic scripts, erased memory, and undated or unverifiable sources.
- Impact: `今日文稿 / 歷史回顧` preserves history; both automations enforce alignment, archive, Evidence, and valid source-time gates.
- Status: ACTIVE
- Basis: 2026-08-24 user requests, topic/history/source-time code, updated automations, 55/55 and 134/134 audits, tests, and browser acceptance.
<!--xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-->
