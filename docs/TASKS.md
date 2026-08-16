# Tasks

## NOW

- The 2026-08-16 source/cost audit and standalone Markdown deliverable are complete. The local radar is running, but production owners must decide whether to keep the no-key third-party FxTwitter adapter for a bounded prototype or migrate X reads to the official pay-per-use API after terms review.

## NEXT

- Decide the production X read-source strategy: explicitly accept and govern the third-party FxTwitter prototype risk, or budget and implement the official X API.
- Observe the installed radar task for at least seven days, then measure end-to-end success plus P50/P95 discovery latency; current successful cycles are not yet a sustained SLA.
- Obtain the five accounts' historical posts, manual adoption decisions, and 1H/6H/24H view snapshots so the five Style Packs can be calibrated from real business data.
- Obtain the real human+AI research workflow and copy-generation workflow paths; both were `NOT_PROVIDED` in P01.
- Approve the integration contracts for `TopicCandidate`, `EvidenceBundle`, `ContentDraft`, and `PerformanceSnapshot` before implementation.
- Complete commercial-use/terms review for the five active X accounts and the YouTube Atom feed; forum sources remain absent.
- If account onboarding is authorized, manually validate the recommended Taiwan-stock X shortlist for identity, recent activity, topical fit, collection terms, and 1H/6H/24H performance before editing `x_sources` or `local_kols`.
- If authorized, adapt the inspected X-growth, X-writing, and human-in-the-loop patterns into one repository-local `taiwan-finance-x-growth` Skill instead of installing an unmodified generic bundle.
- Define a two-week manual pilot with one real account, a target audience, an approved account voice, original/reply/quote-post quotas, human approval, and 1H/6H/24H performance snapshots.

## LATER

- Add MOPS only under a separate explicit task and only after its source/collection authorization is verified.
- Add authorized media/news collection only under a separate task with verified terms, Evidence, and publisher-group rules.
- Enable the United States Market Pack only after a verified US source registry is supplied and validated.
- Revisit advertising policy/precheck only when the business makes promotion a priority again.

## BLOCKED

- US source onboarding is blocked by the absence of a verified US source registry.
- Automated collection from non-`API_VERIFIED` sources is blocked pending terms, license, robots, or explicit permission review.
- Five-account Style Pack calibration and performance baselines are blocked by missing screenshots, history, adoption, and view data.
- Exact integration with the business's existing human+AI and copy workflows is blocked because their paths were not provided.
- Additional Taiwan X, YouTube, and forum coverage is blocked pending verified identities and collection/usage authorization.
- Public follower/view snapshots are discovery evidence only; the Taiwan-stock X shortlist is not an authorized collection registry and its exact heat remains `NEEDS_CONFIRMATION` until first-party or approved measurements exist.
- The target X account/profile baseline, account owner consent, X API/OAuth authorization, content lead workflow, and first-party analytics are `NOT_PROVIDED`; account-growth effectiveness cannot yet be measured.
- AI-generated automated replies require prior written X approval, unsolicited keyword-triggered automated replies are prohibited, and non-API website scripting is prohibited under X's April 2026 automation rules. Until those conditions change, interaction must remain draft-assisted and human-executed.
- Current end-to-end X monitoring SLA remains `UNKNOWN`: the Windows task is live and recent cycles succeeded, but seven-day reliability and P50/P95 latency have not been measured.

## DONE

- Git baseline publication: created the first repository history on `main`, connected `origin` to `PeaSea-21/Global-X-Finance-Growth-Intelligence`, preserved runtime/credential/cache exclusions, and pushed the reviewed project baseline to GitHub.
- Delivered `deliverables/项目整体逻辑与数据源成本说明.md`, covering the implemented data flow, source governance, current runtime state, direct costs, authorization caveats, missing capabilities, risks, and recommended next steps.
- 2026-08-16 source/cost audit: verified the implemented collection paths, local scheduled-task state, current database counts, and current upstream pricing/terms. Confirmed that the current runtime has no model/API bill and uses TWSE OpenAPI, a no-key third-party FxTwitter adapter, and a no-key YouTube Atom feed; official X API reads are pay-per-use and the third-party path remains a production policy/continuity risk.
- Taiwan realtime radar P02 implementation is present and live: five X sources run on ten-minute due intervals, one TWSE YouTube source runs on a thirty-minute due interval, and the Windows dispatcher last returned success during the 2026-08-16 audit.
- 2026-08-14 GitHub/X-growth scan: reviewed the current X recommendation-algorithm repository, algorithm playbook, X-growth and X-writing Skill bundles, a human-in-the-loop social-media agent, watchlist/reply-agent patterns, Postiz, and X's April 2026 automation/authenticity rules. Recommended a project-specific manual-approval workflow and rejected browser scripting, automatic likes, unsolicited automatic replies, engagement pods, and bulk interaction.
- 2026-08-14 Taiwan-stock X account landscape scan: identified a public-snapshot shortlist of recently rising and long-running accounts, mapped them to semiconductor/AI supply-chain, market/quant, and sentiment use cases, and preserved all accounts as D-level discovery leads rather than adding them to collection configuration.
- CODEX TASK P01: audited current Global X Finance code/data/tests, both local xHotTopic copies, the live PeaSea-21 GitHub repository, the verified Taiwan source registry, local runtime/scheduler state, the last xHotTopic output, and a five-account X adapter sample. Produced the nontechnical pivot audit, 17-row source matrix, five Style Pack v0.1 designs, unified draft/feedback structures, staff workflow, and 10-day integration plan without modifying core code or databases.
- Read-only provider audit: confirmed the project has no AI relay/model call; its configured network sources are TWSE official OpenAPI and X official policy pages. The local Codex configuration selects OpenAI `gpt-5.6-sol` with no custom provider or API base URL configured.
- Foundation MVP: shared TW/US Market Pack path, SQLite schema, verified source registry, immutable Evidence storage, publisher-group deduplication, uncertainty states, compliance limits, credential scan, and automated tests.
- Taiwan Official Data Demo v0.2: authorization-gated TWSE OpenAPI collection from three official datasets, exact deduplication, Evidence pages, and Windows one-click launcher.
- CODEX TASK 03 / v0.3: 1,681 real TWSE raw records normalized through one auditable path; 1,681 entity links; 66 `RULE_BASED_OFFICIAL_SIGNAL` cards; date/code filters, pagination, freshness wording, Evidence back-links, updated boss script and screenshot.
- CODEX TASK C01 / v0.4: six official X policy pages fetched as append-only raw snapshots, 26 structured rules per current six-page set, separate TW/US financial/crypto checklist templates, fail-closed precheck logic, policy UI, CSV/Markdown deliverables, screenshot, and browser acceptance.
- Windows double-click launcher repair: ASCII-safe batch parsing for paths containing spaces, no optional `tzdata` dependency in dashboard/collector date handling, retained failure window, and real `cmd.exe` plus browser verification.
- Project Memory: repo-local skill, task protocols, durable context files, handoff, and integrity check command.
