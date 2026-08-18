# BEN RADAR P04 事件聚类 Benchmark

日期：2026-08-16  
范围：内容机会雷达的事件聚类验证，不是全市场或投资策略评估。

## 结论

P04 没有通过“整体降低相似度阈值”追求更漂亮的压缩率，而是建立事件指纹、候选召回和严格合并两阶段。45 对真实 Gold 上，最终 `SAME_EVENT` Precision **100.00%**、Recall **83.33%**、F1 **90.91%**。这说明当前小样本上没有把 Gold 的不同事件误合并，但仍漏掉 1 对别名复杂的新闻 + X 共同事件。

样本只有 45 对、其中同事件正样本仅 6 对，指标不能外推为生产 SLA。

## Gold Dataset

- 文件：`research/ben_radar_p04/event_cluster_gold.jsonl`
- 总计：45 对真实 Evidence。
- `SAME_EVENT`：6。
- `RELATED_BUT_DISTINCT`：19。
- `DIFFERENT_EVENT`：20。
- 来源：本地 `ben_news_items` 与 `ben_x_posts`，原始文本、ID、URL 和发布时间全部固化；无虚构新闻。
- 场景：转载、同公司不同事件、同主题不同新闻、不同事件阶段、新闻 + X、评论扩写、滚动摘要、关键词碰撞。

## 最终指标

把 `SAME_EVENT` 视为正类：

| Gold 样本 | TP | FP | TN | FN | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 45 | 5 | 0 | 39 | 1 | 100.00% | 83.33% | 90.91% |

三分类：

| 类别 | 正确/总数 | Accuracy |
|---|---:|---:|
| SAME_EVENT | 5/6 | 83.33% |
| DIFFERENT_EVENT | 19/20 | 95.00% |
| RELATED_BUT_DISTINCT | 16/19 | 84.21% |

最终混淆情况：`SAME→SAME 5`、`SAME→RELATED 1`、`DIFFERENT→DIFFERENT 19`、`DIFFERENT→RELATED 1`、`RELATED→RELATED 16`、`RELATED→DIFFERENT 3`。

## 两阶段实现

### Stage 1：候选召回

高召回条件包括：规范化外链、ticker/entity、专名 actor、action、target、number、主题 + 动作、或最低文本重合。候选召回只决定“需要比较”，不直接合并。

### Stage 2：严格合并

优先级为：

1. 共享规范化原始链接。
2. 同实体/主体 + 同动作，再由目标、数字、第二主体或足够文本重合确认。
3. 计划、宣布、批准、完成、业绩等事件阶段冲突时保持 `RELATED_BUT_DISTINCT`。
4. 同公司但不同目标/数字，或只有宽泛主题时不合并。
5. 时间差超过 36 小时不合并；可在诊断层标记为跨窗口相关。

事件指纹包含：`primary_entity`、`ticker`、`company`、`actor`、`action`、`event_stage`、`target`、`object`、`number`、`currency`、`percentage`、`geography`、`theme`、`timestamp`、`event_date`、`source_type`。

## 15 个实际错误案例

这是从初版到最终版真实跑出的错误，不隐藏已修复问题：

| ID | Gold → 当时系统 | 核心问题 | 当前状态 |
|---|---|---|---|
| gold-002 | SAME → RELATED | `$3 bln` / `$3 billion` 未归一 | 已修复 |
| gold-003 | SAME → RELATED | `Peter Thiel` 主体短语交集失败 | 已修复 |
| gold-004 | SAME → DIFFERENT | `Peter Thiel` / `Thiel Macro` 跨平台别名 | 已修复 |
| gold-005 | SAME → RELATED | Vista / Vaca Muerta 目标别名 | 仍存在 |
| gold-006 | SAME → RELATED | Nvidia Q2 新闻与中文 X 扩写数字不同 | 已修复 |
| gold-007 | RELATED → DIFFERENT | Qwen3.8-27B 产品 token 未召回 | 已修复 |
| gold-014 | RELATED → DIFFERENT | 中文 AI 主题漏识别 | 仍存在 |
| gold-017 | RELATED → DIFFERENT | Claude/Anthropic 主体未召回 | 已修复 |
| gold-020 | RELATED → DIFFERENT | SpaceX 专名未进入实体 | 已修复 |
| gold-021 | RELATED → DIFFERENT | OpenAI 主体与跨 36h 关联 | 已修复为跨窗口相关 |
| gold-022 | RELATED → DIFFERENT | 中文“AI供应链”主题漏召回 | 仍存在 |
| gold-025 | RELATED → DIFFERENT | 汽车软件主题与 Rivian 实体缺失 | 仍存在 |
| gold-027 | DIFFERENT → RELATED | 只因 earnings + AI 被判相关 | 已修复 |
| gold-028 | DIFFERENT → RELATED | 宽泛 policy 关键词碰撞 | 已修复 |
| gold-035 | DIFFERENT → RELATED | 同 ticker 无共同动作被判相关 | 仍存在于三分类；不会合并 |

原文节选、系统理由和修复建议见 `research/ben_radar_p04/02_cluster_error_analysis.md`。

## 为什么过去“新闻 + X = 0”

2026-08-16 20:39 UTC+8 的 72 小时诊断：51 条合格新闻、40 条合格 X，跨平台进入候选召回 70 对；最终 `SAME_EVENT` 2 对、`RELATED_BUT_DISTINCT` 52 对、`DIFFERENT_EVENT` 16 对。24 小时首页实际形成 1 个新闻 + X 共同事件。

五类证据：

1. **真实内容重叠有限**：70 个候选对只有 2 对通过严格同事件判断，大部分只是同公司/主题。
2. **来源链接不对齐**：新闻与 X 的共享规范化外链为 0；X 常链 Bloomberg/Focus Taiwan，而新闻池主要是 Yahoo/CNBC/Investing。
3. **召回曾不足**：Qwen、Claude、SpaceX、Peter Thiel 等没有 ticker 的专名在初版漏召回，P04 已加入 actor token。
4. **指纹不完整**：候选对中 58 对没有共同实体、23 对没有共同 actor、41 对没有共同 action、70 对均没有共同 target/number，说明只靠标题仍难确认。
5. **时间窗影响**：发现 4 对共享实体/主体但相差超过 36 小时；应标记跨窗口相关，不能塞进同一稳定事件。

## 可复核入口

- Benchmark：`python scripts/benchmark_ben_clusters.py run --gold research/ben_radar_p04/event_cluster_gold.jsonl`
- 真实快照：`python scripts/validate_ben_p04.py --db data/taiwan-demo.db`
- 诊断页：`GET /stock-radar/cluster-diagnostics`

诊断页显示 pair/event ID、左右指纹、合并/拒绝原因、相似度、实体、actor、action、target、数字、时差和来源类型；这些技术字段没有进入主首页。
