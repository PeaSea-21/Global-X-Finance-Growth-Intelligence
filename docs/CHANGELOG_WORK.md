# Work Changelog

## 2026-08-24 — main repository consolidation

- Consolidated the BEN channel workflow, research, Style Packs, manuscripts, source timestamps, history review, code, tests, site source, and durable assets in `d2bb199`.
- Added `/outputs/` to `.gitignore`; local probes, credentials, private config, runtime outputs, and dependencies stayed outside Git.
- Pushed only `origin/main`, advancing it from `0f61e3c` to `d2bb199`. Remote `gh-pages` stayed at `f80a5fa` before and after the push; no publish script or `gh-pages` push ran.
- Verification passed: `git diff --cached --check`, 150 Python tests, repository credential scan, Project Memory check, and three Node review-page tests.

## 2026-08-14 to 2026-08-16 — Foundation and discovery history (compressed)

- Completed the shared Taiwan/US Market Pack, SQLite migrations, immutable Evidence/source governance, TWSE official data path, compliance precheck, realtime source registry, X/YouTube bounded collectors, P03/P04 event clustering, and the initial BEN Radar UI.
- Completed the P01 business/source audit, X account discovery, cost/rights review, and local/public review-surface groundwork. Detailed evidence remains in PROJECT_CONTEXT.md and the earlier repository history.
- This older history is intentionally condensed to keep the append-only work log below the 64 KiB project-memory limit.

## 2026-08-17 — BEN Radar P05-A data-pipeline and stock-signal correction

- Added one auditable pipeline trace row for each of the 80 persisted news records, including structured fetch, normalization, finance gate, entity, mapping, event, ranking, snapshot, drop stage, drop reason, event ID, and market-qualified ticker fields.
- Confirmed the public-news absence was not a fetch failure: 78/80 rows were outside the current 24-hour window; the remaining eligible news reached events but the prior route/exporter applied a double Top-16 truncation.
- Added source-concentration metrics and a relevance-first snapshot selector with a capped marginal repeated-publisher penalty; the published snapshot now has seven publishers, one real news event, Top-1 share 50%, and no concentration warning.
- Added a Taiwan StockSignal layer for 30 real history-backed stocks using latest completed data versus only the prior 20 sessions. Produced 10 public HotStocks, 10 abnormal stocks, rule components, null-preserving data quality, market-qualified IDs, event links, and Evidence provenance.
- Generated all required `research/ben_radar_p05a/` trace/audit/model/integration artifacts plus the two P05-A deliverables.
- Updated and published the stable public Sites version 2 at `https://ben-finance-radar.nels-sedhq.chatgpt.site` while preserving read-only/browser-local behavior.

### Verification

- Real integration: Yahoo奇摩股市, CNBC, and Investing.com stored samples each passed the unified event path at their original audit times; a natural stored-corpus news/X overlap was found without synthetic promotion.
- Full repository check: 80 tests passed in 131.92 seconds; credential scan passed.
- Public Sites build and 2/2 rendered-site tests passed.
- Browser acceptance: public desktop and 390px mobile layouts had no page-level overflow; public and dynamic routes had zero console warnings/errors; `/stock-radar`, `/ai-radar`, and `/radar` all rendered the intended page.

## 2026-08-17 — BEN RADAR Step 2 OFFICIAL DATA CONNECT

- Added migration `013_official_data_connect.sql` for independent official-source permission states, market-qualified securities, unified daily market data, and mapped MOPS disclosures.
- Added a replaceable official-data service for exactly TWSE, TPEx, and MOPS. TWSE uses the official current snapshot and monthly stock history; TPEx uses the official current OpenAPI snapshot and monthly individual-stock JSON; MOPS uses listed and OTC official material-information endpoints.
- Converted TPEx historical thousand-share/thousand-dollar values to the shared share/New-Taiwan-dollar units, preserved raw official rows as immutable Evidence, and added read-only volume-history, disclosure-reverse-lookup, and coverage queries.
- Updated only the TWSE/TPEx/MOPS registry rows to `API_VERIFIED`; internal use, public display, and redistribution remain `UNKNOWN`.
- Bounded live validation stored 1,087 TWSE and 889 TPEx company securities, 1,407 TWSE and 1,202 TPEx daily rows, 33 sessions each for `TWSE:2330` and `TPEX:6488` over 2026-07-01 through 2026-08-17, and 11 MOPS disclosures with 11 mapped securities.
- One duplicate TPEx snapshot rerun was deliberately interrupted and recorded as failed after the prior snapshot had committed; the subsequent history-only validation succeeded for all 20 configured ticker-month requests. No UI, HotScore, K-line, news, X, AI, or content-generation behavior changed.

### Verification

- Targeted official-data/schema/registry/launcher suite: 11 tests passed.
- Python compilation and `git diff --check` passed; full `scripts/check.ps1` passed 84 tests plus credential scan; Project Memory check passed. The memory scanner now continues across unreadable generated cache directories instead of aborting the whole integrity check.

## 2026-08-17 — BEN RADAR Step 2.5 full-market history backfill

- Reused `official_securities` and `official_market_data_daily`; added only history-coverage status fields and did not create a parallel market-data model.
- Added official whole-market/date batch collection for TWSE and TPEx, per-date incremental commits, immutable full-response Evidence, idempotent `(security_id, trade_date)` writes, atomic progress state, retry of recorded failures, and zero-download Resume for already complete dates.
- Completed the recent 40-session target from 2026-06-22 through 2026-08-17. The database retains truthful earlier TPEx fallback facts through 2026-06-17 rather than deleting valid observations.
- Final coverage: TWSE 1,087/1,087 with history and 1,082 at 20+ valid sessions; TPEx 889/889 with history and 886 at 20+ valid sessions; 79,834 total MarketData records.
- Integrity audit: zero duplicate security/date rows, zero EOD rows with null OHLCV, zero negative volume rows, zero invalid/future dates, and zero unmapped security IDs. Seventeen incomplete official TPEx rows remain honestly `UNKNOWN` and are excluded from valid baselines.
- Two transient TPEx HTTP 520 responses were retained in progress state, then recovered through Resume. A final Resume added no requests, collection runs, or MarketData rows.
- No UI, K-line page, HotScore, anomaly algorithm, news, X, AI, translation, or content-generation work was performed.
- Final targeted verification passed: 10 history/official-data/schema tests, Python compilation, `git diff --check`, direct SQLite coverage/integrity queries, and Project Memory check. The unrelated full suite was intentionally not run for this bounded task.

## 2026-08-17 — BEN RADAR Step 3 Anomaly Engine V0.1

- Added `config/anomaly_rules.v0.1.json` with distribution-backed thresholds and business explanations; no thresholds are embedded in UI or template code.
- Added a read-only prior-only Replay engine for `VOLUME_SPIKE`, `RANGE_BREAKOUT_20D`, `RANGE_BREAKOUT_40D`, `PRICE_VOLUME_BREAKOUT`, `QUIET_TO_VOLUME_SPIKE`, and `PRICE_ANOMALY`.
- Ranking uses matched-rule count, price/volume co-signal presence, relative volume, absolute price Z-score, breakout percentage, and stable security ID in that disclosed order. No 0–100 HotScore is produced.
- The 2026-08-17 Replay evaluated 1,080 TWSE and 867 TPEx securities. It excluded 17 without current EOD rows, six with fewer than 20 prior sessions, and six with zero/nonpositive or more-than-30% unadjusted historical price jumps.
- Produced `research/ben_radar_anomaly/anomaly_top20.csv` plus `anomaly_audit.json`, including raw metrics, rule severities, why-selected text, distributions, quality states, and the five requested audit cases.
- Rule counts: 257 volume spikes, 82 20-day breaks, 12 40-day breaks, 56 price/volume breakouts, 14 quiet-to-spikes, 45 price anomalies, and 88 multi-signal securities.
- The audit found no obvious ranking violation under the frozen rules. This is `READY_FOR_HUMAN_REVIEW`, not verified business quality. TWSE has no full prior-40-session coverage for this Replay; TPEx has 782 eligible 40-day baselines.
- Verification: 15 targeted anomaly/history/official/schema tests passed; artifact validation confirmed 20 unique ranked securities, sequential ranks, nonempty explanations, disclosed rules, no future-baseline use, and valid JSON/CSV output.
- No UI, K-line, news, X, AI, translation, HotScore, content generation, or unrelated full-suite work was performed.

## 2026-08-17 — BEN RADAR Step 3.5 anomaly validation

- Used the existing official market/date batch backfill and Resume path to add only ten necessary completed sessions, extending the bounded window to 50 sessions (2026-06-05 through 2026-08-17) and 97,603 MarketData rows.
- Recovered one transient TPEx HTTP 520 through immediate Resume. Final progress is `COMPLETE`, with zero duplicate security/date rows, EOD-null OHLCV, negative volume, invalid/future dates, or unmapped securities.
- Kept `config/anomaly_rules.v0.1.json` unchanged and stored its SHA-256 in the validation audit.
- Added same-market Replay-day volume percentile and LOW/MEDIUM/HIGH liquidity level. Unit tests confirm liquidity changes do not affect the ranking key.
- Replayed 2026-08-14, 2026-08-13, 2026-08-12, 2026-08-11, and 2026-08-10. Each generated a unique 20-row all-market CSV under `research/ben_radar_anomaly_validation/`.
- Prior-40 coverage passed the fixed 95% validation floor on every market/date: TWSE 99.44%–99.72%, TPEx 95.17%–97.46%. Remaining partial cases reflect real no-trade/listing gaps.
- Audit found 159 distinct LOW-liquidity anomaly candidates, 19 low-change but strong volume/breakout Top20 cases, and 16 securities with at least a two-session consecutive Top20 streak. Ticker-prefix co-occurrence remains an explicitly unverified sector lead.
- No obvious systematic error was found in rank order, baseline dates, daily row counts, or liquidity annotations. This supports workbench entry for human review, not production rule verification.
- Verification: 16 targeted anomaly/history/official/schema tests passed; independent artifact checks verified the unchanged config hash, five dates, 20 unique ranked rows per date, required liquidity fields, and PASS audit states.
- No UI, K-line, news, X, AI, translation, HotScore, content generation, PDF, or new source work was performed.

## 2026-08-18 — BEN RADAR Step 4 Stock Workbench V0.1

- Added a read-only `stock_workbench` adapter that runs the frozen Anomaly Engine for the latest six complete Replay dates, maps every stock rule to Chinese, derives current/longest Top20 streaks, and loads real EOD OHLCV plus recent MOPS Evidence without changing rule thresholds or ranking.
- Replaced the legacy stock-signal panel with a compact 20-stock market-anomaly scanner. Every outer card exposes actual shares, 20-day median shares, RVOL, close/change, liquidity, matched rules, explanation, and current streak.
- Added deterministic early-momentum and persistence groups. Neither participates in anomaly ranking.
- Added clickable detail drawers for all 20 stocks with 1M/3M real daily candles, volume bars, prior-20/prior-40 high reference lines, raw metrics, and honest confirmed/unconfirmed catalyst status.
- Re-exported the same new engine payload to the public site and published Sites version 4 at `https://ben-finance-radar.nels-sedhq.chatgpt.site`.

### Verification

- Targeted Python suite: 11 tests passed. Full repository check passed 94 tests plus the credential scan when run with the repository virtual environment. Public Sites build passed and 2/2 rendered-site tests passed.
- Browser acceptance at 1280px and 390px: 20 cards, visible actual volume/RVOL, functional detail chart, no horizontal overflow, no English rule badges on outer cards, and zero page console errors.
- Public URL returned HTTP 200 with `ben-stock-workbench.v0.1`, 20 rendered stock cards, and the 2026-08-17 data date.
- No news/X expansion, AI, HotScore, KOL distillation, or content generation was added.

## 2026-08-18 — BEN Radar remote publication

- Committed the complete runnable BEN Radar dependency chain from P02 through Stock Workbench V0.1 as `af0f478` (`feat: deliver BEN Radar stock workbench v0.1`) and pushed it to GitHub `origin/main`.
- Included code, migrations, governed configuration, tests, BEN Radar acceptance artifacts, reports, and the public-site source. Excluded runtime databases, caches, screenshots, credentials, unrelated YouTube benchmark research, and repository-local experimental skills.
- Pre-push verification passed: 94 Python tests, 2 public-site tests, credential scan, and Project Memory check. The first push encountered a transient TLS handshake failure; the immediate retry succeeded and advanced remote `main` from `e77e65c` to `af0f478`.

- Verification: Windows PowerShell parser passed; static inspection found no secret-persistence calls. No authenticated request was run because the user correctly retained the key locally, so real provider compatibility remains `NEEDS_CONFIRMATION`.

## 2026-08-18 — Ben 20-channel daily-hotspot business analysis

- Converted Ben's supplied recording transcript into a standalone business-requirement draft at `deliverables/BEN_20频道每日热点业务需求分析_2026-08-18.md` without copying the full transcript into Project Memory.
- Defined the product unit as `channel × business date`, with 5–8 explainable candidates, honest shortages, market-session timing, Evidence gates, channel-match reasons, and a 10/30/60-second human workflow.
- Separated 100 daily placements from unique events and documented multi-channel routing. Repository search found no authoritative 20-output-channel profile set; existing stocks, X accounts, realtime sources, and Style Packs were not relabeled.

## 2026-08-18 — GPT proposal review and Channel-driven plan v2

- Read the complete user-supplied GPT proposal and assessed it against Ben's recording, the prior 20-channel business analysis, current code/configuration, source governance, and the dirty-worktree industry-mapping state.
- Produced `deliverables/BEN_Radar_Channel_Driven_最优业务方案_v2_2026-08-18.md`. Retained the proposal's useful product definition, Signal/Topic distinction, EOD-first boundary, deterministic/LLM split, transparent ranking direction, lean technical stack, and human KPI focus.
- Corrected the pipeline to `Evidence -> Signal -> Event -> Topic -> Channel Assignment -> Channel Daily Brief`; changed 3–5 to a 5–8 target with honest shortages; separated source class from epistemic state; bounded LLM authority; and preserved Stock Workbench as a signal/evidence inspector rather than the primary product.
- Replaced the one-channel MVP with a 20-channel audit followed by three contrasting channel archetypes over five historical Replay dates and five live business days. Added explicit gates for 20-channel expansion, source acquisition, United States onboarding, content workflow, and any future realtime-data spend.
- Verified that the proposed Industry Mapping worktree remains uncommitted and outside the Topic path (`NEEDS_CONFIRMATION`); no runtime behavior was changed.

## 2026-08-18 — Codex P06A channel-intake task prompt

- Created `deliverables/CODEX_TASK_P06A_20频道画像审计与三频道试点选择_提示词.md` as the exact task prompt to pair with the user's forthcoming channel attachments in a new Codex task.
- Scoped the task to complete channel inventory, field-level provenance, versioned draft profiles, overlap and data-coverage matrices, three contrasting pilot recommendations, structured Topic Card acceptance examples, business report, and Project Memory verification.
- Added safeguards against invented channels, filled `UNKNOWN`, hard-coded examples, unsupported capabilities, and premature code/Schema/database/source/ranking changes.

## 2026-08-18 — BEN Radar P06A channel-profile audit and pilot recommendation

- Read the user's only supplied channel attachment and reconciled 20 unique channel names with zero duplicates, unidentified rows, or missing names. Preserved the 18-count directory inconsistency, the conflicting category placement of `半導體駭客` and `華爾街溫度計`, and the unresolved 24/7 cutoff for `鏈上顯微鏡` instead of silently correcting them.
- Generated 20 versioned `ChannelProfile v0.1 DRAFT` records. Each retains its complete source block, summary, content forms, audience, update frequency, tags, SEO, cross-category matrix row, brand-family fields, and global risk template, plus field-level `SUPPLIED / DERIVED_FROM_SUPPLIED / PROPOSED / UNKNOWN / CONFLICT` provenance.
- Added one-row-per-channel overlap and current-data coverage matrices. Verified current read-only capability facts: 97,603 TWSE/TPEx EOD rows through 2026-08-17, 11 mapped MOPS disclosures, no ChannelProfile/Assignment/Brief tables, and no applied Industry Mapping tables. Uncommitted Industry Mapping remains `PARTIAL`; US EOD, calendars, adoption history, and feedback remain `NOT_IMPLEMENTED`; news rights and X production status were not upgraded.
- Recommended `資金雷達 / SIGNAL_HEAVY`, `個股顯微鏡 / EVENT_HEAVY`, and `產業透視鏡 / CROSS_ENTITY`, all `RECOMMENDED_PENDING_APPROVAL`, with objections, prerequisites, and alternatives. Generated five Topic Card acceptance examples for each; all 15 are labeled `SCHEMA_EXAMPLE_NOT_REAL_TOPIC`.
- Produced the nine required research artifacts plus `deliverables/BEN_RADAR_20频道画像与三频道试点建议_P06A.md`. Added reproducible generator and validator scripts inside the research directory only.

### Verification

- Dedicated P06A validator passed: 20 profiles and unique IDs, 20 overlap rows, 20 coverage rows, three pilot types, 15 labeled schema examples, and seven material questions.
- Current capability suite passed 19 tests covering official data, Anomaly Engine, the uncommitted Industry Mapping worktree, and Schema. This confirms the files/tests run, not production integration of Industry Mapping.
- Full application tests were intentionally skipped because P06A changed only research, deliverable, and Project Memory files and explicitly prohibited application implementation.

## 2026-08-18 — X reply task workbook through 2026-09-01

- Created `outputs/01a014e6-3700-7b82-8981-9c9d12259957/X回复任务排期_2026-08-18至2026-09-01.xlsx`: 16 accounts, 15 dates, 240 account-day groups, 6,000 task slots, a selected-date dashboard, status controls, and manual-only execution.
- Artifact-tool re-import and four-sheet visual QA passed: every group has 25 rows, the first two days reserve 800 slots, formulas have no matched errors, and the then-unprovided links/replies remained empty.

## 2026-08-19 — Completed 800-row X reply assignment CSV

- Parsed the user's pasted source into exactly 800 ordered X URL/reply pairs, preserving every URL and reply string without generation or rewriting.
- Assigned source rows 1–400 to 2026-08-18 and 401–800 to 2026-08-19. Within each date, the 16 supplied accounts receive 25 consecutive rows each in the supplied account order.
- Created the UTF-8 BOM CSV at `outputs/01a014e6-3700-7b82-8981-9c9d12259957/X回复任务_800条_2026-08-18至2026-08-19_Notion飞书.csv` with auditable task, assignment, status, link, reply, and completion fields.
- Set all rows to `待回复`. No X login, posting, reply automation, or account interaction was performed.

### Verification

- Source validation passed: 800 continuous items, zero duplicate URLs, and zero blank replies.
- Artifact-tool CSV import and saved-file re-import passed. Independent PowerShell `Import-Csv` confirmed 800 rows, two dates, 16 accounts, 32 date-account groups, exactly 25 rows in every group, 800 unique URLs, zero blank replies, correct first/last assignments, and a valid UTF-8 BOM.
- Rendered and visually checked the CSV header plus representative rows; dates, accounts, status, URLs, and reply text were present and legible.

- YouTube: UI 0/4; user text 5 files; no bodies stored.

## 2026-08-19 — Corrected BEN Radar to a post-close channel Top 5

- Corrected the earlier 12:05 assumption: wait for Taiwan close and per-source EOD readiness, then target the same-session brief for 15:00–15:15 Asia/Taipei.
- Defined five ranked, evidence-qualified news/event/topic/stock assignments per channel and market cutoff. Taiwan timing does not govern US, global-macro, or 24/7 crypto channels.
- Each item requires Why Now, Why Channel, Evidence, session/as-of labels, and stock detail. AI may order `1–5`; evidence gates remain authoritative. Late sources retry, and shortages cannot be padded.
- No application, Schema, database, source, scheduler, market-data, ranking, or UI implementation changed. P06B still starts with the three approved pilots.

## 2026-08-19 — Post-close daily run

- 15:10 PASS: 5/5/5; audit 0; public 0e607b8.

- Hotspot review: no runtime change.

## 2026-08-19 — Extracted finance-relevant X following candidates

- Parsed the user-supplied `twitter-正在关注-1784448167852.csv` with 2,150 account rows and preserved the source account fields without rewriting profile text or metadata.
- Selected 67 candidates spanning the existing project account pool, listed-company/product/newsroom accounts, financial media, macro/market research, AI infrastructure, semiconductor, Taiwan supply-chain, and US-stock research. Pure crypto marketing/referral and unrelated generic-AI accounts were excluded.
- Created `outputs/01a019cd-4657-7a90-b9ce-b66b01926538/X关注列表_股票财经AI相关候选账号.csv` with the 23 source columns plus six audit columns: category, suggested use, market scope, confidence, rationale, and matched dimension.
- Added reproducible extractor `scripts/extract_finance_x_following.mjs`; the output remains a candidate list and does not change collection configuration or rights states.

### Verification

- Artifact runtime re-import and preview render completed successfully.
- Independent CSV checks passed: 67 rows, 67 unique handles, zero duplicates, clean UTF-8 BOM headers, all 23 source columns present, all 67 metadata fields nonblank, and zero mismatches against the selected source rows.
- `scripts/project-memory-check.ps1` passed. `git diff --check` passed with only existing LF-to-CRLF warnings.

## 2026-08-20 — Daily 67-account X collection

- Reconciled the supplied 67-account finance/stock/AI candidate file into `config/x_accounts.csv`: 19 core, 40 watch, 8 low-confidence, and 67 unique handles. Controlled endpoint checks showed stale `@ChatGPTapp` returned 404 while `@ChatGPT` returned 200, so the configuration uses the live handle.
- Inspected `trickter/X-HotTopic` commit `6594894` without executing its third-party scripts. Ported the relevant reliability behavior into the existing collector: 4-request/second start limiting, 35-second timeout, three-attempt retry, millisecond `since`, bottom-cursor pagination, ten-page safety limit, and explicit incomplete-run state without advancing the checkpoint.
- Added `scripts/run_daily_x_collection.py` plus PowerShell runner/installer. Each run records per-account results, retries only failed accounts, preserves dated run files and `latest.json`, enables all configured confidence tiers, and reconciles removed accounts without deleting history.
- Removed the 67-account BEN sync from the ten-minute realtime dispatcher and installed `Global X Finance - Daily X Collection` for 14:35 +08 daily. The separate realtime-registry cycle remains unchanged. Updated weekday 15:05 Codex automation `ben-radar` to report and read the 14:35 X batch; enabled optional X input in the three-channel config.
- Preserved all X rows as `OPINION`, original timestamps and URLs, publisher-group/repost semantics, immutable Raw Evidence, and `platform + post_id` deduplication. FxTwitter terms, commercial use, continuity, and SLA remain `UNKNOWN`.

### Verification

- Probe: 66 direct 200 responses plus one stale-handle 404; the corrected handle returned 200. Average response 8.724s, maximum 32.641s.
- First collection: 67/67 complete, 771 fetched, 345 eligible prior-24-hour rows, 344 new posts; immediate rerun had zero duplicates. Task Scheduler returned 0.
- 2026-08-19 X-enabled replay passed with TWSE 1083/1087, TPEx 862/889, 407 X rows, 23 media/X candidates, 5/5/5 output, and zero violations; official Evidence ranked ahead of X opinions.
- Targeted X/channel suites passed 19 tests; full check passed 114 tests plus credential scan, Project Memory, and `git diff --check`.

## 2026-08-20 — BEN Radar daily rule update

- Moved active weekday `ben-radar` from 15:05 to 15:20 Asia/Taipei. The brief reports the 67-account X batch and X-backed/non-backed topics; one bounded supplemental run is allowed, with unresolved same-day X marked `X_DEGRADED` and no stale substitution. No business code, database, public page, Git commit, or publication changed.

## 2026-08-20 — Post-close daily run

- The single required process exited 0 with current-session `PASS`, 1083/1087 TWSE and 867/889 TPEx rows, both MOPS endpoints successful, 5/5/5 channel output, `RULE_BASED_FALLBACK`, and zero violations. All RSS sources ultimately succeeded; Investing.com recovered from one first-attempt `URLError`. The dated payload and local review JSON matched by SHA-256. No X collection, posting, commit, push, or public deployment occurred.

## 2026-08-20 — YouTube transcript batch reconciliation

- Deduplicated `j-zGkkZdcOs`, upgraded P08 to three `老王愛說笑` samples, and added three MacroMicro formats to P10. The repository records nine unique samples (eight complete, one partial); parsing, benchmark, credential, and metadata checks passed.

## 2026-08-20 — Local five-channel preview

- Added the five-channel page, daily EOD build, refresh button, guarded `gh-pages` publisher, and 15:20 automation update. Public commit `8ccf53a` passed external checks; no social posting or model claim.

## 2026-08-20 — Ben YouTube narrative and hook handbook

- Delivered verified Markdown/Word handbooks from nine text and 30 title/thumbnail observations: three structures, eight hooks, five scripts, review guidance, and originality limits. All 23 Word pages passed structure/accessibility/visual checks.

## 2026-08-21 — `收盤夜話` writing-pilot intake

- Replaced the proposed `產業透視鏡` writing pilot with `收盤夜話`; created a provenance-bounded `PROVISIONAL` Style Pack, five-angle/top-three-script contract, source requirements, human-readable implementation plan, and three targeted tests. Existing runtime, public page, and schedule were not changed.

## 2026-08-21 — `收盤夜話` FactPack and editorial pilot

- Added `_market_activity_leaders` to `src/global_x_finance/close_talk_fact_pack.py`. Each daily FactPack now carries up to 40 same-session official EOD leaders with market-qualified IDs, close, price change, change percentage, volume, trade value, transaction count, source ID, and clickable TWSE/TPEx URL. The audit allowlist includes these item-level evidence IDs.
- Rebuilt the 2026-08-20 cash source pack and FactPack (`READY`, `COMPLETE_FOR_CASH_MARKET_BASE`): 40 activity leaders, 50 news leads/5 publishers, 30 X attention leads/16 accounts, and 30 MOPS disclosures. TAIFEX futures/options and securities lending remain unconnected.
- Generated `outputs/ben_channel_daily/2026-08-20/close_talk_editorial.json`: five angles, 15 titles, three Traditional-Chinese drafts (1,636/1,620/1,616 chars), fact/interpretation/unknown separation, checkpoints, and 28 clickable source cards; no promotion or advice.
- Added `scripts/render_close_talk_editorial.py` and generated `outputs/ben_channel_daily/2026-08-20/close_talk_editorial.md` for human reading. `scripts/audit_close_talk_editorial.py` returned `PASS`, `angle_count=5`, and `violation_count=0`.
- Updated the active Codex `ben-radar` automation to 13:35 Asia/Taipei: same-process gate, FactPack, editorial generation/audit/render, then success report. No public editorial publication, social posting, commit, or push.

### Verification

- Targeted close-talk tests: 9 passed; full `scripts/check.ps1`: 128 passed plus credential scan passed.
- Real 2026-08-20 source pack: `READY`, seven cash datasets; editorial audit `PASS`, 5 angles, 0 violations, Markdown render with 28 links.
- Hardened secret scanning so URL slugs are not treated as API keys; added a regression test.

## 2026-08-21 — BEN Radar conversation rule sync

- Synced the existing Codex conversation `BEN Radar 台股每日收盤選題` to the active `收盤夜話` single-channel editorial contract. The thread now records the 13:05 X input / 13:35 main-run timing, 48-hour event window, five ranked angles with 2–3 titles each, top-three full-draft requirement, item-level FactPack source citations, explicit `UNKNOWN`/`SOURCE_PENDING`/`X_DEGRADED` states, and no automatic posting or GitHub Pages publication.
- The sync turn did not execute the daily pipeline; no collection, output, code, database, publication, commit, or push occurred.

## 2026-08-21 — 收盤夜話 daily run stopped at source gate

- X batch passed 67/67 with 355 new posts; the required main command ran once and exited naturally with current-session `PASS`, TWSE 1079/1088, TPEx 878/889, and all nine news sources successful.
- The seven-item cash pack remained `SOURCE_PENDING/INCOMPLETE_REQUIRED`: breadth/turnover was ready, TWSE/TPEx index and flow data were stale or unavailable, and margin endpoints were incomplete. No FactPack, five titles, full drafts, or editorial audit were generated.
- A bounded source-only retry still returned prior-date index/flow data and incomplete margin responses; no stale facts were substituted.

## 2026-08-21 — Same-day BEN content preview publication

- Rebuilt `sites/ben-content-studio/data.json` from the 2026-08-21 brief; publisher validation passed (0 violations, 5 weight topics, 3 pilots).
- Published the labelled preview to `gh-pages` commit `647bde0`; remote verification returned HTTP 200 and date `2026-08-21`. Full `收盤夜話` remains gated.

## 2026-08-21 — Single-channel manuscript surface

- Updated `sites/ben-content-studio/app.js` and its HTML template so the public workbench is explicitly manuscript-first: only `收盤夜話` is rendered, the page title names the manuscript, and each topic action says `看完整文稿`.
- Recorded DEC-034 and refreshed the task/context handoff. The current public JSON still truthfully reports `close_talk_editorial.status=UNAVAILABLE` for 2026-08-21; no other channel or stale manuscript is substituted.
- Targeted page tests and the Project Memory check are required before publication; no public push was performed in this turn.

## 2026-08-21 — Clarified 收盤夜話 source timing and gate

- Verified the live source configuration: X discovery starts at 13:05, Taiwan regular close is 13:30, source polling starts at 13:35, and the configured primary build is 13:50 with a normal 13:50–14:10 delivery target.
- Documented the six official post-close endpoints: TWSE/TPEx index, TWSE/TPEx institutional flow, and TWSE/TPEx margin/short. Current hard gates are same-day EOD coverage plus both index rows; flow and margin remain optional enhancements with explicit `UNKNOWN` on delay/failure.
- Confirmed 2026-08-21: EOD breadth was ready, both index endpoints returned 2026-08-20, institutional data was stale/unknown, and both margin requests failed; therefore no full manuscript was generated.

## 2026-08-21 — Same-day source recheck

- At 15:20 +08, ran one bounded source-only recheck after the scheduled process had exited. TWSE institutional flow had become current, but both index endpoints still returned 2026-08-20; TPEx flow and both margin/short endpoints remained pending. No editorial generation was started and no stale data was substituted.

## 2026-08-21 — Staged 收盤夜話 delivery and late-source fallback

- Changed the close-talk source contract so same-session TWSE/TPEx EOD plus derived breadth are the base gate; index, institutional flow, margin/short are optional enhancement rows with explicit per-endpoint status, date, attempts, and `UNKNOWN` boundaries.
- Added the official dated TWSE `afterTrading/MI_INDEX` fallback when the TWSE OpenAPI is stale, and added `scripts/run_close_talk_enrichment.py` for the 14:45 second search/retry pass. FactPack now accepts a base-ready pack and labels `BASE_DRAFT` versus `ENRICHED_DRAFT`.
- Updated `config/channel_pilots.v0.1.json` to target 13:45 primary build and a 14:45 enhancement poll. Updated Codex automations: `ben-radar` at 13:35 and `ben-radar-14-45` for enrichment/versioned replacement.

### Verification

- Live 2026-08-21 source pack: `base_status=READY`, `enhancement_status=SOURCE_PENDING`; TWSE dated fallback and TWSE institutional flow were current, while margin rows remained pending. No prior-session values were substituted.
- The updated daily command completed with `status=PASS`, same-day non-replay EOD coverage, zero channel violations; FactPack build returned `READY` from the base pack. The enrichment script completed with `ENHANCEMENT_PENDING` and preserved the base path.
- Targeted close-talk/source/style/content tests: 14 passed. Official automation guidance was checked at [developers.openai.com/codex/automations](https://developers.openai.com/codex/automations).

## 2026-08-21 — Published the first same-day `收盤夜話` manuscript

- Built `outputs/ben_channel_daily/2026-08-21/close_talk_editorial.json` from the real `BASE_DRAFT` FactPack and rendered `close_talk_editorial.md` for human reading. The artifact has five ranked angles, three title options per angle, three complete Traditional-Chinese scripts (1,372–1,654 characters), explicit confirmed/interpretation/unknown fields, next-session checkpoints, and 27 clickable source cards in total.
- Added the reproducible generator `scripts/generate_close_talk_editorial_2026_08_21.py`; it reads only the dated FactPack and preserves official/news Evidence IDs. The editorial audit returned `PASS`, `angle_count=5`, and `violation_count=0`.
- Rebuilt `sites/ben-content-studio/data.json` so the existing manuscript-first page contains the same-day editorial. Publisher validation passed, then `scripts/publish_ben_content_studio.ps1 -TradeDate 2026-08-21` published `gh-pages` commit `d416696681af6bf8859634e299d6438bf7231da9`.
- Anonymous remote verification returned HTTP 200 for both the page and `data.json`; remote date is `2026-08-21`, editorial status is `DRAFT_FOR_HUMAN_REVIEW`, and the page title is `BEN 收盤夜話｜每日盤後文稿`. No social post or main-branch push was made.

## 2026-08-21 — Clarified Ben's channel and source requirements

- Ben reviewed the first public `收盤夜話` manuscript and confirmed the general direction is usable. The remaining business requirement is channel differentiation: each channel needs its own language, opening, narrative logic, copy structure, evidence/opinion ratio, title pattern, and ending style rather than a shared generic finance template.
- Confirmed a source UX gap: API/JSON links are technically traceable but are not good Ben-facing verification targets. The next UI/source task must provide direct human-readable article, official announcement, dated dataset/row, X post, or video/transcript links, while retaining raw API URLs as secondary evidence.
- Confirmed the daily topic window: use the newest 24 hours for fresh events and up to 48 hours for context; combine official EOD, announcements/financial reports, news, market reaction, and attention signals; rank hotness separately from ordinary price/volume anomalies; show the draft body character count at the top.
- No source adapter, ranking rule, or UI code was changed in this clarification turn. The next input needed is at least five recent complete scripts for the next channel, with titles/dates and any Ben keep/reject examples.

## 2026-08-23 — Daily run stopped at the build-time gate

- Started the required repository-virtual-environment command exactly once at 12:03 +08 and waited for that process to exit naturally.
- The script returned `WAITING_FOR_BUILD_TIME` for `market_session_date=2026-08-23`; its configured build time was 13:45 +08. The date was also a Sunday, so no trading-session success was inferred.
- No current-day `run_summary.json`, `audit.json`, or `channel_brief.json` was written. The local review JSON remained dated 2026-08-21, so market coverage, MOPS/news endpoint status, channel counts, and ranking were `UNAVAILABLE / NOT_ATTEMPTED` for this run.
- No X collection or retry, posting, Git commit, push, or public publication occurred.

## 2026-08-23 — First-ten channel Style Packs and Sunday collection

- Added `research/ben_radar_first10_style_packs/` with a 15-row inventory (12 transcript samples plus three explicit no-sample rows), 10 channel Style Packs, a Ben-readable review, and a reproducible validator. Seven channels are provisional; `個股顯微鏡`, `產業透視鏡`, and `財報獵人` remain `NO_TRANSCRIPT_NEEDS_SAMPLES`. `資金雷達` and `板塊輪動儀` explicitly retain profile/sample mismatch flags.
- Added `src/global_x_finance/weekend_crawl.py` and `scripts/run_ben_weekend_crawl.py`. Sunday primary/enrichment runs collect human-verifiable 24-hour fresh and 24–48-hour context news, report source concentration and same-day X state, and never claim a Taiwan post-close manuscript.
- Updated `ben-radar` to 13:35 and `ben-radar-14-45` to 14:45 on Sunday through Friday; Saturday is excluded. Weekdays keep the same-session EOD manuscript gates, while Sunday uses the source-only branch. Updated `Global X Finance - Daily X Collection` to the same six-day schedule.
- Diagnosed the 2026-08-23 X task failure as `UNIQUE constraint failed: ben_x_posts.raw_item_id` for distinct posts sharing identical text. Raw Evidence identity now includes `platform + post_id + text`, preserving two distinct posts without weakening immutable evidence or altering historical rows.
- Added actual body character counts to generated scripts and the Ben-facing manuscript header. Source cards now prioritize `human_verification_url` and retain `raw_api_url` as secondary evidence; the editorial audit rejects raw API-only primary links and incorrect character counts.
- Rebuilt the 2026-08-21 local FactPack/editorial/Markdown/site payload from the preserved passing base FactPack. The editorial audit returned `PASS`, five angles, and zero violations. No GitHub Pages publication, social post, commit, or push occurred.

### Verification

- First-ten validator: `PASS`, 10 channels, 7 with transcripts, 3 without, 12 transcript samples, zero violations.
- Targeted tests: 21 X/weekend/style tests passed; weekend primary and enrichment each returned `NEWS_CRAWL_PASS`, 9/9 sources, 126 fresh rows and 74 context rows.
- Real X acceptance after the fix: `PASS`, 67/67 complete, completion ratio 1.0, 76 new/kept posts.
- Full `scripts/check.ps1`: 136 tests passed and the credential scan passed. Editorial evidence verification found 27 human-readable primary links, 18 secondary raw API links, zero raw API primary links, and exact character-count matches for all three full scripts.

## 2026-08-23 — Requested three-channel daily run failed on the Sunday source gate

- Started the exact repository-virtual-environment command once at 15:10 +08, after the configured 13:45 build time, and waited for the same process to exit naturally at 15:25 with code 1.
- The dated `run_summary.json` reports `SOURCE_PENDING_OR_NO_SESSION` for 2026-08-23. All four attempts had TWSE 0/1,088 coverage with `NO_TRADING_DATA` and TPEx 0/889 coverage with `HTTP_403`.
- The TWSE MOPS endpoint succeeded twice with seven rows (seven new on the first call, seven duplicates on the retry). The TPEx MOPS endpoint failed twice with `HTTP_403 Forbidden`.
- The market gate stopped this command before Yahoo Taiwan, Yahoo Finance, Investing.com, or CNBC RSS collection, channel generation, ranking, and audit. Today's `audit.json` and `channel_brief.json` are absent; the local review JSON remains dated 2026-08-21.
- This failed legacy command is separate from the new Sunday source-only crawl, which had already passed. No X collection or retry, automatic posting, Git commit, push, GitHub Pages publication, or stale-data substitution occurred in this run.

### Verification

- Re-read the dated `run_summary.json`, queried this run's MOPS `collection_runs`, confirmed the review JSON date and hash, and confirmed no daily process remained running.

## 2026-08-23 — Republished the Ben-facing `收盤夜話` manuscript

- Published the already-audited 2026-08-21 manuscript surface with body character counts, human-readable verification links, and secondary raw API links to the isolated `gh-pages` branch at commit `ce15058ef17a83c8b84f20e46796cead172c61f2`.
- Anonymous no-cache checks returned HTTP 200 for the page, `data.json`, and `app.js`; the remote payload reports `market_session_date=2026-08-21` and `DRAFT_FOR_HUMAN_REVIEW`, and the new source-link and character-count fields are present.
- No social post, `main` commit, or `main` push was made. The Sunday 2026-08-23 source-only snapshot was not represented as a same-day post-close manuscript.

## 2026-08-23 — Published the first-ten-channel manuscript workbench

- Added `scripts/build_first10_content_studio.py` and `scripts/audit_first10_content_studio.py`. The builder combines the seven transcript-backed Style Packs with the passing 2026-08-23 24/48-hour source snapshot and the audited 2026-08-21 close-talk/EOD artifacts; generated channel prose is normalized to Traditional Chinese while source titles remain unchanged.
- Rebuilt `/ben-content-studio/` as a ten-channel overview. Seven channels expose reviewable content, while `個股顯微鏡`, `產業透視鏡`, and `財報獵人` show honest waiting-sample states. The current artifact has 11 topics, nine full scripts, 51 source cards, exact body character counts, and zero audit violations.
- `暗池雷達` and `期權守門人` explicitly disclose missing original dark-pool prints, options-chain, IV, and OI data; neither claims a directional institutional bet. Daily content-studio writes now preserve the separately dated first-ten workbench until a newer audited snapshot replaces it.
- Updated the publisher gate to require all ten channels, seven ready states, three waiting states, and a passing first-ten audit. Published the isolated `gh-pages` commit `6ec08774114ccb7fb8f444dece25e6a2d80b27ed`.

### Verification

- First-ten audit: `PASS`, 10 channels, 11 topics, nine full scripts, 51 sources, zero violations. Node page test passed; targeted Python tests passed 4/4; publisher `-ValidateOnly` passed.
- Full `scripts/check.ps1`: 137 tests passed and the credential scan passed.
- Browser acceptance passed at 1440x900 and 390x844: ten cards, three waiting states, no card overlap/overflow, responsive one-column mobile layout, exact expanded character count, human-readable sources, and zero console errors.
- Anonymous no-cache checks returned HTTP 200 for the page, `app.js`, and `data.json`; the remote payload reports source snapshot `2026-08-23`, last market session `2026-08-21`, ten channels, seven draft-ready, three waiting, and nine full scripts.

## 2026-08-23 — Published the complete 20-channel manuscript workbench

- Added `research/ben_radar_second10_style_packs/` with a seven-row transcript inventory, ten channel Style Packs, a Ben-readable review, and a reproducible validator. Four channels are transcript-backed and provisional; six profile-only channels remain `NO_TRANSCRIPT_NEEDS_SAMPLES`. Profile/sample drift stays explicit.
- Added `scripts/build_all20_content_studio.py` and `scripts/audit_all20_content_studio.py`, updated the page/publisher/tests, and generated an all-20 `channel_workbench`. The dated snapshot has 20 channels, 11 draft-ready states, nine waiting states, 15 topics, 13 full manuscripts, 19 transcript samples, 62 source cards, and zero violations.
- Fixed mobile horizontal overflow caused by the long Style Pack status in the channel detail header, and added safe wrapping for source links. Browser acceptance passed at 1440x900 and 390x844 with 20 cards, nine waiting states, no overlap or horizontal overflow, a responsive one-column mobile layout, three clickable `全球資金地圖` sources, and an exact 689-character expanded manuscript count.
- Published the isolated `gh-pages` commit `f57968bcf87e62cc61a850735588cb03253fa0e8`. Anonymous no-cache checks returned HTTP 200 for the page, `data.json`, `app.js`, and `styles.css`; the remote payload reports 20 channels, 11 draft-ready, nine waiting, 15 topics, 13 full manuscripts, source snapshot `2026-08-23`, and market session `2026-08-21`.

### Verification

- Second-ten Style Pack validator and all-20 audit: `PASS`, zero violations. Publisher `-ValidateOnly`: `PASS`. Targeted Python tests: 4 passed. Node page test: 1 passed.
- Full `scripts/check.ps1`: 137 tests passed; credential scan passed. `git diff --check` reported no whitespace errors.

## 2026-08-23 — Expanded sources and made every visible channel a five-topic desk

- Added Federal Reserve, SEC, EIA, ECB, and CoinDesk to the weekend discovery layer as optional enhancements while preserving the original nine required sources. Added source classes, coverage tags, structured-data gap reporting, and raised the 48-hour snapshot cap from 200 to 400.
- The live Sunday crawl passed all 14 sources with 139 fresh items, 148 context items, and same-day X `PASS`. Four official enhancement feeds had no items inside the current 48-hour window; no stale row was promoted into a topic.
- Reworked the first-ten/all-20 builders so the 11 manuscript-backed channels each receive exactly five topics. Shared hotspot IDs support legitimate cross-channel coverage, while the audit enforces global uniqueness across every public title option.
- Kept all 20 channel records in the backend artifact but changed the public page to omit `WAITING_FOR_TRANSCRIPT_SAMPLES`. The local payload contains 55 topics, 13 full manuscripts, 40 labelled topic outlines, and 134 source cards; nine sample-free channels remain unrendered.

### Verification

- All-20 audit: `PASS`, 55 topics, 13 manuscripts, 134 sources, zero violations. Targeted Python tests: 8 passed. Node page test and publisher `-ValidateOnly`: `PASS` with 11 public channels and 55 topics.
- Browser acceptance passed at 1440x1000 and 390x844: 11 cards, five topics on every card, nine hidden channels absent, full-manuscript and outline details readable, and no horizontal overflow.
- Full `scripts/check.ps1`: 138 tests passed; credential scan passed. `git diff --check` reported no whitespace errors.
- Published isolated `gh-pages` commit `afbf0cac696172f0b7edb13225fa722e7d1c2d55`. Anonymous no-cache requests returned HTTP 200 for the page, `data.json`, `app.js`, and `styles.css`; final remote browser inspection confirmed the new title, 11 visible channels, five topics on every card, nine hidden channels absent, the `14/14 · 官方4` source summary, and no horizontal overflow.

## 2026-08-23 — Completed all 55 visible manuscripts

- Added channel-specific complete-manuscript blueprints for all 11 transcript-backed channels and filled the 42 previously empty topic bodies from their current facts, explicit unknowns, evidence sources, channel angle, and Style Pack. The 13 existing bodies retained their facts and structure; seven internal production phrases received narrow spoken-language cleanup.
- Tightened the all-20 audit and publication gate to require 55 topics, 55 full manuscripts, at least 600 non-whitespace characters per body, and zero `CHANNEL_TOPIC_OUTLINE` placeholders. Final output has 55 unique bodies, 55 unique primary titles, 134 source cards, a 613-character minimum, a 1,633-character maximum, and a 920.5-character average.
- Updated the page to present every visible channel as `5個選題 · 5篇全文`, fail closed on a missing manuscript, and remove stale outline wording. Added a self-contained favicon so local and public builds no longer depend on a sibling site path.
- Published isolated `gh-pages` commit `cd05592cf7bf1de01e2282d26e23ec963fa5d320`; no `main` commit/push or social publication was performed.

### Verification

- All-20 audit and publisher `-ValidateOnly`: `PASS`, 20 backend channels, 11 public channels, 55 topics, 55 full manuscripts, 134 sources, zero violations. Relevant Python tests passed 21/21; Node page test passed 1/1.
- Full `scripts/check.ps1`: 138 tests passed; credential scan passed. Desktop 1440x1000 and mobile 390x844 browser acceptance passed with 11 cards, no broken images, no horizontal overflow, working channel/detail/dialog interactions, complete text expansion, and hidden sample-free channels absent. Anonymous remote checks returned HTTP 200 for the page, data, script, stylesheet, and favicon; remote browser verification confirmed 55 full scripts and working manuscript/source expansion.

## 2026-08-23 — Rebuilt all 55 manuscripts to duration-based program length

- Replaced the rejected 600-character floor with channel-duration requirements: `收盤夜話` 3,000+, 5–8 minute channels 2,000+, 3–5 minute channels 1,500+, and 3-minute channels 1,200 non-whitespace characters. Existing bodies no longer bypass regeneration.
- Added 11 channel program specifications plus topic-specific transmission analysis for market breadth, memory, shipping, substrates, AI pricing, financing, Taiwan rotation, crypto liquidation, tokenization, exchange/bridge risk, China ADR financing, insurance, retirement ETFs, and related event classes. Every script now includes competing interpretations, explicit missing-data boundaries, scenario tests, and next verification points without inventing absent data.
- Added per-topic duration/minimum/pass metadata, Ben-facing target labels, unique-body and internal-wording audits, per-channel length statistics, and fail-closed publisher checks. The final 55 manuscripts are unique and retain 134 human-verifiable source cards; nine sample-free channels remain hidden.
- Verification: all-20 audit `PASS` with zero violations; targeted tests passed; full `scripts/check.ps1` passed 138 tests and credential scan; publisher validation and `git diff --check` passed; desktop 1440x1000 and mobile 390x844 browser QA found no horizontal overflow or console errors.
- Published only the isolated `gh-pages` branch at `f80a5fa6454a426504e27bb17e1899ee9dc01c35`. Anonymous checks returned HTTP 200 for page, JSON, JavaScript, CSS, and favicon; remote browser confirmed 11 visible channels, 55 manuscripts, and the 3,479-character/15-minute first script. No `main` commit/push or social publication occurred.

## 2026-08-24 — Enabled gated weekday publication for the BEN content studio

- Updated `ben-radar` and `ben-radar-14-45` so a passing weekday base or enriched draft may publish only to isolated `gh-pages`. Both require same-day, non-replay, zero-violation inputs and a no-cache remote date check; social posting and `main` pushes remain forbidden.
- Raised the daily `收盤夜話` contract from three shorter scripts to five complete 3,000–4,200-character manuscripts. The editorial audit now checks every rank.
- Added `scripts/prepare_ben_content_studio_publish.py` and daily workbench synchronization so the dated scripts replace the channel actually rendered by the public page. Tightened the publisher to require the current close-talk date, five duration-passing scripts, a 55-script audit, and an audit fingerprint.
- Verification: targeted tests passed 13/13; full `scripts/check.ps1` passed 140 tests and the credential scan. Python compilation passed. Validation against the legacy three-script artifact failed closed at the new 3,000-character gate, as intended. The 13:05 X task then returned `PASS`, 67/67 complete, 223 new posts, and Windows result 0. No new public commit was made; the latest public version remains `f80a5fa` until a scheduled manuscript run passes.

## 2026-08-24 — 14:45 close-talk enrichment remained pending

- Confirmed Taipei Monday and started the exact repository-virtual-environment enrichment command once at 14:52 +08, without starting phase A or X. Waited for the same process to exit naturally with a nonzero result.
- The dated `enrichment_summary.json` reports `ENHANCEMENT_PENDING` for 2026-08-24. All 14 configured news sources succeeded on the first attempt, but the source pack remained `enhancement_status=SOURCE_PENDING` and `coverage_status=BASE_READY_OPTIONAL_PENDING`.
- Missing or failed current-session datasets were market breadth/turnover, TPEx index, TWSE/TPEx institutional flow, and TWSE/TPEx margin/short. TPEx endpoints returned HTTP 403; unresolved dates remained `UNKNOWN` and no prior-session value was substituted.
- The phase-A `run_summary.json`, `audit.json`, `channel_brief.json`, FactPack, editorial, editorial audit, and render are absent for 2026-08-24. The enhancement gate therefore stopped before editorial regeneration, prepare, publication, or remote-date advancement.
- Anonymous no-cache verification returned HTTP 200 for the public `data.json`, still dated 2026-08-21 at the market, workbench, and `收盤夜話` levels. It retains 20 backend channels, 11 visible channels, 55 topics, and 55 duration-passing manuscripts. Remote `gh-pages` remains `f80a5fa6454a426504e27bb17e1899ee9dc01c35`.
- No social post, `main` commit/push, X rerun, stale-data substitution, or `gh-pages` update occurred.

## 2026-08-24 — Added topic-manuscript contracts and append-only channel reviews

- Added topic-contract v2 to all 55 visible topics: displayed title, core question, five-part channel-specific selection reason, thesis/counter-thesis, script claims, Evidence IDs, and three measurable review checkpoints. The manuscript builder repairs missing coverage and the audit independently recomputes title, reason, claim, and Evidence alignment.
- Added immutable per-channel history snapshots, idempotent fingerprinting, same-date versioning, and append-only outcome updates. Resolved reviews require an observation date and clickable human-verification Evidence; historical titles and manuscripts are never rewritten.
- Added `今日文稿 / 歷史回顧` UI with lazy history loading, original thesis, counter-thesis, checkpoints, review status, measured outcome, and Evidence. Fixed current-topic visibility when switching to history and verified responsive desktop/mobile behavior.
- Updated both BEN weekday automations to archive the current 11-channel workbench before replacement, apply only Evidence-backed review outcomes, and require the 55-topic alignment/history audit before isolated `gh-pages` publication.
- Verification: all-20 audit `PASS` with 55 aligned manuscripts, 11 history entries, and zero violations; 13 focused tests passed; full `scripts/check.ps1` passed 149 tests plus credential scan; Node page test, `git diff --check`, and 1440x1000/390x844 browser acceptance passed. Publisher validation failed closed on the legacy 2026-08-21 editorial's pre-existing sub-3,000-character bodies. No new public commit was made.

## 2026-08-24 — Added visible publication and fetch times to source cards

- Replaced compact Evidence links with source cards placed before the manuscript. Cards show the original title, original publication time, actual fetch time when present, and human-verification/raw links; timestamped values use Taipei time and date-only official rows are labelled as source-data dates.
- Propagated `fetched_at` through weekend news, close-talk news/X/disclosure FactPacks, editorial generation, first-ten builders, and content-studio synchronization. Legacy databases without the news `fetched_at` column remain readable and return an honest null.
- The all-20 audit now requires every public source to have a real publication/fetch/observation date and valid ISO `published_at`/`fetched_at`; it reports `source_time_count`. Added a missing-time regression test and updated both active BEN automations with the same fail-closed gate.
- Verification: 19 focused Python tests, Node page test, and all-20 audit passed with 134/134 timed source cards and zero violations. The full project check passed 150 tests plus the credential scan. Browser checks at 1440x1000 and 390x844 confirmed source cards precede manuscripts, no horizontal overflow, and no console errors. The same-day source gate stayed pending, so no public deployment occurred.
<!--xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx-->
