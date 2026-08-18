# P04 聚类错误分析

## Benchmark 迭代

| 版本 | TP | FP | TN | FN | Precision | Recall | F1 | 错误对数 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 两阶段初版 | 1 | 0 | 39 | 5 | 100.00% | 16.67% | 28.57% | 15 |
| 主体/金额归一后 | 3 | 0 | 39 | 3 | 100.00% | 50.00% | 66.67% | 8 |
| P04 最终版 | 5 | 0 | 39 | 1 | 100.00% | 83.33% | 90.91% | 5 |

说明：TP/FP/TN/FN 把 `SAME_EVENT` 当作正类；三分类准确率另见 Benchmark 交付物。所有数字来自同一份 45 对 Gold 的真实运行，不是人工回填。

## 至少 10 个实际错误案例

下表记录实际 Benchmark 迭代中出现过的错误；“已修复”仍保留，避免只展示最终好看的数字。

| Gold ID | 原文 A / 原文 B（节选） | Gold → 系统 | 原因 | 处理 |
|---|---|---|---|---|
| gold-002 | `Nvidia weighs $3 bln in SB Energy...` / `Nvidia in talks to invest $3 billion in SB Energy...` | SAME → RELATED | `bln` 与 `billion` 未归一，造成关键金额冲突。 | 已修复：金额 scale 规范化。 |
| gold-003 | `Peter Thiel buys 1% stake in ... Vista Energy` / `Billionaire Peter Thiel buys 1% stake...` | SAME → RELATED | 无 ticker，主体短语被整段抽取，交集为空。 | 已修复：人名/机构拆分为 unigram、bigram 与完整短语。 |
| gold-004 | Peter Thiel/Vista 新闻 / Bloomberg X 的 `Thiel Macro...Vista...` | SAME → DIFFERENT | 新闻与 X 对同一主体使用不同命名。 | 已修复：主体 n-gram 与动作共同确认。 |
| gold-005 | Vaca Muerta oil firm 新闻 / `Thiel Macro...Vista` X | SAME → RELATED | 一侧缺少 Vista 名称，只共享 `Thiel`；目标别名未解析。 | **仍存在**：应增加 Vista/Vaca Muerta 实体别名，但不能泛化合并所有 Thiel 投资。 |
| gold-006 | `Nvidia discloses $21 billion stake in SpaceX...` / 中文 X 讨论 Nvidia Q2 的 Intel、SpaceX 持股 | SAME → RELATED | 中英文数字单位不一致，X 同时加入额外持仓。 | 已修复：Nvidia + SpaceX 两个主体与 investment 动作共同确认。 |
| gold-007 | 两条 Qwen3.8-27B 帖：笔电运行 / Hugging Face 榜首 | RELATED → DIFFERENT | 产品名未进入实体字典，候选召回失败。 | 已修复：大小写/数字混合产品 token 进入 actor。 |
| gold-014 | `AI半導體熱潮...投資台積電...` / `法人看AI趨勢未變 台股...通膨` | RELATED → DIFFERENT | 中文主题词表对第二条只命中宏观，未命中 AI。 | **仍存在**：补充中文 AI 边界识别，仍保持 distinct。 |
| gold-017 | Claude Model Comparison / Claude desktop Browser | RELATED → DIFFERENT | Claude/Anthropic 未作为可共享主体召回。 | 已修复：专名主体召回；严格层保持不同事件。 |
| gold-020 | Nvidia 持有 SpaceX 新闻 / `Can SpaceX Leap to the AI Frontier?` | RELATED → DIFFERENT | 第二条缺 ticker，SpaceX 未作为共享主体。 | 已修复：专名 actor 召回。 |
| gold-021 | OpenAI 广告隐私政策 / OpenAI IPO 前人才流失 | RELATED → DIFFERENT | OpenAI 未作为主体且时差超过 36 小时。 | 已修复为跨窗口相关；不会合并成同事件。 |
| gold-022 | `台股...聚焦AI供應鏈` / `台股...AI族群續強` | RELATED → DIFFERENT | 第一条未命中 AI 主题，候选召回失败。 | **仍存在**：主题词边界需补强。 |
| gold-025 | 软件定义汽车寿命 / Tesla、Rivian 辅助驾驶体验 | RELATED → DIFFERENT | 第一条没有识别 Tesla/Rivian，汽车主题也未建模。 | **仍存在**：后续增加汽车软件实体与主题。 |
| gold-027 | Anthropic 营收 / 台湾服务器导轨公司获利 | DIFFERENT → RELATED | 仅因 `earnings + AI` 被判相关。 | 已修复：无共同实体/主体且文本低相似时判不同。 |
| gold-028 | OpenAI 隐私政策 / 哥伦比亚地震后关税请求 | DIFFERENT → RELATED | 宽泛 `policy` 与政策主题碰撞。 | 已修复：主题和动作不能单独构成 related。 |
| gold-035 | 台湾产业风险评论提台积电 / 台积电联合征才 | DIFFERENT → RELATED | 同 ticker 被宽松判为相关。 | **仍存在**：三分类边界把“同公司无共同动作”视为 related；生产合并层不会合并。 |

## 当前风险

- 最终 `SAME_EVENT` Precision 为 100%，但 6 个正样本很小，不能外推成生产 SLA。
- 当前优先保护“不误聚类”，因此仍有 1 个 `SAME_EVENT` 漏聚类。
- 中文主题召回和别名解析仍是 `RELATED_BUT_DISTINCT` 三分类的主要短板。
- 页面 24 小时事件数未因调低阈值而虚假下降；这是有意取舍。
