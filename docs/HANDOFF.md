# Handoff

- 更新时间：2026-08-16 10:42:19 +08:00
- Direction: build a human-operated **财经账号实时内容供给工作台** for roughly 10–15 content staff; no automatic posting or investment advice.
- Implemented flow: TWSE official OpenAPI Evidence -> exact normalization -> rule cards, plus five X timelines and one TWSE YouTube Atom feed -> immutable radar Evidence -> health/recent-content UI.
- Operating truth at audit time: the Windows radar task was installed and ready; its latest observed run returned exit code 0. The database held 1,786 raw items, 105 radar items, and 24 radar runs.
- Cost truth: the current runtime has no AI/model bill and no official X API bill. TWSE, FxTwitter, and YouTube Atom are called without credentials; local SQLite/Flask storage is used.
- Risk: FxTwitter is a third-party public adapter, while current X guidance requires the official API and official X reads are pay-per-use. Treat the current X path as a bounded prototype, not a durable free production entitlement.
- Registry truth: 23 Taiwan entries comprise 6 active, 5 manual-only, 10 needing verification, and 2 blocked. Candidate media/regulator entries are not automatic data feeds.
- Standalone brief: `deliverables/项目整体逻辑与数据源成本说明.md` contains the full nontechnical system logic, source, cost, and risk explanation.
- US Market Pack remains empty and blocked pending a verified source registry.
- Missing business inputs: real research/copy workflow paths, approved account voice, adoption decisions, and 1H/6H/24H performance data.
- Git baseline is established on `main` and published to `origin` at `PeaSea-21/Global-X-Finance-Growth-Intelligence`; runtime databases, logs, local environments, credentials, caches, and generated ZIP archives remain ignored.
- Recommended next task: decide the production X read-source strategy, then run a seven-day reliability/latency observation before expanding sources or building content-generation workflow.

