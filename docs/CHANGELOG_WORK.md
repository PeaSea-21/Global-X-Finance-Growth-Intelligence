# Work Changelog

## 2026-08-17 — BEN RADAR P05-SOURCE-AUDIT

- Audited exactly TWSE, TPEx, MOPS, CNA, Yahoo奇摩股市, 经济日报, MoneyDJ, and DIGITIMES; no other source was added and no Radar UI, score, K-line, AI, content-generation, source configuration, database, or collector was changed.
- Verified current implementation truth: TWSE OpenAPI has 3 configured datasets and 3,362 stored raw rows; Yahoo Taiwan has 40 stored BEN news rows; the other six audited sources have no current collector or stored source rows.
- Performed one bounded live collection test per source. TWSE returned 1,378 JSON rows, TPEx 10,489 JSON rows, MOPS daily disclosures 6 JSON rows, CNA 20 RSS items, Yahoo 50 RSS items, UDN Money 30 unique HTML article links, MoneyDJ 20 unique HTML article links, and the DIGITIMES XML feed returned HTTP 404 with zero items.
- Recorded the rights boundary: only the three official OpenAPI routes are `P0_CONNECT`; CNA and Yahoo are `DISCOVERY_ONLY` because their public RSS grants are noncommercial; UDN Money and MoneyDJ explicitly reject unlicensed commercial automation/data mining; DIGITIMES remains `DO_NOT_AUTOMATE` because the advertised feed failed and full content is licensed/member content.
- Wrote and CSV-validated `research/ben_radar_source_audit/source_audit.csv` with 8 rows and 19 audit fields.

## 2026-08-17 — Production source-acquisition feasibility review

- Inspected the implemented RSS, FxTwitter, YouTube Atom, TWSE OpenAPI, scheduler, source-governance, raw Evidence, and failure-state paths; no collector, schema, database, credential, scheduled task, or public site was changed.
- Verified from current official documentation that TWSE exposes machine-readable OpenAPI endpoints, SEC EDGAR public data APIs require no API key but require identified and fair-access automation capped at 10 requests/second, and X offers the user-post timeline through a pay-per-use official API.
- Verified that Yahoo奇摩股市 and 中央社 publish RSS feeds but describe free usage as personal/nonprofit noncommercial; these feeds therefore remain unsuitable as an assumed commercial/public-product entitlement without permission. Bloomberg Data License and Reuters Connect/API are the production routes for licensed Bloomberg/Reuters content.
- Defined the recommended implementation order: official SEC/TWSE data; official X API; contract-verified Twelve Data market data; licensed Bloomberg/Reuters; then individually authorized Taiwan-media adapters. HTML parsing is a last-resort authorized adapter and must not bypass robots, login, paywall, anti-bot, or access controls.

## 2026-08-17 — Current source inventory audit

- Performed a read-only audit of the BEN news/X tables, unified raw Evidence, configured source registries, and `sites/ben-radar-public/app/radar-data.json`; no collector, database, source configuration, or public site content was changed.
- Confirmed that the published 16-card snapshot contains 18 Evidence items from 3 publishers: Bloomberg `@business` (15), Reuters Business `@ReutersBiz` (2), and TestingCatalog (1). This is the actual public-page source mix, not the 29-account monitoring list.
- Confirmed successful BEN news storage from Yahoo奇摩股市 (40), CNBC (30), and Investing.com (10). Yahoo Finance has 0 valid rows and remains a visible HTTP 429 failure.
- Confirmed 15 of 29 configured BEN X accounts have stored posts. The separate P02 realtime pipeline has collected five X accounts plus the TWSE official YouTube Atom channel, and TWSE OpenAPI has three configured official datasets. SEC EDGAR and Twelve Data remain deferred and inactive.

## 2026-08-17 — Stable HTTPS public BEN Radar snapshot

- Reproduced the screenshot's `503 Tunnel Unavailable` and confirmed both the local 8766 Flask process and LocalTunnel process had been reclaimed after the prior task ended. The failure was infrastructure lifecycle, not page rendering.
- Stopped treating random local tunnels as a deliverable and created `sites/ben-radar-public/`, a separately deployable read-only Sites surface.
- Added `scripts/export_ben_public_site.py` to render the current local `/stock-radar` context without mutation and export a bounded JSON snapshot. The published snapshot contains 16 ranked event cards and original Evidence links from the current database.
- Implemented the Chinese-first radar layout, category/source/sort controls, transparent score dimensions, Evidence expansion, verification checklist, browser-local queue/ignore/notes, JSON/CSV export, mobile layout, and explicit snapshot/non-investment-advice boundaries.
- Generated and validated a site-specific 1200x630 social card, removed the starter skeleton, and added dynamic absolute Open Graph/X metadata.
- Created a public Sites project, pushed the exact committed source, saved version 1, set unauthenticated public access under the user's prior authorization, and published `https://ben-finance-radar.nels-sedhq.chatgpt.site`.

### Verification

- Production build passed. Site tests passed 2/2: server-rendered product content, at least 16 cards, required Evidence/queue/disclaimer text, snapshot data integrity, metadata, and social asset.
- Sites deployment status reached `succeeded`; the deployment URL is HTTPS and no longer depends on local Flask, LocalTunnel, cloudflared, the user's computer, or the current Codex task.
- The hosted surface is a dated snapshot. Local dynamic collection, health, and cluster diagnostics were not exposed as server routes and must not be described as realtime public service.

## 2026-08-17 — Public-link outage diagnosis and LocalTunnel recovery

- Reproduced the user's `ERR_CONNECTION_CLOSED` on the old `fastest-sheets-people-nasa.trycloudflare.com` hostname and confirmed both the previous local Flask process and its foreground tunnel had ended.
- Started the current P04 Flask application on `127.0.0.1:8766` as a hidden background process and verified the local origin continued to serve `/stock-radar` and `/static/demo.css`.
- Tested fresh Cloudflare Quick Tunnels over QUIC and HTTP/2. The tunnel registered, but current network diagnostics showed Cloudflare public TCP 443 and the tunnel transport path were blocked or unreliable, so the generated Cloudflare hostnames were not delivered as working links.
- Installed the bounded LocalTunnel 2.0.2 client after approval and started a hidden background tunnel to the same 8766 origin. The active review URL is `http://ben-finance-radar-0817.loca.lt/stock-radar`.
- Preserved the user's no-authentication approval and did not add a server write API, credential, Cloudflare account, DNS record, or database change. The fallback is explicitly HTTP-only and temporary.

### Verification

- Anonymous HTTP checks returned 200 for `/stock-radar` (71,827 bytes), `/stock-radar/cluster-diagnostics` (369,541 bytes), `/health`, and `/static/demo.css`.
- Parsed public HTML contained the expected `BEN 財經熱點雷達` heading, 16 opportunity cards, 16 collapsed Evidence controls, the selection-queue UI, and the linked radar stylesheet.
- HTTPS remained unavailable from the current machine because its Schannel credential path failed and Cloudflare public 443 was blocked; production sharing therefore remains a separate HTTPS-hosting task.

## 2026-08-16 — Stale local demo diagnosis and launcher recovery

- Reproduced the reported 404: port 8765 returned HTTP 200 for `/health`, `/ai-radar`, and `/radar`, but HTTP 404 for `/stock-radar`.
- Confirmed 8765 belonged to a Python process created at 16:54, before P04, and the existing Cloudflare Quick Tunnel also targeted that stale process.
- Started the current P04 build on isolated port 8766 and verified HTTP 200 for `/`, `/health`, `/ai-radar`, `/stock-radar`, `/radar`, and `/stock-radar/cluster-diagnostics`.
- Updated `scripts/start_demo.ps1` to validate the current radar marker, reuse only a matching build, and choose the first free port among 8765/8766/8767. Updated the app's automatic browser target to `/stock-radar`.
- After the user explicitly approved public exposure of current BEN Radar/Evidence data, created a new unauthenticated Cloudflare Quick Tunnel to 8766 at `https://fastest-sheets-people-nasa.trycloudflare.com/stock-radar`.

### Verification

- Targeted launcher and radar tests: 7 passed.
- Browser verification on 8766: correct BEN title, 16 event cards, local queue marker present, no horizontal overflow, and zero console errors.
- Anonymous public verification: `/stock-radar`, `/health`, `/static/demo.css`, and `/stock-radar/cluster-diagnostics` all returned HTTP 200. The public browser page rendered 16 cards with no horizontal overflow or console errors.


## 2026-08-16 — BEN Radar P04 core validation and boss test instrumentation

- Froze the pre-P04 rolling snapshot and documented the previous 92 raw / 60 eligible / 56-event behavior before changing clustering.
- Built `research/ben_radar_p04/event_cluster_gold.jsonl` from 45 real local Evidence pairs: 6 `SAME_EVENT`, 19 `RELATED_BUT_DISTINCT`, and 20 `DIFFERENT_EVENT`. Added candidate generation, Gold construction, and repeatable benchmark commands.
- Added structured event fingerprints for entity, ticker/company, actor, action, stage, target/object, normalized numbers, geography, theme, time, and source type. Added explainable two-stage candidate and strict recheck decisions with merge/reject diagnostics.
- Added migration `012_ben_translation_summary_cache.sql` and a cache-first translation/summary adapter. Original Chinese is preserved; an optional configured model can retry; current no-model operation uses honest `TRANSLATION_UNAVAILABLE / RULE_FALLBACK` output without fabricating translation claims.
- Reworked event output to expose separate heat and Evidence-quality scores, explicit fact versus market interpretation, DIRECT/SUPPLY_CHAIN/SECTOR/POSSIBLE stock relationships, content angles, verification tasks, translation metadata, stable IDs, and complete Evidence links.
- Added `/stock-radar/cluster-diagnostics`, browser-local `ben-stock-radar.ben-test.v1` timing events, selection-queue persistence, and mobile containment for the `/radar` metrics grid.
- Delivered `deliverables/BEN_RADAR_P04_事件聚类Benchmark.md`, `deliverables/BEN_RADAR_P04_产品验证报告.md`, and the five research/validation artifacts under `research/ben_radar_p04/`.

### Verification

- Final Gold benchmark: 45 pairs, 5 TP, 0 FP, 39 TN, 1 FN; Precision 100%, Recall 83.33%, F1 90.91%. Initial real-error review contained 15 cases; the final benchmark retains 5 three-class errors for further review.
- Rolling validation moved from 93 raw / 61 eligible / 59 events at 20:39:41 +08:00 to 93 raw / 60 eligible / 58 events at 21:03:08 as the strict 24-hour window advanced. Both snapshots retained 1 multi-item, 1 multi-publisher, and 1 news+X event; Top-20 Chinese title and summary coverage stayed 20/20.
- Targeted P04 suite: 18 tests passed. Full suite: 75 tests passed in 81.39 seconds. The first combined check then correctly found its own synthetic-token fixture because Windows flattened the requested absolute Pytest temp path into the repository; after deleting that exact generated directory, the standalone credential scan passed.
- `scripts/project-memory-check.ps1`, credential scan, and `git diff --check` passed; the latter reported only existing LF-to-CRLF warnings.
- Browser acceptance covered `/stock-radar`, all/news filters and sorting, local queue persistence, cluster diagnostics, `/radar`, and a 6-hour AI view at desktop and 390px mobile widths. No final horizontal overflow or console error remained; Evidence stayed collapsed by default.
- Human Ben 10/30/60-second tests were not simulated and remain `尚未执行`.

## 2026-08-16 — BEN Stock Content Radar

- Rebuilt the primary radar as a Chinese-first editorial opportunity page inspired by xgrowth.tools' lifecycle and topic organization without copying its brand or code. Added `/stock-radar` as a compatible read-only route while preserving `/ai-radar`.
- Replaced 2H/24H and the old three-column analysis card with 24H/12H/6H, all/TW/US/AI/macro/other categories, news/X filters, and heat/growth/discussion/latest/market-impact sorts. Added concise summary cards, compact single-column events, stock tags, bounded market response, content opportunity formats/angles, and default-collapsed Evidence.
- Made homepage titles Chinese-first. Original Chinese is shown when valid; English receives a deterministic rule title when supported or `中文摘要生成中` when not. Original English and full URLs remain unchanged inside Evidence and are not presented as AI translations.
- Expanded entity aliases and boundary matching, event actions, and finance topics. Added tiered link/entity/action/topic/time/text clustering, stable event IDs, engagement-snapshot velocity/acceleration, trend states, score dimensions, and cluster-quality diagnostics. Rejected a temporary 0.08 entity+action threshold after it merged unrelated NVIDIA investment stories; the accepted threshold is 0.16.
- Audited rolling real data twice. The starting snapshot had 92 raw items, 84 eligible events, no multi-item clusters, and no cross-platform event. A later snapshot had 94 raw items, 63 eligible finance items, 59 events, 2 multi-item clusters, 0 multi-publisher confirmations, and 0 news+X events. No synthetic confirmation was created.
- Added versioned local topic-queue state (`ben-stock-radar.topic-queue.v1`) with queue, ignore, notes, restore, and JSON/CSV export. CSV export guards formula-leading values. No database or unauthenticated server write path was added.
- Moved Yahoo Finance endpoint diagnostics and current Ben news-source run state from the editor homepage to `/radar`.
- Delivered `deliverables/xgrowth.tools_股票方向横纵分析报告.md` and a rendered/visually inspected nine-page `output/pdf/xgrowth.tools_股票方向横纵分析报告.pdf`.

### Verification

- Targeted clustering/page suite: 13 tests passed.
- Full `scripts/check.ps1`: 70 tests passed in 66.25 seconds; credential scan passed. One pre-existing credential-scan test fixture was relabeled `synthetic_` so the repository scanner recognizes it as test data while the unit still verifies detection.
- `scripts/project-memory-check.ps1` and `git diff --check` passed; Git reported only existing LF-to-CRLF warnings.
- Browser acceptance at 1280px and 390px: no page-level horizontal overflow, Evidence collapsed by default and safe when expanded, local queue state and note reveal worked, and console errors/warnings were empty.
- PDF rendered through Poppler to nine PNG pages; all pages were visually inspected with no clipping, overlap, or unreadable text.

## 2026-08-16 — CODEX TASK P03C-LEAN

- Validated `config/x_accounts.csv` as exactly 29 accounts: 16 core, 12 watch, and 1 low-confidence account. Added migration `011_ben_x_intelligence.sql` for account state, per-run results, immutable X post links, engagement snapshots, localization cache, and endpoint diagnostics.
- Added one bounded FxTwitter v2 timeline collector with four-request maximum concurrency, jitter, identifiable User-Agent, priority-aware 10/30/60-minute due state, 120-second incremental overlap, one-retry ceiling, HTTP 204/no-new handling, 429/Retry-After/5xx handling, and `platform + post_id` idempotence. Reused the existing P02 scheduler and did not add another Windows task.
- Preserved original X text, authorship, timestamps, URLs, engagement, account role/priority, entities, quote/repost relationships, raw payload, and Raw Evidence. Pure reposts remain stored but do not increase independent-source counts; required same-owner handle groups map to `nvidia`, `openai`, and `anthropic`.
- Replaced the page's separate news-only cards with deterministic unified events using normalized links, entity-plus-action evidence, time proximity, and publisher-group deduplication. Added normalized engagement-velocity X scoring, early-signal treatment, financially relevant filtering, strict original-time 2H/24H views, and all/news/X filters.
- Added a default Traditional-Chinese and optional Simplified-Chinese UI using OpenCC. Original news titles and original X posts are not converted or overwritten; unavailable English translations remain explicitly unavailable.
- Performed one controlled GET for each required Yahoo Finance URL with exact HTTP metadata. Both returned HTTP 429, no Retry-After, `Server: ATS`, `text/html`, one attempt, and final status `DEGRADED_RATE_LIMITED`. Yahoo奇摩股市 remains a separate successful source while both share publisher group `yahoo`.
- Generated `deliverables/Ben_radar_x_intelligence_full_page.png` from the final Traditional-Chinese page after removing horizontal overflow.

### Verification

- Real 29-account run: 11 `SUCCESS`, 18 `NO_NEW` (HTTP 204), 0 failed; 42 X posts saved, 2 reposts retained but excluded from independent-source counts. At 2026-08-16 17:00 +08, strict windows contained 4/41 X posts and 0/52 news rows for 2H/24H respectively; the 24H unified view contained 85 events, 33 with X, and 0 cross-platform confirmations.
- Real `cmd.exe` execution of `启动台湾Demo.bat` exited 0 and reused the running local Demo.
- Browser acceptance: Traditional/Simplified switching and all/news/X filters worked; original content remained unchanged; both news and X cards rendered; horizontal overflow was removed; console errors were empty.
- Targeted suite: 25 tests passed (`test_x_intelligence`, `test_ai_market_radar`, launcher, and P02 scheduler regressions). Credential scan and `git diff --check` passed.

## 2026-08-16 — CODEX TASK P03B-LEAN

- Replaced the first Ben page with a lean evidence-first V2: six top metrics, 2H/24H real-news views, top-20 deduplicated event candidates, short Chinese summaries, original links, transparent ranking reasons, and deterministic rule analysis.
- Ran one real bounded collection across exactly four configured candidates. Yahoo奇摩股市 returned 40 valid items, Investing.com 10, CNBC 30, and Yahoo Finance failed both attempted feeds with HTTP 429. Only successful rows were saved; no fallback or synthetic news was generated.
- Added append/cache tables for news runs, immutable news rows, and TWSE daily stock history. Built a 30-stock demo pool and obtained at least 21 official sessions for all 30 stocks.
- Added explainable 20-day anomaly rules. The accepted snapshot produces 7 displayed anomalies: 5 relative-volume cases, 4 breakout/breakdown cases, and 4 price/volume resonance cases. Volume is shown in lots/萬張; transaction value is secondary and formatted in TWD hundred-millions.
- Reduced the primary navigation to AI市場雷達, 2H/24H熱點, 個股異動, and 智能分析. Removed the first-version feedback controls and raw long integers from the page while preserving all old routes and P02 monitoring data.
- Deferred K-line rendering because the requested core priorities were complete and the task explicitly placed it behind source, history, anomaly, and analysis quality.
- Generated `deliverables/Ben_market_radar_v2_full_page.png` from the final rendered page.

### Verification

- Current windows: 2 real articles in 2 hours, 53 real articles in 24 hours, and 20 displayed deduplicated/ranked event candidates.
- Browser: 24-hour and 2-hour views returned meaningful content; 20 event cards and 7 anomaly cards rendered; no feedback controls, long raw number `54418832121`, framework error, or console error was present.
- Final targeted P03B/P02 regression suite: 16 tests passed. Credential scan, Project Memory check, and `git diff --check` passed.

## 2026-08-16 — Temporary Cloudflare Quick Tunnel

- Verified the existing local Demo health and `/ai-radar` routes returned HTTP 200 before exposing them.
- Retrieved current Cloudflare official Quick Tunnel guidance and downloaded official `cloudflared` 2026.8.2 to the Windows temporary directory only.
- Started an account-less Quick Tunnel from a random `trycloudflare.com` hostname to `http://127.0.0.1:8765`; no Cloudflare token, account login, DNS record, custom domain, application code, database, or repository runtime configuration was added.
- The public radar URL is `https://without-champion-louisville-touch.trycloudflare.com/ai-radar`; access is unauthenticated and therefore intentionally available to anyone who receives it while both local processes remain running.
- Cloudflare connectivity pre-checks passed DNS, QUIC, HTTP/2, and API reachability. Anonymous public checks returned HTTP 200 for the radar page, health endpoint, and radar CSS; expected page title/TWSE content and theme CSS were present, and no Access login page was returned.
- This is a temporary demo endpoint with a random hostname and no uptime guarantee. Stopping the local Demo, stopping `cloudflared`, closing the host machine, or losing connectivity will make it unavailable.
- Revalidated the same unauthenticated URL at 19:46 +08 after P03C: `/ai-radar`, `/health`, and `/static/demo.css` all returned HTTP 200; the radar title was `AI市場雷達｜Ben Radar X Intelligence` and health reported `status=ok`, `market=TW`.

### Verification

- Public `/ai-radar`: HTTP 200, expected AI市場雷達 and TWSE content present.
- Public `/health`: HTTP 200 with `{"market":"TW","status":"ok"}`.
- Public `/static/demo.css`: HTTP 200 with the AI radar theme present.

## 2026-08-16 — CODEX TASK P03-QUICK

- Added `AI市場雷達` to the existing local Demo navigation and implemented `/ai-radar` in Traditional Chinese with a scoped dark finance-terminal presentation.
- Built a 50-security rectangular treemap from the latest real `LISTED_SECURITY_DAILY_TRADING` rows; rectangle area follows official trade value and color follows a calculated daily change percentage. Every tile opens its immutable Raw Evidence.
- Reused current official signal cards to display 16 short move cards across trade value, trade volume, daily change, and official industry-level foreign-holding data. Missing foreign-holding dates remain `UNKNOWN`.
- Reused the non-backfill P02 two-hour feed, preserved `OPINION`, source account, published time, and original link, and applied only conservative rule-based categories and excerpts.
- Kept tail risk empty because current Evidence did not support a major alert; no synthetic event was created.
- Generated 10 evidence-linked research candidates from transparent official rules and labeled the reasoning `FACT`, `AI_INFERENCE`, and `RULE_BASED`; no model API or investment recommendation was used.
- Added browser-local Ben feedback toggles and JSON/CSV export without changing the database.
- Added a truthful United States empty state (`美國資料源待接入`) with zero heatmap rows.
- Added regression tests for trade-value area sizing, previous-close percentage calculation, navigation, Taiwan empty handling, and US no-fake-data handling.
- Generated `deliverables/Ben_AI_market_radar_full_page.png` from the locally rendered page.

### Verification

- Real Demo snapshot: 50 heatmap securities, 16 move cards, 1 recent two-hour item, 0 supported tail-risk alerts, and 10 research candidates; latest official trading date 2026-08-14.
- Browser acceptance: Taiwan and US switches rendered correctly, feedback toggled locally, US contained zero heat tiles, and console errors were zero.
- Real `启动台湾Demo.bat` execution returned exit code 0, reused 3,362 normalized rows and 132 signal cards without duplication, detected the running current Demo, and opened the browser.
- Final repository check: 60 tests passed in 82.82 seconds; credential scan passed. Project Memory integrity check passed.

## 2026-08-16 — CODEX TASK P02 supplemental governance acceptance

- Separated `identity_verified`, `endpoint_verified`, `monitoring_method_verified`, `terms_status`, `commercial_use_status`, `monitoring_status`, and runtime outcome in the registry, database, collector, CLI, and source-health page.
- Restricted `monitoring_status` to `ACTIVE`, `MANUAL_ONLY`, `NEEDS_VERIFICATION`, or `BLOCKED`; public reachability no longer substitutes for terms or commercial-use authorization, and unresolved rights remain visibly `UNKNOWN`.
- Added migrations `008_source_governance_separation.sql` and `009_realtime_active_rights_guard.sql`, including guards that prevent ACTIVE when identity/endpoint/method are not verified or rights are explicitly manual-only/blocked.
- Labeled the single TWSE YouTube channel as “初始验证覆盖” and explicitly rejected “台湾 YouTube 覆盖完成”.
- Real scheduled operation exposed a sequential-source minute split. Fixed due-time advancement to use one cycle-level minute anchor and added a regression test.
- New final Windows cycles at 12:38/12:48/12:58 +08:00 returned task result 0 with 6/6, 5/5, and 5/5 due-source success. The last cycle created one new immutable X Evidence row and 89 exact duplicates.
- The one post-baseline item was published at 04:51:47 UTC and discovered at 04:58:34 UTC, producing a real 6.785-minute sample and current 6.79-minute average. It is one sample, not a sustained SLA.
- Refreshed the verified X/YouTube CSVs, three-cycle evidence CSV, coverage report, nontechnical guide, boss script, README, and browser screenshot.

### Verification

- Full repository check: 57 tests passed in 55.97 seconds; credential scan passed.
- Browser acceptance: `/radar` and `/radar/feed` rendered the six separated states, the YouTube initial-coverage boundary, the new OPINION row, Raw/original links, and 6.8-minute latency with no console warnings or errors.
- Project Memory integrity check passed after the final task, decision, changelog, and handoff refresh.

## 2026-08-16 — CODEX TASK P02 final scheduled acceptance

- Completed three clean scheduled cycles after fixing issues exposed by real Windows operation: completion-time drift, runner exit ordering, and the default battery-power skip policy.
- Cycle 1 at 10:23 +08:00: Windows result 0, 6/6 due sources succeeded, 0 new Raw Evidence, 105 exact duplicates.
- Cycle 2 at 10:33 +08:00: Windows result 0, 5/5 due X sources succeeded, 0 new Raw Evidence, 90 exact duplicates; YouTube correctly remained not due.
- Cycle 3 at 10:43 +08:00: Windows result 0, 5/5 due X sources succeeded, 0 new Raw Evidence, 90 exact duplicates; YouTube correctly remained not due.
- Preserved all diagnostic history. No active source has a failure state; 105 radar items map one-to-one to 105 Raw Evidence rows and all remain `OPINION`.
- Added final verified-source CSVs and `deliverables/三周期实测_P02.csv`. The supplied 43-channel document audit remains entirely candidate-only and did not create false ACTIVE channels.

### Verification

- Full repository check: 53 tests passed in 70.31 seconds; credential scan passed.
- Live UI acceptance: `/radar` and `/radar/feed` returned HTTP 200 with meaningful content and no error overlay.
- Current task state: last run 2026-08-16 10:43:39 +08:00, result 0, next run 10:53:38 +08:00.

## 2026-08-16 — Git repository initialization and GitHub publication

- Created the first Git history baseline from the current reviewed repository contents.
- Standardized the local default branch as `main` and connected `origin` to `PeaSea-21/Global-X-Finance-Growth-Intelligence`.
- Preserved `.gitignore` exclusions for runtime databases, logs, local environments, credentials, caches, and generated ZIP archives.
- Published the repository to the empty public GitHub destination requested by the user.

### Verification

- Full project check passed before publication: 53 tests passed in 95.39 seconds and the credential scan passed.
- Project Memory integrity check passed after the Git metadata update.
- Local `main` and `origin/main` were verified at the same commit after push.

## 2026-08-16 — Standalone project logic and source-cost brief

- Created `deliverables/项目整体逻辑与数据源成本说明.md` as a self-contained Chinese Markdown brief.
- Documented the implemented source-governance, TWSE, X, YouTube, Evidence, normalization, scheduler, health, and local UI flow.
- Separated current zero-direct-fee operation from permanent availability, platform-policy, copyright, reuse-right, and commercial-authorization claims.
- Included the audited runtime snapshot, explicit missing capabilities, production risks, and prioritized next steps.
- Did not modify application code, schemas, source configuration, databases, scheduled tasks, credentials, or integrations.

### Verification

- Markdown file verified at 13,575 bytes / 298 lines; title, Mermaid diagram, source links, risk section, and referenced repository paths were present.
- Project Memory integrity check passed. Application tests were not rerun because this task changed documentation only.

## 2026-08-16 — Data-source, runtime, and cost audit

- Traced the implemented flow from the Windows launcher and scheduler through source governance, TWSE collection, realtime X/YouTube collection, immutable Evidence storage, normalization, rule cards, health state, and the local Flask UI.
- Confirmed the automatic upstreams are three TWSE OpenAPI datasets, five X account timelines through xHotTopic's third-party FxTwitter adapter, one public YouTube Atom feed, and six manually refreshed X policy pages; the remaining registered news/regulatory sources are manual, blocked, or awaiting terms/technical review.
- Confirmed there is no AI model call, model provider, relay, automatic content generation, or publishing integration in the runtime.
- Verified the Windows task `Global X Finance - Taiwan Realtime Radar` is installed and returned exit code 0 on its latest observed run. The demo database contained 1,786 raw items, 1,681 normalized official items, 66 official rule cards, 105 radar items, and 24 radar runs at audit time.
- Verified TWSE Swagger exposes the configured public endpoints without an API security scheme, FxTwitter is called without a credential, and the YouTube Atom feed is called without a Data API key. These currently create no upstream API bill, but do not establish permanent availability or commercial-use rights.
- Verified current official X API pricing is pay-per-use and current X developer guidance requires the official API. The third-party FxTwitter path is therefore a prototype continuity/policy risk, not a production-grade free entitlement.
- Did not modify application code, schemas, source configuration, databases, scheduled tasks, credentials, or network integrations.

### Verification

- Read-only source/configuration/code inspection completed.
- Live scheduled-task and read-only SQLite status queries completed.
- Source registries validated: 17 foundation rows with 1 `API_VERIFIED`; 23 radar rows with 6 `VERIFIED_ACTIVE`.
- Project Memory integrity check passed. Targeted collector/radar tests passed: 13 tests in 15.07 seconds using the system Python; the runtime-only `.venv` does not currently include the optional `pytest` development dependency.

## 2026-08-14 — GitHub X-growth and interaction workflow scan

- Reviewed current public GitHub projects covering the X recommendation algorithm, algorithm-derived growth playbooks, X-specific growth/writing/reply Skills, watchlist-driven reply drafting, human-in-the-loop social-media agents, scheduling, collaboration, and analytics.
- Identified the most reusable pattern for this project as `official/TWSE signal + X watchlist -> early-mover topic score -> EvidenceBundle -> original/reply/quote/thread drafts -> human approval -> manual publish record -> 1H/6H/24H feedback`.
- Determined that the existing YouTube workflow and a new X-native workflow should share one research/Evidence layer but use separate packaging and timing: X for immediate conversation and topic discovery; YouTube for later explanatory depth and authority.
- Verified X's April 2026 automation rules prohibit non-API website scripting and automated likes, restrict unsolicited automated replies, and require prior written approval for AI-powered automated reply bots.
- Did not install third-party Skills, configure X credentials/OAuth, change collection configuration, enable posting/interaction, or modify core code, schema, or databases.

### Verification

- GitHub repository pages, licenses, README workflows, and current X official automation/authenticity policies were checked from public primary sources.
- Project Memory integrity check run after the documentation update.

## 2026-08-14 — Taiwan-stock X account landscape scan

- Researched publicly discoverable X profiles and recent public engagement snapshots for Taiwan-stock, semiconductor, AI supply-chain, market/quant, and adjacent sentiment accounts.
- Separated recently rising/new-generation accounts from long-running popular accounts and mapped the shortlist to the Taiwan Market Pack's existing topic hypotheses.
- Treated follower counts, views, biographies, and third-party public mirrors as time-sensitive discovery evidence, not as verified collection authorization or investment evidence.
- Confirmed `x_sources` and `local_kols` remain empty; did not add accounts to configuration, automate collection, publish content, or modify core code, schema, or databases.

### Verification

- Repository search confirmed there was no pre-existing Taiwan-stock X blogger pool to preserve or extend.
- Project Memory integrity check run after the documentation update.

## 2026-08-14 — CODEX TASK P01 product pivot audit

- Changed the documented primary direction to a human-operated finance content supply workbench; preserved advertising compliance as a non-priority existing capability.
- Audited actual Global X Finance code, configuration, databases, source registry, tests, and runtime output without changing core code or schemas.
- Audited both local xHotTopic copies and the live `PeaSea-21/xHotTopic` remote. Verified the functional source trees match locally, while the two Git histories/remotes differ.
- Inspected xHotTopic timeline collection, raw snapshot/manifest behavior, topic linking, heat scoring, evidence screening, cache, usage accounting, dashboard, scheduler code, tests, and the last real output.
- Confirmed no xHotTopic Windows scheduled task or live snapshot currently exists; the latest complete output is 2026-08-03 and has `partial` coverage.
- Ran a bounded five-account FxTwitter adapter test: 5/5 requests succeeded with 1.150–1.888 second request latency. Recorded the third-party and small-sample limitations; did not claim end-to-end real-time monitoring.
- Produced `deliverables/产品方向切换与现有能力审计_P01.md`, `deliverables/台湾信息源覆盖矩阵_P01.csv`, and `deliverables/X监控实测_P01.csv`.
- Designed five original Style Pack v0.1 positions, a unified content-draft contract, 1H/6H/24H feedback contract, a 10–15-person workflow, and a 10-workday integration plan.
- Marked the missing human+AI workflow, copy workflow, and five-account screenshots/history/views as `NOT_PROVIDED`; did not invent them.

### Verification

- xHotTopic validation succeeded; 72 unit tests passed and `compileall` passed.
- Global X Finance full check passed: 45 tests passed in 67.03 seconds; credential scan passed.
- Project Memory integrity check passed.
- P01 changed documentation/deliverables and Project Memory only; no core application code or database was modified.

## 2026-08-14 — Provider and relay audit

- Searched the repository for relay, proxy, model-provider, API-base, and model-call configuration without exposing credentials.
- Confirmed the project contains no AI model integration or third-party relay; its configured upstreams are TWSE official OpenAPI endpoints and X official policy pages.
- Confirmed the local Codex configuration selects OpenAI `gpt-5.6-sol` and does not define a custom `model_provider`, `base_url`, or `api_base`.
- No business code, schema, endpoint, credential, or model configuration was changed.

### Verification

- Repository-wide configuration/source search completed.
- Project Memory integrity check run after the documentation update.

## 2026-08-14 — CODEX TASK C01

- Added migration `004_x_ads_policy_precheck.sql` for append-only policy version metadata, snapshot-linked structured rules, and versioned Taiwan/United States checklist templates.
- Registered and fetched exactly six X official policy pages from `business.x.com`; stored raw HTML, exact SHA-256, fetched time, summary, verification state, and supersession links without overwriting history.
- Added 26 traceable policy rules covering global prohibitions, finance/crypto restrictions, Taiwan/United States requirements, X pre-authorization, account eligibility, verification, Bio URL, landing pages, disclosures, deceptive claims, review evasion, and sensitive events.
- Added separate Taiwan/United States financial and crypto checklist templates with all unknown facts preserved as `UNKNOWN`.
- Added fail-closed precheck logic with only four results: `PASS_PRECHECK`, `REVIEW_REQUIRED`, `BLOCKED`, and `UNKNOWN`. Internal pass wording explicitly disclaims guaranteed X approval and formal legal advice.
- Added `/compliance`, policy/rule/checklist history views, official Evidence links, Markdown/CSV deliverables, and `deliverables/x-ads-policy-compliance-demo-v0.1.png`.
- No ad content was generated, no X certification was requested, and no campaign was submitted.

### Verification

- `data/mvp.db`: 6 official snapshots, 26 structured rules, 4 active checklists.
- `data/taiwan-demo.db`: 12 append-only snapshots from two verified six-page fetches, 52 historical rule rows, 4 active checklists; latest six-page view contains 26 rules.
- Browser acceptance: meaningful content, four checklist cards, 12 snapshot-version rows, 38 official X links, no error overlay, no console warnings/errors, and working home navigation.
- Targeted policy/compliance suite: 17 tests passed.
- Final repository check: `45 passed in 69.83s`; credential scan passed. Project Memory integrity check also passed.

## 2026-08-14 — X promoted-policy status audit

- Verified that the repository retains official URLs for X Financial Services and Deceptive and Fraudulent Content policies, but does not contain policy text, a rule-by-rule review, or a policy-fetch implementation.
- Confirmed read-only that both `data/mvp.db` and `data/taiwan-demo.db` contain zero rows in `policy_snapshots`.
- Confirmed the existing implementation is only a fail-closed safeguard: a promoted draft cannot receive `PASS_PRECHECK` while product or advertiser-license facts are missing.
- No finance business logic, schema, collector, content-generation, or publishing behavior was changed.

### Verification

- Repository-wide text and filename search completed for promoted/advertising/compliance terms and X policy domains.
- Project Memory integrity check run after the documentation update.

## 2026-08-14 — CODEX TASK 00.5

- Audited the referenced `liewcf/project-memory` repository without executing its scripts: reviewed the MIT license, skill instructions, install guidance, all shipped Python scripts, and test coverage including symlink/out-of-root protections.
- Confirmed the upstream scripts contain no network upload, secret harvesting, credential reads, or subprocess behavior; noted that upstream installation targets a user skill directory and that its setup can create/update or migrate files inside the target project.
- Created the repo-local `.agents/skills/project-memory/` skill using the official skill initializer; did not install it globally.
- Added `AGENTS.md` with mandatory task-start and task-end memory protocols.
- Added `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/CHANGELOG_WORK.md`, and `docs/HANDOFF.md` from current repository evidence.
- Added `scripts/project-memory-check.ps1` to check required files, handoff timestamp, protocol markers, size limits, and obvious credential patterns.
- Did not modify migrations, database Schema, collector behavior, content generation, publishing, or other finance business logic.

### Verification

- Pre-change full repository baseline on 2026-08-14: `26 passed in 21.33s`; credential scan passed.
- Existing delivery drift found: `deliverables/汇报摘要.md` reports 17 tests, while the current test suite actually runs 26. The delivery file was preserved and the mismatch was recorded for a later explicitly scoped task.
- Final Project Memory check passed: 7 required files found; protocol, timestamp, size, and obvious credential checks passed.
- Final full repository check passed: `26 passed in 13.70s`; credential scan passed.

## 2026-08-14 — CODEX TASK 03

- Added migration `003_normalized_signals.sql` for explicit normalized TWSE fields, entity keys, and auditable official signal cards.
- Added an idempotent TWSE normalization service for listed-security daily data, market-index close data, and foreign-holding data. Missing fields remain `UNKNOWN`; raw official strings and Raw Evidence are preserved.
- Added entity mappings and four transparent daily card types: top-10 trade volume, top-10 trade value, top-10 absolute daily change rate, and official foreign-holding ratio rows.
- Added `/signals` with date filtering, security-code search, 24-card pagination, freshness status, formula version, calculation basis, risk notice, Raw Evidence link, and official URL.
- Updated the dashboard, Windows launcher, README, nontechnical guide, boss demo script, report summary, and v0.3 screenshot.
- Removed the one-click launcher's dependency on optional Windows IANA `tzdata` by calculating Taiwan freshness with its year-round UTC+08:00 offset; added a regression test.

### Verification

- Real database: 1,681 normalized records, 1,681 entities/item links, and 66 cards (10 + 10 + 10 + 36).
- Exact-field audit: 1,378 listed-security records compared with official Raw JSON; 0 mismatches across code, name, OHLC, volume, value, and change.
- Idempotence: second normalization created 0 normalized rows and 0 cards.
- Browser acceptance: home freshness, 66-card listing, 24-card first page, 3 pages, 30 dated cards, 36 `UNKNOWN`-date cards, code search for 2330, and Evidence JSON back-link verified.
- Automated suite: 30 tests passed; credential scan passed.
- Windows one-click launcher completed successfully after the timezone compatibility fix and reused all 1,681 normalized rows and 66 cards without duplication.

## 2026-08-14 — Windows double-click launcher repair

- Reproduced the user-reported failure through the real Windows `cmd.exe` path. The UTF-8 Chinese batch body was misparsed and truncated the repository path at its space.
- Replaced the outer `.bat` body with ASCII-only commands, quoted `%~dp0` paths, explicit working-directory setup, PowerShell availability checking, and a paused failure state.
- Removed remaining optional IANA `tzdata` dependencies from the dashboard and ROC-date collector by using Taiwan's year-round UTC+08:00 offset.
- Strengthened the launcher test so the outer batch must be ASCII-decodable and retain quoted paths and failure pause behavior.

### Verification

- Real hidden `cmd.exe` launch succeeded and `/health` returned `status=ok`, `market=TW`.
- Homepage returned HTTP 200 and rendered meaningful content, 1,681 raw/normalized records, 66 signal cards, and no framework error overlay.
- Full repository check passed: `30 passed in 44.81s`; credential scan passed.

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
