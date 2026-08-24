# 可直接交给 Codex 的任务提示词

使用方式：把真实频道资料作为附件，与下面整段任务书一起发送给一个新的 Codex 任务。不要只发送频道资料，也不要删掉范围和验收要求。

---

# CODEX TASK P06A — BEN Radar 20 频道画像审计与三频道试点选择

你正在处理仓库：

`C:\Users\yinen\Documents\ChatGPT\全球财经热点采集 Agent`

当前任务不是直接开发 20 个频道，也不是重做 Radar。请先把我本次附上的真实频道资料转成可审计的业务配置草案，核对现有数据能力，并推荐三个差异明显的试点频道。完成本任务的全部产物和验证后停止，等待我确认试点频道；不要提前进入 Schema 或应用实现。

## 1. 必读资料与优先级

开始前必须完整读取：

1. 本次用户附上的全部频道资料。
2. `AGENTS.md`
3. `docs/PROJECT_CONTEXT.md`
4. `docs/DECISIONS.md`
5. `docs/TASKS.md`
6. `docs/CHANGELOG_WORK.md`
7. `docs/HANDOFF.md`
8. `deliverables/BEN_20频道每日热点业务需求分析_2026-08-18.md`
9. `deliverables/BEN_Radar_Channel_Driven_最优业务方案_v2_2026-08-18.md`

然后运行：

```powershell
git status --short --branch
```

事实冲突时的优先级：

1. 当前用户提供的频道资料和本任务要求。
2. 当前代码、配置、数据库结构、Git 状态与实际测试结果。
3. 上述两份业务方案。
4. Project Memory。
5. 历史聊天或 GPT 概念稿。

HANDOFF 只是线索，不是事实来源。频道资料中没有的信息不得凭常识补齐；标记为 `UNKNOWN` 或 `NEEDS_CONFIRMATION`。

在实质工作前，用不超过 10 行汇报：项目目标、已完成能力、当前工作树状态、频道资料数量、当前阻塞、本任务范围、下一步。

## 2. 产品定义

本项目目标固定为：

> BEN Radar 是面向财经内容团队的频道每日选题决策系统。它把共享的真实事件池转换成每个频道当天 5–8 个可解释、可核验、可进入人工生产流程的候选。

固定业务链路：

```text
Evidence → Signal → Event → Topic → Channel Assignment → Channel Daily Brief
```

不要退回“股票榜单 + 新闻列表”的信息墙，也不要把当前 Top20 股票、29 个 X 监控账号、来源 registry 或 YouTube 来源误认为输出频道。

## 3. 本任务严格范围

本任务必须完成：

1. 读取并逐项盘点用户提供的全部频道。
2. 原样保留频道名称、简介、标签、样例和其他用户字段。
3. 为每个频道生成一份版本化 `ChannelProfile v0.1 DRAFT`。
4. 标出频道之间的重叠、差异、冲突和潜在撞题关系。
5. 将每个频道的需求映射到当前真实数据能力和缺口。
6. 推荐三个差异明显、最能验证共享引擎的试点频道。
7. 为三个试点分别写 5 个“合格 Topic Card 应长什么样”的结构化验收样例；如果真实 Evidence 不足，使用 `SCHEMA_EXAMPLE_NOT_REAL_TOPIC`，不得伪装成当天真实热点。
8. 冻结 P06B 实现前需要确认的业务问题清单。

本任务禁止：

- 修改应用代码、Flask 页面、Schema、migration 或数据库。
- 接入、抓取、测试或采购新的外部数据源。
- 修改 Anomaly Engine 规则、阈值、排名或现有 Stock Workbench。
- 把工作树中未提交的 Industry Mapping 当作已完成生产能力。
- 自行决定美股、Reuters、Bloomberg、CNBC、X 或其他来源已经获授权。
- 生成 20 套硬编码频道逻辑。
- 安装第三方 Skill、Agent、数据库、向量库或基础设施。
- 自动发布、自动互动或生成投资建议。
- 因为目标是 5 条而编造热点、催化剂、数字或 Evidence。

允许修改的范围仅限：

- 新建本任务要求的 `research/ben_radar_channel_intake/` 审计产物。
- 新建本任务要求的 `deliverables/` 业务报告。
- 按 `AGENTS.md` 更新六份 Project Memory 文件。

## 4. 频道资料提取规则

先统计用户实际提供了多少个频道。若不是 20 个：

- 不补造频道。
- 明确列出实际数量、重复项、无法识别项和缺失数量。
- 继续完成已提供频道的审计。
- 最终状态标记 `PARTIAL_INPUT`，不得声称完成 20 频道画像。

每个字段都必须带 provenance：

```text
SUPPLIED               用户明确提供
DERIVED_FROM_SUPPLIED  可直接从用户资料确定性归纳
PROPOSED               为后续讨论提出的建议
UNKNOWN                没有资料
CONFLICT               用户资料内部冲突
```

不得把 `PROPOSED` 写成用户已经确认。

## 5. ChannelProfile v0.1 DRAFT 契约

每个频道至少输出：

```text
channel_id
channel_name
source_index
source_fields_raw
profile_version = 0.1-draft
profile_status

channel_summary
target_audience
primary_market
secondary_markets[]
security_scope[]
preferred_sectors[]
preferred_entities[]
preferred_topic_types[]
excluded_topics[]
prohibited_claims[]

allowed_source_classes[]
minimum_evidence_policy
opinion_usage_policy
maximum_data_age
market_session_preferences[]

preferred_formats[]
content_depth
title_intensity
risk_tolerance
required_disclosures[]

daily_primary_target = 5
daily_backup_target_range = 0..3
shortage_policy = HONEST_SHORTAGE
recent_duplicate_window_days = 30

positive_examples[]
negative_examples[]
missing_fields[]
conflicts[]
proposed_fields[]
field_provenance{}
```

`channel_id` 必须稳定、唯一、可读，但不能覆盖用户原始频道名。

## 6. 频道矩阵

必须建立两张矩阵。

### 6.1 频道重叠/差异矩阵

逐频道比较：

- 市场重叠。
- 行业/实体重叠。
- Topic 类型重叠。
- Evidence 要求差异。
- 内容深度/格式差异。
- 可能使用同一 Event 的概率。
- 撞题风险。
- Why Channel 能否形成实质差异。

不要用一个不透明相似度分数代替解释。可以提供辅助分值，但必须同时给出具体重叠字段和差异字段。

### 6.2 数据覆盖/依赖矩阵

每个频道逐项标记：

```text
AVAILABLE_VERIFIED
AVAILABLE_BUT_PROTOTYPE
PARTIAL
UNKNOWN
BLOCKED_RIGHTS
NOT_IMPLEMENTED
```

至少覆盖：

- TWSE/TPEx EOD。
- 历史基线和 Anomaly Engine。
- Industry Mapping。
- MOPS 重大讯息。
- 月营收、财报、法说、Guidance。
- 台湾新闻。
- 国际新闻。
- X。
- 美股 EOD。
- 财报/宏观日历。
- 频道近 30 天采用历史。
- 1H/6H/24H 反馈。

所有能力判断必须引用当前代码、配置、数据库结构、交付物或测试证据；无法当前验证的写 `UNKNOWN / NEEDS_CONFIRMATION`。

## 7. 三个试点频道选择规则

先审计全部频道，再推荐三个试点。三个试点应尽量分别代表：

1. `SIGNAL_HEAVY`：当前 EOD/异常数据成熟，能验证 Market Signal → Topic。
2. `EVENT_HEAVY`：依赖公司事件或合格 Evidence，能验证 Event → Topic。
3. `CROSS_ENTITY`：需要跨公司/产业组合，能验证多实体关系与频道差异。

选择时同时考虑：

- 当前真实数据成熟度。
- 三个频道之间的业务差异。
- 是否能复用同一底层引擎，而非三套硬编码。
- 是否能在最近五个完整交易日做 Replay。
- 是否能设计明确的人类验收。
- 数据缺口是否小到足以试点。

不得只选三个最相似、最容易的频道。若真实频道中不存在某类，说明原因并选择最接近者；若不足三个可行频道，诚实输出更少的推荐。

所有选择状态为 `RECOMMENDED_PENDING_APPROVAL`，不能写成已批准。

## 8. Topic Card 验收样例

为每个推荐试点输出 5 个结构样例，每个样例必须包含：

```text
topic_title
readiness
what_happened
what_changed
why_now
why_channel
related_market_qualified_security_ids[]
market_session_date
session_state
data_as_of
verified_facts[]
derived_findings[]
opinions[]
unknowns[]
source_conflicts[]
evidence_ids[]
independent_publisher_groups[]
suggested_angles[]
working_titles[]
risk_flags[]
```

若当前真实 Evidence 不足以生成真实样例：

- 使用结构占位值。
- 加 `data_label = SCHEMA_EXAMPLE_NOT_REAL_TOPIC`。
- 禁止使用看似真实的当前数字、公司事件或因果结论。

## 9. 必须生成的文件

创建目录：

`research/ben_radar_channel_intake/`

至少生成：

1. `source_inventory.md`：频道输入文件、实际频道数、重复/缺失/解析问题。
2. `channel_profiles_v0.1.json`：所有频道的结构化 Profile 草案。
3. `channel_profiles_human_review.md`：面向业务人员的逐频道审阅版。
4. `channel_overlap_matrix.csv`：频道重叠、差异和撞题风险。
5. `channel_data_coverage_matrix.csv`：频道对当前数据能力的依赖与缺口。
6. `pilot_recommendation.md`：三个试点推荐、证据、反对理由和替代项。
7. `pilot_topic_card_examples.json`：每个试点 5 个结构化验收样例。
8. `open_questions.csv`：只列会实质影响频道规则或试点的缺失问题。
9. `acceptance_report.md`：逐项检查本任务验收标准。

同时生成一份可转发报告：

`deliverables/BEN_RADAR_20频道画像与三频道试点建议_P06A.md`

报告要让非技术业务负责人看懂，先写结论、频道分组、三个试点、主要数据缺口和需要确认的问题，再写技术附录。

## 10. 验收标准

必须满足：

1. 用户提供的每个频道都有一条可追溯 Profile，实际数量已对账。
2. 所有非用户字段都有 provenance；`UNKNOWN` 未被补成猜测。
3. 频道原始名称、简介、标签和样例未被覆盖或丢失。
4. 三个试点具有明显业务差异，并说明为什么不是只做一个频道或直接做 20 个。
5. 每个试点有 5 个结构化 Topic Card 验收样例；合成示例明确标注。
6. 数据覆盖矩阵与当前仓库事实一致。
7. 未把未提交 Industry Mapping、美股、新闻授权、X 原型或 LLM 写成已完成生产能力。
8. 未修改代码、Schema、migration、数据库、来源配置、规则或公共站点。
9. JSON/CSV 可被标准解析；频道 ID 唯一；矩阵行数与频道数一致。
10. `git diff --check` 通过；若只有既有换行提示，应如实说明。
11. `powershell -ExecutionPolicy Bypass -File scripts/project-memory-check.ps1` 通过。

本任务只改文档/研究产物，不需要为了形式重跑完整应用测试；但必须说明跳过原因。若你意外修改了应用或 Schema，必须停止、报告偏离，不得把超范围改动包装成完成。

## 11. Project Memory 收尾

按 `AGENTS.md`：

- 更新 `docs/TASKS.md`。
- 仅在出现已获用户确认的正式决策时更新 `docs/DECISIONS.md`；试点推荐本身不是正式决策。
- 追加 `docs/CHANGELOG_WORK.md`。
- 刷新 `docs/HANDOFF.md`，明确待用户确认的三个试点和未解决问题。
- 运行 Project Memory check。

## 12. 最终回复要求

最终回复先给：

1. 实际识别到多少个频道。
2. 推荐的三个试点及各自类型。
3. 最大的三个数据/业务缺口。
4. 哪些内容仍为 `UNKNOWN / NEEDS_CONFIRMATION`。
5. 产物文件链接。
6. 验证结果与跳过的测试。

不要声称 P06B 已实现，不要要求用户理解技术细节。最终只提出真正会改变试点选择或频道规则的少量问题。

---

任务结束。
