# EXECUTIVE FINDINGS

研究范围：3 个已核验频道、每频道 10 条、合计 30 条真实视频；元数据与播放快照来自 2026-08-16 已缓存的 YouTube 官方公开 Atom 频道资料，缩略图于同日从 `i.ytimg.com` 成功取得并逐张人工核看。表现结论只做同频道相对比较；`correlation ≠ causation`。

## 1. 三个频道不是同一种点击模型

**Finding**：台股频道主要把议题压成“现在该怎么看”的单一问题；科技频道把一集包装成三项科技事件账本；宏观频道用研究员/来宾与“宏观条件 → 产业影响”承诺建立解释权威。

**Evidence**：台股样本 7/10 标题为问句；科技样本 10/10 使用统一系列角标、主持人、证据截图和三行议题摘要；宏观样本 10/10 使用播客/研究品牌视觉，5/10 为棚景多人、5/10 为图表或字幕式直式切片。证据：全部 30 个 video ID，见 [video_dataset.json](video_dataset.json)。

**Confidence**：HIGH（包装层）；LOW（真实口播叙事层）。

**Why it matters**：内容团队应先选“点击任务”——决策、更新或解释——再写标题与封面，不能只换关键词。

**Action**：同一事实题同时 A/B 测试“单一问题”“三项更新”“因果解释”三类包装，正文事实保持不变。

## 2. 问句是台股频道的品牌基线，不是已证实的增长按钮

**Finding**：问句很常见，但现有样本不足以证明“加问号就会提高表现”。

**Evidence**：台股 7/10 标题含问句；三条 `ABOVE_BASELINE` 中两条含问句（`9Ckyf26ASg4`、`sgHsCaH2umQ`），另一条 `Iir132pvy-A` 是强机会陈述。全样本可比问句标题 13 条，其中 5 条为 ABOVE/BREAKOUT（38.5%）。

**Confidence**：MEDIUM（频率）；LOW（效果归因）。

**Why it matters**：问句适合界定问题，但不能替代具体对象、事件和证据。

**Action**：测试“公司/对象 + 明确事件 + 单一问题”，并设一组无问号的事实型标题作为对照。

## 3. 科技频道的统一三行封面更像品牌系统，而非单片爆款因子

**Finding**：科技频道高低表现视频都使用同一高密度版式，因此不能把该版式单独解释为高表现原因。

**Evidence**：10/10 有主持人或来宾、资料截图、系列角标与三行议题摘要；三条 ABOVE 为 `UBqg6zio5SE`、`lcA6hGaZsOM`、`3tAUC5Zg8rw`，三条 BELOW 为 `fT4GIObuq-s`、`9Mi0xxoIUbc`、`_F1XFJs3t9Y`，包装骨架相同。

**Confidence**：HIGH。

**Why it matters**：统一版式可降低认知成本，但真正的差异更可能来自议题组合、时点、来宾或分发。

**Action**：保留稳定视觉骨架，只变更首议题、影响暗示和封面信息优先级；不要同时改完所有元素。

## 4. 宏观频道唯一 BREAKOUT 是“专家 + 长周期叙事”，但仍是单例

**Finding**：`Iv66HJtx2AY` 是 30 条中唯一满足频道内 IQR 上界的 BREAKOUT；它用专家身份和“金融海啸到 AI 浪潮”的长周期桥接，而不是纯突发新闻。

**Evidence**：年龄校正 `performance_ratio=15.2243`；宏观频道 breakout fence 为 4.1081。缩略图为两人棚景、专家/研究身份与“AI 关键转机”主题块。样本 ID：`Iv66HJtx2AY`。

**Confidence**：MEDIUM（异常值存在）；LOW（机制归因，只有一条且来宾/分发混杂）。

**Why it matters**：evergreen 的长周期解释也可能跑出，不必只追即时新闻。

**Action**：做一条“历史阶段 → 当前数据 → 下一验证点”的专家解释型试片，并与同主题纯新闻版比较。

## 5. 30 条中建立了可用但仍属 provisional 的频道内基线

**Finding**：年龄校正后得到 ABOVE 8、BREAKOUT 1、NORMAL 12、BELOW 7；另有 2 条发布不足 24 小时，明确不参与比较。

**Evidence**：台股 9 条可比，3 ABOVE；科技 10 条可比，3 ABOVE；宏观 9 条可比，2 ABOVE、1 BREAKOUT。方法与阈值见 [performance_analysis.json](performance_analysis.json)。

**Confidence**：MEDIUM。

**Why it matters**：可以开始用自身分布找候选，不再跨频道比较绝对播放数。

**Action**：未来滚动扩至每频道 30–50 条，并补时长、正式视频类型与发布时间段后重估模型。

## 6. AI 最常见，但“最常见”不等于“最容易跑赢”

**Finding**：AI 是出现最多的标签，表现接近频道基线；本样本中宏观与财报标签的中位相对表现更高，但后者样本小。

**Evidence**：AI 14 条，中位比率 1.0038；台湾股票 10 条，0.9879；半导体 8 条，0.9088；全球宏观 5 条，1.4222；财报 3 条，1.8660。主题允许多标签。

**Confidence**：MEDIUM（AI/台股/半导体）；LOW（财报等小组）。

**Why it matters**：热点标签只提供入场券，必须再加结构性问题或证据价值。

**Action**：AI 选题不做泛资讯，优先叠加“财报验证”“供应链压力点”或“宏观传导”之一。

## 7. 机会词与高表现共同出现得比纯风险词多，但频道与题材严重混杂

**Finding**：可比样本中，含机会信号的 10 条有 5 条 ABOVE/BREAKOUT；含风险信号的 8 条只有 2 条。不能据此断言机会词导致增长。

**Evidence**：机会样本高表现率 50%；风险样本 25%；breaking framing 6 条中 3 条高表现。高表现例：`Iir132pvy-A`、`9Ckyf26ASg4`、`3tAUC5Zg8rw`；风险低表现例亦存在。

**Confidence**：LOW。

**Why it matters**：观众可能更愿意点击“机会 + 条件”，但夸大机会会损害财经可信度。

**Action**：测试“正面催化 + 一项明确限制”，不要测试无证据的财富暗示。

## 8. 标题长度反映节目任务，不宜用统一字数规则

**Finding**：科技清单标题最长，台股单题标题最短，宏观居中；长度差异主要来自内容单元数量。

**Evidence**：平均标题长度：台股 29.4 字符、科技 44.4、宏观 37.5。科技高低表现均维持长标题。

**Confidence**：HIGH（描述）；LOW（表现因果）。

**Why it matters**：标题优化应先限制承诺数量，再决定字数，而不是机械追求短标题。

**Action**：单题视频只保留一个问题；周更 roundup 可保留三项，但封面必须建立清楚先后级。

## 9. 高表现封面没有单一共同公式，最稳定的是“清楚层级”

**Finding**：9 条 ABOVE/BREAKOUT 横跨强情绪人物、统一科技清单、专家棚景三类；共同点不是颜色或人数，而是移动端能辨认的一个主层级。

**Evidence**：台股 ABOVE 包含多股大字盘面、强机会陈述和人物问句；科技 ABOVE 仍是统一三行摘要；宏观 BREAKOUT 是双人棚景与单一主题块。30/30 人工核看，联系图见 [台股](evidence/thumbnail_contact_tw.jpg)、[科技](evidence/thumbnail_contact_tech.jpg)、[宏观](evidence/thumbnail_contact_macro.jpg)。

**Confidence**：MEDIUM。

**Why it matters**：复制某种红黄配色没有依据；先解决视觉优先级更可靠。

**Action**：每张封面只指定一个主问题/主数字，次级证据最多两块，并进行手机尺寸审阅。

## 10. 标题与封面应分工；简单重复只适合极短决策题

**Finding**：台股封面常重复或放大标题问题；科技封面重复并补全三项 agenda；宏观封面更常补充专家身份、图表或因果落点。

**Evidence**：台股视觉关系以 `RESTATES/AMPLIFIES` 为主；科技 10/10 为 `RESTATES_AND_SUMMARIZES`；宏观棚景多为 `COMPLEMENTS`，直式切片偏 `RESTATES`。逐条字段见数据集。

**Confidence**：HIGH。

**Why it matters**：复杂题若标题与封面只说同一句，会浪费第二个信息面。

**Action**：台股单题可用 question–answer；科技 roundup 用 completion；宏观解释用 authority-proof 或 number-proof，但证据必须真实。

# 研究范围与方法

- 频道固定：老王愛說笑、M觀點、MacroMicro財經M平方；身份核验沿用 P03 的官方 channel ID。
- 样本：每频道 10 条，保留 P03 原 3×3，并从同一 15 条官方公开缓存中扩展普通、近期与高表现候选；没有只挑爆款。
- 元数据：标题、精确发布时间、播放快照、缩略图 URL 可用；duration、likes、comments、正式 video type、caption availability 未从批准通道可靠取得，保留 `UNAVAILABLE/UNKNOWN/NOT_RUN`。
- 表现：排除不足 24 小时视频；在频道内拟合 `log(age_days) → log(views)`，以实际播放 / 年龄期望播放形成 ratio；Q25 以下 BELOW、Q25–Q75 NORMAL、Q75 以上 ABOVE、超过 `Q75 + 1.5×IQR` 为 BREAKOUT。
- 视觉：30 张公开缩略图均实际下载与人工检查；没有从 URL 或标题猜图。
- 内容：没有请求、播放或存储完整字幕；前 30 秒、节奏、口头表达、CTA 均不作伪推断。
- 财经事实：创作者视频只作 benchmark source；原创内容只使用 P03 已锁定的台积电官方 FactPack。

# Topic / Title / Thumbnail Benchmark

## Topic

| 主题 | 可比视频数 | 频道内表现比率中位数 | 置信度 | 解释 |
|---|---:|---:|---|---|
| AI | 14 | 1.0038 | MEDIUM | 最高频，接近基线；热点本身不保证跑赢 |
| 台湾股票 | 10 | 0.9879 | MEDIUM | 高频，表现分化，需依对象/事件细分 |
| 半导体 | 8 | 0.9088 | MEDIUM | 频繁但本窗口不高于基线 |
| 美股 | 6 | 0.9649 | MEDIUM | 接近基线 |
| 全球宏观 | 5 | 1.4222 | MEDIUM | 较高，但含节目/来宾混杂 |
| 财报 | 3 | 1.8660 | LOW | 较高，小样本 |
| 利率 | 2 | 0.2124 | LOW | 较低，小样本，不能泛化 |

热点倾向：具体模型/公司调整、财报、非农/通胀、市场新高。Evergreen 倾向：历史周期、ETF 选择、估值方法、利率机制、风险管理。两类都存在高表现样本；本轮没有观看时长，不能比较长尾寿命。

## Title

| 频道 | 平均长度 | 问句 | 急迫 | 恐惧 | 机会 | 主结构 |
|---|---:|---:|---:|---:|---:|---|
| 老王愛說笑 | 29.4 | 7/10 | 4/10 | 1/10 | 5/10 | 单对象/多股决策问句 |
| M觀點 | 44.4 | 4/10 | 5/10 | 4/10 | 4/10 | 三议题科技更新账本 |
| MacroMicro財經M平方 | 37.5 | 4/10 | 2/10 | 5/10 | 2/10 | 宏观事件/专家/产业影响 |

高频抽象结构：

- `对象/事件 + 能否/如何 + 条件或风险`
- `议题 A + 议题 B + 议题 C`
- `宏观数据/历史阶段 + 产业或资产影响`
- `权威角色 + 带你理解 + 关键机制`
- `强结果 + 反方限制 + 下一观察点`

## Thumbnail

| 频道 | 人物 | 证据画面 | 文字密度 | 主要关系 |
|---|---|---|---|---|
| 老王愛說笑 | 8/10 单人；2/10 无人 | 6/10 图表，3/10 截图 | 4/10 HIGH | repetition / amplification / question-answer |
| M觀點 | 8/10 单人；2/10 多人 | 10/10 截图，3/10 图表 | 10/10 HIGH | repetition + completion |
| MacroMicro財經M平方 | 5/10 多人；5/10 单人或小面板 | 5/10 截图，4/10 图表 | 5/10 HIGH | completion / authority-proof / repetition |

没有 impressions 与 CTR，任何“封面提升点击率”的说法都不成立；这里只报告共现与可测试假设。

# 老板关心的 12 个问题

## 1. 三个频道分别主要靠什么吸引点击？

- 台股：具体股票/ETF + 机会或风险 + 直接问句，人物手势或盘面大字强化。
- 科技：一次更新三件重要事，统一主持人/截图/三行摘要降低识别成本。
- 宏观：专家或研究员权威、宏观到产业的解释承诺、图表/棚景补充可信感。

## 2. 哪些选题最常出现？

AI 14、台湾股票 10、半导体 8、美股 6、全球宏观 5；主题为多标签计数。

## 3. 哪些选题最容易跑赢自身频道基线？

本窗口中财报中位比率 1.866（n=3，LOW）、全球宏观 1.4222（n=5，MEDIUM）较高；AI 1.0038（n=14）接近基线。不能把小样本排序当长期规律。

## 4. 哪些标题结构最常见？

台股单一问句、科技三议题清单、宏观事件到产业影响；具体结构见 Title Benchmark。

## 5. 哪些标题结构与更高表现共同出现？

机会词 10 条中 5 条高表现；breaking 6 条中 3 条；问句 13 条中 5 条。科技高表现仍采用三议题清单，但低表现也相同。相关不等于因果。

## 6. 哪些 thumbnail 结构最常见？

人物 + 大字最普遍；科技再叠证据截图与系列角标，宏观再叠棚景/专家标签或图表，台股常配 K 线/盘面。

## 7. 高表现视频的 thumbnail 有什么共同特征？

没有统一颜色、人数或图表公式；较一致的是一个可辨识的主层级。台股的强情绪人物、科技的稳定三行摘要、宏观的专家棚景都能进入高表现组。

## 8. 热点与 evergreen 分别怎么包装？

热点：具体公司/模型/财报 + 时效词 + 屏幕证据；evergreen：历史跨度/方法问题 + 专家或解释权威 + 单一机制。宏观唯一 BREAKOUT 属于后者，但只有单例。

## 9. 前 30 秒有什么规律？

`UNKNOWN / TRANSCRIPT_UNAVAILABLE`。本轮没有合法字幕或视频播放证据，不能从标题与封面虚构 hook。

## 10. 哪类 evidence 最能提升财经内容可信度？

一级来源（公司 IR、财报、央行、政府/交易所数据）才能支撑事实；图表、截图与专家身份只能提升“证据感”，不能代替核验。原创样稿的重要数字全部映射至台积电 IR FactPack。

## 11. 哪些模式适合我们做？

- 台湾股票：单一决策问句、事件到影响、风险/机会双信号。
- 美股：三议题更新账本、财报共识挑战。
- AI/半导体：供应链落点、数据矩阵、公司事件到产业影响。
- 宏观：宏观条件到产业传导、专家/研究员解释、历史阶段到当前验证点。

## 12. 哪些不应该复制？

频道名、节目名、主持人肖像/身份、独有口头禅、固定开场、个人经历、原缩略图文案、原句；也不应复制夸张承诺或把创作者观点当事实。

# BEN CONTENT RECOMMENDATION

## Taiwan Finance

### Topic directions

1. 台股产业事件 → 受影响环节 → 下一官方数据；证据 `fZg4vn7D4XM`、`8gn2VKtwHRI`、`sgHsCaH2umQ`；Confidence MEDIUM。
2. ETF/杠杆产品的条件与风险边界；证据 `vdW1eELwnsk`、`i_gEGJDcWu8`；Confidence LOW。
3. 台积电/半导体财报结构，而非单一涨跌预测；证据 `8GxNAzIg3CM` 加本轮官方 FactPack；Confidence MEDIUM。

### Title patterns

1. `具体对象 + 发生什么 + 一项决策问题`；证据台股问句 7/10；Confidence MEDIUM。
2. `强结果 + 哪个环节贡献 + 一个限制`；证据 PAT-07；Confidence LOW_TO_MEDIUM。
3. `多股事件清单 + 共同产业线索`；证据 `9Ckyf26ASg4`（ABOVE 1.9523）；Confidence LOW（单一高样本）。

### Thumbnail patterns

1. 单一主问题 + 主体人物或对象，最多两层；证据台股 8/10 单人；Confidence HIGH。
2. 问题在标题、关键数据在封面，做 completion；证据 Title×Thumbnail 对比；Confidence MEDIUM。
3. 若用盘面截图，只保留一个对象与一个结论区；证据 `8gn2VKtwHRI`、`0byAdzUmaos`；Confidence MEDIUM。

### Narrative patterns

1. Event-to-Impact：事件 → 官方数据 → 产业影响 → 验证点；Confidence MEDIUM。
2. Decision Explainer：问题 → 条件 → 反例 → 风险边界；Confidence MEDIUM。
3. Consensus Challenge：市场简化理解 → 冲突数据 → 二阶影响 → 限制；Confidence MEDIUM。以上为高层模板，口播规律仍待 transcript。

## US Stocks / AI

### Topic directions

1. AI 公司财报与估值验证；证据财报标签中位 1.866、`RolkbaZOwQg`、`fcZ1mOQr6BY`；Confidence LOW_TO_MEDIUM。
2. 模型/产品事件 → 商业或算力影响；证据科技频道 10 条多议题更新；Confidence MEDIUM。
3. AI 政策/地缘 → 公司与供应链二阶影响；证据 `9Mi0xxoIUbc`、`LjLONE12zFs`；Confidence LOW_TO_MEDIUM。

### Title patterns

1. `公司事件 A + 公司事件 B + 共同市场问题`；证据科技 10/10 多议题；Confidence HIGH（频率）。
2. `财报结果 + 市场共识 + 被忽略指标`；证据 PAT-07；Confidence MEDIUM。
3. `技术发布 + 商业含义 + 谁受影响`；证据科技/AI 样本；Confidence MEDIUM。

### Thumbnail patterns

1. 主持/专家锚点 + 一张真实资料画面 + 三行以内摘要；证据科技 10/10；Confidence HIGH。
2. 首议题大于次议题，避免三项同权；来自科技高低样本对照；Confidence MEDIUM（待 A/B）。
3. 财报用一个指标作 number-proof，不用股价箭头；来自宏观/科技截图模式；Confidence MEDIUM。

### Narrative patterns

1. Three-item Update Ledger；Confidence HIGH（包装）/LOW（口播顺序）。
2. Data-led Deep Dive：指标 → 驱动 → 产业影响 → 情境；Confidence MEDIUM。
3. Evidence First：官方资料 → 解释 → 反方风险 → 观察清单；Confidence HIGH（治理适配）。

## Macro

### Topic directions

1. 宏观数据 → AI/半导体传导；证据 `4gEpLNIRhhk`；Confidence LOW_TO_MEDIUM。
2. 财报季与货币政策并列观察；证据 `zkeWUsTC09E`（ABOVE 1.8660）；Confidence LOW。
3. 历史周期 → 当前结构 → 下一验证点；证据 `Iv66HJtx2AY`（BREAKOUT 15.2243）；Confidence LOW_TO_MEDIUM。

### Title patterns

1. `宏观事件 + 产业反应 + 能否延续`；证据 `4gEpLNIRhhk`；Confidence LOW。
2. `历史阶段 A → 当前趋势 B + 专家解释`；证据唯一 BREAKOUT；Confidence LOW。
3. `数据/政策角色 + 各自观察指标`；证据 `zkeWUsTC09E`；Confidence LOW。

### Thumbnail patterns

1. 专家棚景 + 单一因果问题；宏观 5/10 多人；Confidence MEDIUM。
2. 图表切片 + 一句“压力落点”；宏观 4/10 图表；Confidence MEDIUM。
3. 已发生数据与未来情境分色，避免把预测画成事实；Benchmark + FactPack 治理；Confidence HIGH。

### Narrative patterns

1. Macro-to-Micro Causal Chain；Confidence MEDIUM。
2. Historical Bridge：历史相似/差异 → 当前数据 → 反证；Confidence LOW_TO_MEDIUM。
3. Scenario Boundary：基准情境 → 上下行条件 → 下一官方数据；Confidence HIGH（适合财经风险控制）。

# Channel Profile V2 摘要

四层画像、证据 ID 与置信度见 [channel_profiles_v2.json](channel_profiles_v2.json)。Topic 与 Packaging 已可用；Narrative 因无字幕保持 LOW；Performance 因 10 条小样本及 duration/type 缺失保持 MEDIUM 或 LOW_TO_MEDIUM。

# 原创生产结果

[youtube_x_samples_v2.md](youtube_x_samples_v2.md) 已完成：News Explainer、Consensus Challenge、Data-led Deep Dive 三组；每组包含 YouTube 标题 5 个、缩略图概念 3 个、开头钩子、口播大纲、X 短帖、X 中帖与 thread 大纲。三组共享 `F001–F007`，重要数字均链接至台积电官方来源。

# Readiness

| 维度 | 状态 | 依据 |
|---|---|---|
| CORE | READY | P03 Skill 沿用；P04 8 个核心交付齐全 |
| METADATA | PARTIAL | 30/30 标题、时间、播放、缩略图；duration/likes/comments/type/caption 未补齐 |
| PERFORMANCE | PARTIAL | 28 条可比、频道内年龄校正基线已建；格式/时长/曝光未控制 |
| VISUAL | READY | 30/30 实际核看并保留三张联系图 |
| TRANSCRIPT | NOT_READY | 0/30；TranscriptAPI DISABLED，未请求字幕 |
| PROFILE | PARTIAL | Topic/Packaging 可用；Narrative 仍低置信 |
| PATTERN_LIBRARY | READY | 7 个 creator-neutral、证据链接模式 |
| GENERATION | READY | 三套 YouTube/X V2 与证据映射完成 |

**Overall：`P04_PARTIAL_READY`。**
