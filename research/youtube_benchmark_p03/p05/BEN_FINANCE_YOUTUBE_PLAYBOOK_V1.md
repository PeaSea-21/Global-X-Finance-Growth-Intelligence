# BEN Finance YouTube Playbook V1

> 适用日：2026-08-17。`BEN Topic Score V1` 是编辑决策启发式，不是已验证增长规律。Benchmark 只提供可测试假设；财经事实必须来自 Evidence Pack。

## 1. Content Tracks

- `TRACK_A_TAIWAN`：回答“今天发生的事情，对台湾股票投资者意味着什么？”
- `TRACK_B_US_AI`：回答“这个 AI / 美股事件真正改变了什么？”
- `TRACK_C_MACRO`：回答“宏观事件通过什么链条影响股票？”

## 2. Qualification Gate

依序检查：G1 真实事件；G2 财务/估值/产业相关；G3 有解释缺口；G4 至少一个可靠事实来源。G1 失败直接 REJECT；G4 弱则降级并要求人工复核。传言、来源冲突或事实不足不得伪装成 READY。

## 3. Topic Score

总分 100：Market Impact 20、Audience Relevance 15、Freshness 15、Evidence Strength 15、Explanation Gap 10、Packaging 10、Visual 5、Shelf Life 5、Differentiation 5。每项必须记录分数、理由、证据与置信度。80–100=A，65–79=B，50–64=C，低于 50=SKIP。临界分、预测、冲突源和证据不足均设 `human_review_required=true`。

## 4. Format Router

1. `FORMAT_01_SINGLE_DECISION_QUESTION`：对象→问题→证据→正面→风险→观察条件。
2. `FORMAT_02_THREE_ITEM_UPDATE_LEDGER`：三事件→各自影响→共同主题→明日观察。
3. `FORMAT_03_MACRO_TO_MICRO_CHAIN`：宏观→数据→金融变量→行业→公司→股票→风险。
4. `FORMAT_04_CONSENSUS_CHALLENGE`：主流观点→被忽略数据→替代解释→二阶影响→反方→条件结论。
5. `FORMAT_05_DATA_LED_DEEP_DIVE`：关键数据→比较→驱动→影响→情景→下一数据。
6. `FORMAT_06_EVENT_EXPLAINER`：发生什么→确认事实→为何重要→谁受影响→下一观察。

Router 先看观众任务而非字数。证据：`BF01/BP01–BP03`。三项更新在 P04 是稳定品牌格式，不是已证实爆款因子。

## 5. Evidence Rules

先建 Evidence Pack 后写脚本。每条事实必须有 `evidence_id/source/source_type/timestamp/confidence/usable_claim/forbidden_overclaim`。优先官方 IR、监管机构、政府/一级数据；公司指引始终归因并标为未来。`CREATOR_OPINION` 永不自动升级为事实。旧季度数据必须标日期，不得冒充最新季度。

## 6. Title System

每题先产六种机制：T1 决策问题、T2 数字、T3 市场影响、T4 解释缺口、T5 共识挑战、T6 风险/机会。不是同义改写。标题中的数字必须在 Evidence Pack；禁止 fake urgency、确定涨跌、目标价和收益承诺。每次实验尽量只变标题。

## 7. Thumbnail System

每题产三套：TH-A 问题压缩、TH-B 数字证明、TH-C 证据主体。标题给范围，封面给主问题或补充证据；优先 completion 而非重复。只设一个主层级、最多两个次元素，并做手机尺寸审阅。证据 `BF09/BF10/BP04/BP05`；没有 CTR，不能宣称某版式有效。

## 8. Hook System

0–10 秒直接给事件与真实冲突；10–30 秒说明为何重要、观众会得到什么、最大未知是什么。禁止让“大家好欢迎回来”占据核心 Hook。Hook 必须兑现标题和封面，不加入 Evidence Pack 外的新数字。

## 9. Content Brief

固定字段：Core Question、Audience Promise、Verified Facts、Unknowns、Interpretation、Recommended Format、Opening、Context、Evidence、Interpretation、Counterpoint、Conclusion、Watch Next。事实与解释分栏；Unknowns 不可隐藏。

## 10. Finance QA

- Fact Gate：每个数字可追溯。
- Attribution Gate：管理层、机构与分析者观点分别标示。
- Time Gate：过去、当前、未来准确标记。
- Prediction Gate：只写 scenario + uncertainty + condition。
- Investment Advice Gate：无无依据买入、确定收益或虚构目标价。

任一关键数字无证据即 `FAIL`；事实够但需判断/更新为 `REVIEW`；全部通过为 `PASS`。

## 11. Production Queue

使用 `production_queue.json` 的 `NEXT 12 VIDEOS`。编辑只从 `READY` 取题；`NEED_EVIDENCE` 先补一级来源，`NEED_REVIEW` 先人工判断，`HOLD` 等事件/窗口。取题后冻结 topic_id、证据版本与测试变量。

## 12. Measurement

发布前填写 hypothesis、topic_score、format、title/thumbnail pattern、expected result；未知指标保持 null。24h 看初始 reach/CTR/早期 retention，72h 看更稳定的包装与观看，7d 做 `SUPPORTED/REJECTED/INCONCLUSIVE`。相对表现只与自有频道、相近 Track/年龄基线比较。

## 13. Diagnosis

- Low impressions：先查分发、topic demand、频道历史。
- High impressions + low CTR：查标题、封面、promise。
- Good CTR + poor 30s：查 hook mismatch、慢开场、承诺错配。
- Good 30s + poor AVD：查节奏、密度、结构、重复。
- Good watch + low engagement：查效用、情绪相关、CTA、受众。
- Good metrics + low absolute views：可能是 distribution limitation，勿立即否定内容。

## 14. Experiment

一次尽量只改 title、thumbnail、hook 或 format 之一。现实无法控制时标 `QUASI_EXPERIMENT` 并记录 confounds。假设库见 `experiment_hypotheses.json`：10 个标题、8 个封面，全部从 P04 证据转成低置信可检验命题。

## 15. Learning Loop

BEFORE PUBLISH 冻结假设；24H/72H 留快照；7D 判断。LOW=Benchmark observation；MEDIUM=多个独立 Benchmark 一致或自有 2–3 次同方向；HIGH 必须主要靠自有重复实验。单条 15.2243× breakout 不能升级 HIGH。

## 16. Do / Don't

Do：先证据后脚本；写清时间；一个主承诺；保留反证；记录未知；只与自有基线比较；每轮只学一个变量。

Don't：把创作者视频当事实；模仿人格/口头禅；把相关性写因果；用旧闻冒充今天；用公司指引当结果；同时改所有变量；自动发布；用缺失数据补零或造数。

## 编辑每日 Decision Flow

1. 事件是真的吗？
2. 影响市场吗？
3. 逐项打 Topic Score。
4. 分配 Track。
5. Router 选 Format。
6. 建 Evidence Pack。
7. 设计 6 Title × 3 Thumbnail，确定唯一测试变量。
8. 完成 Content Brief 与 0–30 秒 Hook。
9. 跑 Finance QA；只有 PASS 才进入 READY。
10. 人工发布（本系统不自动发布）。
11. 记录 24H / 72H / 7D。
12. 更新假设为 SUPPORTED / REJECTED / INCONCLUSIVE，不以单条升级 HIGH。
