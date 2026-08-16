# Work Changelog

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
