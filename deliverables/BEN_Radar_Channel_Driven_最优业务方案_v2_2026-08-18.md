# BEN Radar Channel-driven 最优业务方案 v2

- 日期：2026-08-18
- 输入：Ben 录音业务需求、用户提供的 GPT 方案、当前仓库代码/配置/验证产物
- 状态：`PROPOSED_PENDING_CHANNEL_INPUT`
- 下一依赖：20 个输出频道的名称、简介、标签和边界
- 本方案不代表已经实现，不修改现有行情、数据库、来源权限或 Anomaly Engine 规则

## 0. 先说结论

GPT 方案的产品方向大体正确，但只能算概念稿，不能直接拿来开发。

它最有价值的判断是：BEN Radar 应该从股票/新闻信息墙转成 Channel-driven Topic Intelligence；Signal 不等于 Topic；EOD 足以启动；确定性计算与 LLM 应分工；第一阶段不需要换数据库或做实时行情。

它显得“一般”的根本原因是缺少两个决定产品能否真正落地的层：

1. **Signal 与 Topic 之间缺少 Event 层**：多个信号必须先证明是在描述同一个真实事件，才能组成选题；否则“几只股票一起放量”很容易被 AI 拼成不存在的产业故事。
2. **Topic 与频道页面之间缺少 Assignment 层**：同一真实事件为什么给 A 频道、为什么不给 B 频道、跨频道如何换角度、如何防重复，都没有明确对象和规则。

因此，最优业务链路不是 GPT 写的：

```text
Raw Data → Signal → Topic → Channel
```

而应该是：

```text
Evidence → Signal → Event → Topic → Channel Assignment → Channel Daily Brief
```

最终产品也不只是 “Topic Intelligence”，而是更具体的：

> **BEN Radar = 面向财经内容团队的频道每日选题决策系统。**
>
> 它把共享的真实事件池，转换成每个频道当天 5–8 个可解释、可核验、可直接进入生产的选题候选。

## 1. 对 GPT 方案的处理意见

### 1.1 应保留

| GPT 判断 | 处理 |
|---|---|
| 不是行情终端或新闻聚合站 | 保留，作为产品边界 |
| Research Compression + Editorial Decision | 保留，作为商业价值 |
| Signal 不等于 Topic | 保留，但中间必须增加 Event |
| 底层数据共享，频道差异配置化 | 保留，升级为版本化 Channel Profile |
| EOD 行情可以启动 | 保留，并加入市场交易日/时段语义 |
| 确定性程序与 LLM 分工 | 保留，但 LLM 权限还要收紧 |
| 不做神秘 HotScore | 保留，频道排名要披露门槛和理由 |
| Python + Flask + SQLite 足够 MVP | 保留，当前没有迁移技术栈的业务证据 |
| 用 Time to Topic 和采用率验收 | 保留，但指标不够完整 |

### 1.2 必须修改

| 原方案问题 | 为什么不够 | v2 修正 |
|---|---|---|
| 每频道 Top 3–5 | 低于 Ben 明确提出的 5 个及以上 | 目标 5–8；不足时显示真实短缺 |
| 第一版只做一个频道 | 只能证明一个页面能工作，不能证明 Channel-driven | 先读完 20 频道，再选 3 个差异明显的频道试点 |
| Signal 直接交给 Topic Builder | 容易把相关但不同的事情错误合并 | 增加 Event Cluster 与关系类型 |
| LLM 判断频道匹配 | 太自由、不可重复、难审计 | 硬规则先做资格判断，LLM 只补语义解释 |
| 后台可算一个总分 | 容易重新变成不透明 HotScore | 硬门槛 + 分层级 + 维度理由 + 稳定排序版本 |
| 固定每 30–60 分钟重算 | 未区分 EOD 不变与事件流变化 | EOD 提交、新事件入池和班次截止点触发重算 |
| FACT/MEDIA/X/DERIVED/AI 五类 | 把“来源类型”和“事实状态”混在一起 | 改成来源轴 + 认知状态轴两套标签 |
| Reuters/CNBC/MOPS/X 像是现成生产源 | 与当前授权、持续运行和覆盖事实不一致 | 每个来源保留 `READY / PROTOTYPE / UNKNOWN / BLOCKED` |
| 最后自然升级实时行情 | 实时不是必经终点，成本可能没有回报 | 只有错过选题被证明来自行情延迟时再采购 |

### 1.3 不应照搬

1. 不应把 GPT 举例的频道名直接当作公司的真实 20 频道。
2. 不应因为“Topic-first”就删除 Stock Workbench；它应保留为 Signal 检查和 Evidence 详情层，只是不再做首页主产品。
3. 不应把三只同产业股票同步异动自动写成“资金共振原因已确认”；这最多是程序派生的共现信号，催化剂仍可能 `UNKNOWN`。
4. 不应在未完成来源授权、持续性测试和成本确认前，把国际媒体、X 或美股行情写成生产能力。

## 2. 产品主键：频道 × 业务日

用户打开系统后首先选择的是自己负责的频道，而不是股票、来源或市场。

系统主页面对象为：

```text
ChannelDailyBrief
  业务日期
  频道
  本次简报对应的市场时段
  数据更新时间与覆盖状态
  5 个主候选
  0–3 个备选
  今日强热点不足原因
```

20 个频道 × 每频道至少 5 个候选，代表每天至少 100 个 `ChannelTopicAssignment`，不是每天必须创造 100 个互不相同的事件。

一个事件可以服务多个频道，但必须满足：

- 每个频道有独立的 `why_channel`。
- 每个频道有符合自身受众的内容角度。
- 不复制同一个标题和正文。
- 页面显示该事件还被分配给哪些频道，避免团队撞题。
- 同一频道近期采用过的同类选题必须提示重复。

## 3. 六层业务架构

### 3.1 Evidence：真实输入

保存原始市场数据、公告、新闻和 X 内容以及来源、时间、权限状态和内容哈希。下游任何总结都不能覆盖原始 Evidence。

最低要求：

- 原始发布时间与抓取时间分离。
- 市场、交易所和证券 ID 明确。
- 同一 publisher group 不重复计算独立证据。
- 来源可访问不等于可商业采集或公开展示。
- 失败、过期和缺失保留真实状态。

### 3.2 Signal：原子变化

Signal 只回答“哪里出现了值得注意的变化”，不直接回答“该讲什么”。

```text
Market Signal
  RVOL / Breakout / Price anomaly / 多日持续 / 流动性

Corporate Signal
  MOPS 重大讯息 / 月营收 / 财报 / 法说 / Guidance

Attention Signal
  新闻增量 / X 讨论增量 / 多来源共现

Calendar Signal
  财报日 / 法说会 / 监管或宏观日历
```

现有 Anomaly Engine 应保留为 `Market Signal Engine`，其排名规则不等于最终频道选题排名。

### 3.3 Event：现实世界发生了什么

Event 层先把多个 Evidence/Signal 组织成可审计的真实事件。

```text
Event
  entities[]
  action
  object / target
  stage
  normalized numbers[]
  event time
  market session
  evidence_ids[]
  SAME_EVENT / RELATED_BUT_DISTINCT links
```

只有 `SAME_EVENT` 可以合并。相同行业、相近时间或相同关键词只能建立 `RELATED_BUT_DISTINCT` 关系，不能直接当成一个事件。

例如三只航运股同步放量，可以形成一个 `SECTOR_COOCCURRENCE` 派生事件，但“因为运价上涨”必须有运价或合格新闻 Evidence；没有时应显示“共现已确认，原因未确认”。

### 3.4 Topic：值得讨论的编辑命题

Topic 不是 Event 的摘要，而是可以交给编辑判断的内容命题。

```text
TopicCandidate
  what_happened
  what_changed
  why_now
  audience_question
  related_entities[]
  supporting_event_ids[]
  verified_facts[]
  derived_findings[]
  opinions[]
  unknowns[]
  source_conflicts[]
  readiness
```

建议使用三种准备度：

- `READY_TO_PITCH`：事实和数据已足够，编辑可直接判断是否生产。
- `NEEDS_RESEARCH`：有明显价值，但催化剂或关键事实仍需补证据。
- `WATCH_ONLY`：只有弱信号或条件未满足，不应进入主生产队列。

### 3.5 Channel Assignment：为什么给这个频道

Topic 通过频道硬门槛后，才产生 Assignment。

```text
ChannelTopicAssignment
  channel_id
  topic_id
  business_date
  channel_fit_reasons[]
  why_now[]
  suggested_angles[]
  title_options[]
  rank_tier
  rank_reasons[]
  duplicate_warnings[]
  risk_flags[]
```

同一个 Topic 在不同频道中可以有不同 Assignment；Topic 的事实不能因频道不同而变化。

### 3.6 Channel Daily Brief：给人的最终产品

每频道默认输出：

- 1 个“今天最该讲”。
- 4 个主候选。
- 0–3 个备选。
- 0–2 个继续观察项。
- 一条覆盖说明：数据时段、来源缺口、候选是否达到 5 条。

如果只有 3 条合格候选，就显示 `3/5，今日强热点不足`，不得用旧闻、弱相关或虚构理由补满。

## 4. Channel Profile 不是一句简介

GPT 的 “Channel DNA” 概念可以保留，但应改成可版本化、可审计的 `ChannelProfile`，包含四层。

### 4.1 资格层：决定能不能进

- 主市场和次市场。
- 允许的资产/证券类型。
- 允许的主题和内容类型。
- 排除主题、禁用表达和风险边界。
- 最低 Evidence 要求。
- 是否允许以 `OPINION` 为主要线索。
- 最大数据陈旧度。

### 4.2 偏好层：决定谁排前面

- 变化强度。
- 市场反应。
- 官方/公司 Evidence。
- 产业共振。
- 争议与解释价值。
- 新鲜度。
- 与近期内容的差异。

### 4.3 包装层：决定怎么讲

- 目标受众。
- 深度和长度。
- 适合单股、板块、宏观还是问答。
- 常用内容格式。
- 允许的标题强度。
- 必须出现的风险提示。

### 4.4 学习层：只记录真实业务反馈

- 最近 30 天采用/拒绝的 Topic。
- 拒绝原因。
- 漏掉的重要 Topic。
- 1H/6H/24H 内容表现。
- 当前 Profile 版本和人工批准人。

系统可以根据这些数据提出调权建议，但不能自动改变频道规则；新版本需人工确认。

## 5. 排名：先过门槛，再比优先级

### 5.1 硬门槛

以下任一失败，都不能进入主候选：

1. 市场交易日或 `data_as_of` 不明确。
2. Topic 与频道的市场/主题/资产范围不匹配。
3. Evidence 低于频道最低要求。
4. 关键事实只有 AI 推断且没有支持 Evidence。
5. 已过期，或与本频道近期采用内容高度重复。
6. 存在未披露的 `SOURCE_CONFLICT`。
7. 数据质量状态为不可用。

不满足主候选但仍有研究价值的，可以进入 `NEEDS_RESEARCH`，不能偷偷降低门槛。

### 5.2 排名维度

候选通过门槛后，按频道版本化规则比较：

| 维度 | 回答的问题 |
|---|---|
| Channel Fit | 是否真正符合本频道受众和定位？ |
| Change Strength | 相比历史、预期或此前状态，变化有多明显？ |
| Evidence Quality | 官方/公司证据、独立来源和冲突状态如何？ |
| Time Relevance | 对当前市场班次是否仍然有效？ |
| Talkability | 是否存在清楚的矛盾、反差或解释价值？ |
| Novelty | 与本频道近 30 天内容是否重复？ |
| Diversity | 当日 Top5 是否过度集中在同一事件、行业或来源？ |

前台不显示一个神秘总分，而显示：

- 是否过门槛。
- `A / B / C` 优先层级。
- 入选的前三个原因。
- 主要扣分与未知项。
- 具体原始指标。

Market Signal 排名与 Editorial Ranking 必须分开版本化，防止修改频道偏好时悄悄改变行情异常算法。

## 6. 真实性标签：改成两条轴

GPT 把 FACT、MEDIA、X SIGNAL、DERIVED、AI ANALYSIS 放在同一层，会让员工把“来源”和“事实状态”混淆。

### 来源轴

```text
OFFICIAL_MARKET
OFFICIAL_DISCLOSURE
COMPANY_IR
LICENSED_MEDIA
PUBLIC_MEDIA_DISCOVERY
X_OFFICIAL
X_OPINION
OTHER_OPINION
```

### 认知状态轴

```text
FACT
DERIVED
AI_INFERENCE
OPINION
UNKNOWN
SOURCE_CONFLICT
```

示例：

- TWSE 成交量：`OFFICIAL_MARKET + FACT`。
- RVOL 4.7：`OFFICIAL_MARKET + DERIVED`。
- KOL 猜测需求改善：`X_OPINION + OPINION`。
- AI 解释可能是资金轮动：`AI_INFERENCE`，必须列支持 Evidence，不能升级为 FACT。
- 催化剂未找到：`UNKNOWN`，不能写成 0 或无催化剂。

## 7. LLM 的正确位置

LLM 不负责以下工作：

- 交易日、时间和时区。
- 价格、成交量、RVOL 和突破计算。
- 证券/产业 ID。
- Evidence 去重和 publisher group。
- 来源权限和可用状态。
- Event 的硬合并规则。
- 频道资格门槛。

LLM 只接收一个结构化 `TopicPacket`，可以做：

- 将已确认 Event 整理为候选 Topic。
- 补充受众问题和 Why Now 表述。
- 对已通过硬门槛的候选解释 Why Channel。
- 生成 2–3 个原创选题角度和工作标题。

每个模型输出必须：

- 返回结构化字段。
- 引用输入中的 Evidence ID。
- 不得新增股票、数字、公司行为或因果事实。
- 明确输出 `unknowns` 和 `source_conflicts`。
- 保存模型/Prompt/Profile 版本和缓存键。
- 模型不可用时回退到确定性摘要，不把失败伪装成 AI 结果。

## 8. 时间体系：不是简单的三种刷新速度

EOD 可以做第一版，但每项信息必须带自己的有效时段。

```text
market
market_session_date
session_state
source_published_at
collected_at
data_as_of
freshness_state
```

建议的业务简报班次：

| 简报 | 使用的数据 |
|---|---|
| 台股盘前简报 | 上一完整台股交易日 + 隔夜新增事件 |
| 台股收盘简报 | 当日完整 EOD + 当日公告/事件 |
| 亚洲早间美股简报 | 美国上一完整交易日/刚收盘数据 |
| 事件更新 | 新公告、新闻或 X Evidence 入池后，只重算受影响 Topic/频道 |

重算触发点应是：

1. 新的完整 EOD snapshot 已提交。
2. 新 Event 通过 Evidence 和新鲜度闸门。
3. 固定班次截止时间到达。
4. Channel Profile 新版本获批准。

不需要为了看起来实时而每 30 分钟重跑所有行情和 20 个频道。

## 9. 前台：频道简报，不是信息墙

### 9.1 第一屏

- 左侧或顶部：20 个频道及各自合格候选数。
- 当前频道名称、简介和 Profile 版本。
- 数据状态：台股/美股时段、新闻、MOPS、X 的 `as_of` 和覆盖。
- “今天最该讲”一条。
- 其余 4 个主候选。

### 9.2 Topic Card

每张卡只保留决策需要的信息：

1. 一句话选题。
2. `READY_TO_PITCH / NEEDS_RESEARCH / WATCH_ONLY`。
3. 为什么是现在。
4. 为什么适合本频道。
5. 最多 3 个关键事实/数字。
6. 涉及股票和行业，使用市场限定 ID。
7. 2–3 个内容角度和工作标题。
8. Evidence 数、独立 publisher group 数。
9. 市场时段、`data_as_of`、未知和冲突。
10. 采用、备选、忽略、查看 Evidence。

图表、原文、完整指标和采集诊断放到展开详情或独立诊断页。Stock Workbench 继续承担 Signal/图表核验，不再占据频道首页主叙事。

### 9.3 团队防撞

进入生产队列后显示：

- 被哪个频道采用。
- 谁已认领。
- 是否有其他频道使用同一 Event。
- 各频道的角度是否过度相似。
- 当前状态：待核验、可写、起草中、待审核、已手工发布。

第一版仍不自动发布。

## 10. 数据源策略：从缺题反推，而不是列愿望清单

不要先决定要接 100 个来源。先用频道试点记录“为什么没选题”：

```text
NO_CHANNEL_FIT
INSUFFICIENT_EVIDENCE
MISSING_MARKET_DATA
MISSING_CORPORATE_DATA
MISSING_INDUSTRY_MAPPING
STALE_EVENT
DUPLICATE_TOPIC
SOURCE_RIGHTS_BLOCKED
```

只有连续出现的缺题原因，才进入来源建设优先级。

当前能力应按真实状态描述：

| 能力 | 当前状态 |
|---|---|
| TWSE/TPEx EOD 与历史基线 | 已实现并验证，当前公开快照日期为 2026-08-17 |
| Anomaly Engine | 已实现，`READY_FOR_HUMAN_REVIEW`，不是业务规则已验证 |
| Industry Mapping | 工作树中有未提交 migration/module/tests，但尚未接入 Topic 流程，本方案标记 `NEEDS_CONFIRMATION` |
| MOPS | 已有有限的官方重大讯息连接与映射；月营收/财报/法说完整能力未完成 |
| 新闻 | 有限历史样本和事件路径；多项商业使用权仍 `UNKNOWN / DISCOVERY_ONLY` |
| X | 有原型监控与 Evidence；第三方 FxTwitter 路径不是生产级授权/SLA |
| 美股 EOD | 未接入，来源注册和权限 `UNKNOWN / NEEDS_CONFIRMATION` |
| 20 个输出频道 | 尚未提供 |
| 生产 LLM | 尚未接入；不可把当前规则摘要描述成模型能力 |

Reuters、Bloomberg、CNBC 或其他媒体只有在授权、技术入口和使用范围分别确认后，才能写入生产来源清单。

## 11. MVP：既不只做 1 个，也不直接铺 20 个

### 阶段 0：读完并规范化 20 个频道

目标：先理解完整业务版图，再选择试点。

产物：

- 20 份 `ChannelProfile v0.1`。
- 每频道已知主题、禁区、Evidence 门槛和每日目标。
- 频道之间的重叠/冲突矩阵。
- 当前数据覆盖与缺口矩阵。

验收：所有用户原始字段保留；AI 补出的内容明确标记待确认；没有把示例频道名当真实频道。

### 阶段 1：选择 3 个差异明显的频道做离线 Replay

不是先拍脑袋指定“资金雷达”，而是在 20 个频道中选择：

1. 一个当前数据成熟度最高的 Signal-heavy 频道。
2. 一个依赖公司事件/Evidence 的 Event-heavy 频道。
3. 一个需要跨公司/产业组合的 Cross-entity 频道。

用最近 5 个完整交易日 Replay，每频道每天目标 5–8 个 Assignment。

验收：三个频道的 Top5 和 Why Channel 必须有可见差异；不能靠三套硬编码生成器。

### 阶段 2：3 个频道连续 5 个业务日试用

每天生成正式 Channel Daily Brief，Ben/编辑记录：采用、拒绝、漏题和原因。

验收：

- 所有候选有市场时段和 Evidence。
- 候选不足时诚实显示。
- 人能完成 10/30/60 秒选题动作。
- 记录真实采用率、拒绝理由和漏掉的重要 Topic。

### 阶段 3：扩展到全部 20 个频道

只扩配置、数据映射和频道规则，不复制 20 套代码。按频道依赖分批上线，优先上当前 Evidence 覆盖足够的频道。

每频道目标 5–8 条；不能达标的频道保持 `COVERAGE_INSUFFICIENT` 并给出数据缺口。

### 阶段 4：按缺口补来源和市场

根据试点真实漏题，决定是否补月营收、财报、法说、产业数据、美股 EOD、宏观日历或合规媒体来源。美股不是固定排在某个阶段，而由频道优先级和来源授权共同决定。

### 阶段 5：接内容生产与反馈

只有选题命中率稳定后，再接标题/提纲/草稿、认领、防撞、双层审核、人工发布记录和 1H/6H/24H 反馈。

实时行情只有在“重要选题因 EOD 延迟而持续漏掉”得到真实数据证明后，才进入成本评估。

## 12. 业务验收指标

GPT 只给了 Time to Topic 与采用率，不足以判断系统有没有把事实做错或漏掉重要题。

### 效率

- 10 秒：能指出系统推荐的第一选题。
- 30 秒：能看懂 Why Now、Why Channel 和主要 Evidence。
- 60 秒：能采用/忽略并留下原因。
- 3 分钟内：能最终确定至少一个进入生产的选题。

### 质量

- `Precision@5`：Top5 中被采用或被认定值得继续研究的比例。
- `Missed Important Topics`：人工认为重要但系统没推荐的数量与原因。
- `Evidence Pass Rate`：事实可回链 Evidence 的比例，目标 100%。
- `Time Label Accuracy`：市场交易日/时段标记正确率，目标 100%。
- `Duplicate Rate`：同频道近 30 天重复和当日卡片同质化比例。
- `Channel Differentiation`：三个试点频道的 Top5、Why Channel 和角度是否真正不同。
- `Shortage Honesty`：不足 5 条时是否准确显示，而不是填充弱项。

### 学习

- 采用率和拒绝原因按频道统计。
- 漏题按数据、规则、Evidence、时效、频道画像分类。
- 规则/Profile 修改前后保留版本和 Replay 对比。
- 浏览量只用于内容运营反馈，不能证明财经事实或选题判断正确。

试点可以把 “Top5 中 2–3 条被采用或认为值得研究” 作为待业务确认的目标，但在真实基线出现前不能宣称已达标。

## 13. 下一步频道信息怎么给

你下一步可以直接给现有表格、文档或截图，不需要先按照我们的格式重做。最低只要有：

```text
频道名称
频道简介
主要市场/股票范围
重点标签或常讲内容
明确不做的内容（如果有）
```

如果手上还有以下资料，一并给会明显提高第一版质量：

- 每个频道过去 3–5 条认为“选得好”的题。
- 过去明显不适合该频道的题。
- 频道负责人和每日内容数量。
- 频道面向的人群、常用格式和深度。

收到后应执行：

1. 原样保存用户字段，不先改写。
2. 生成 20 份 ChannelProfile 草案。
3. 标出 AI 推断、矛盾和缺失字段。
4. 画出频道重叠/差异矩阵。
5. 选择三个最能验证共享引擎的试点频道。
6. 再冻结 MVP 的 Topic/Assignment/Brief 数据契约和验收样例。

在 20 个频道信息到齐前，可以确认本方案的产品结构，但不能确定频道优先级、具体权重或最终试点名单。

## 14. 最终路线图

```text
20 频道资料审计
  ↓
共享 Evidence / Signal / Event / Topic 契约
  ↓
3 个差异频道 × 5 个历史交易日 Replay
  ↓
3 个频道连续 5 个业务日人工试用
  ↓
按证据达标程度扩到 20 频道
  ↓
从真实漏题反推数据源和美股/基本面优先级
  ↓
认领、防撞、草稿、人审、人工发布记录
  ↓
1H / 6H / 24H 反馈与版本化调优
  ↓
仅在 ROI 被证明后评估付费实时行情
```

这条路线同时避免两个极端：不会因为第一版只做一个频道而把“Channel-driven”做成硬编码，也不会在频道规则和数据覆盖不清楚时铺开 20 套低质量结果。
