# P05 Executive Summary

> Status: `P05_READY` as of 2026-08-17. This means the editorial operating package is usable; it does not mean any growth hypothesis is proven.

## A. P04 后真正学到什么

- 先决定观众任务：单一决策、三项更新或宏观解释，再选标题与封面。证据 `BF01 / BP01–BP03`；包装观察较强，口播层仍未知。
- 财报与宏观在小样本里表现较高，但样本很小；AI 高频却接近频道基线。证据 `BF04 / BF06`。
- 高表现封面没有统一颜色或人物公式；更稳定的是一个清楚主层级，以及标题—封面分工。证据 `BF09 / BF10 / BP05`。
- 机会词与高表现共同出现较多，但频道、题材与时点混杂；可测试‘催化 + 限制’，不可宣称会提升表现。证据 `BF07 / BP07`。

## B. 哪些只属于相关性

问句、机会词、专家棚景、三行科技账本、财报/宏观标签与表现的关系全部是相关性。唯一 15.2243× BREAKOUT 只是单例；没有 impressions、CTR、watch time 或 transcript，不能做因果归因，也不能模仿创作者人格。

## C. 准备测试什么

建立 40 个真实候选（Taiwan 15 / US-AI 15 / Macro 10），并选出 12 个制作测试（5 / 4 / 3）。队列包含 12 条 `READY`；每条有 Evidence Pack、6 个标题、3 个封面、原创 0–30 秒 Hook 与 Finance QA。

优先测试：单一决策问句、主数字 + 质量问题、真实数字冲突、宏观到股票传导、标题—封面 completion。每次只改一个主要变量；无法控制时标记 `QUASI_EXPERIMENT`。

## D. 为什么是这 12 条

不是单纯拿最高分，而是覆盖 Breaking、Earnings、AI、Semiconductor、Macro、Evergreen、Risk、Opportunity、Company-specific 与 Data-driven，并在三个固定 Track 中保留 5/4/3 配比。所有 READY 题均至少有一项官方/公司一级证据。

## E. 成功看什么

先看 impressions 是否足以评价包装，再看 CTR；随后看 first_30s_retention、avg_view_duration、avg_percentage_viewed，最后结合 engagement 和 24h/72h/7d 的频道内相对表现。缺失数据必须保持 `null`。

## F. 何时才知道 Pattern 适合自己

不承诺固定天数。每条视频在 24h、72h、7d 留快照，但 Pattern 置信度取决于足够曝光、相近主题下的重复实验和可控变量。单条视频最多产生一个低置信观察；HIGH 必须主要来自自有频道重复实验。

## Top 10 当前选题

| Rank | Topic | Score | Why now | Format |
|---:|---|---:|---|---|
| 1 | Fed 按兵不动却出现三票加息，市场该看哪条传导链？ | 88 | 政策利率未变但投票分歧显著，下一轮通胀与就业数据会检验分歧。 | `FORMAT_03_MACRO_TO_MICRO_CHAIN` |
| 2 | CPI 月增 0.1%、年增 3.4%，降息还是加息更有根据？ | 87 | 这是最新消费通胀数据，恰逢 FOMC 三位委员主张加息后的验证窗口。 | `FORMAT_03_MACRO_TO_MICRO_CHAIN` |
| 3 | AMD 营收增 50%，数据中心翻倍后下一道考题是什么？ | 87 | 这是最新已披露大型 AI 芯片财报，可作为 NVIDIA 财报前的同业事实基线。 | `FORMAT_05_DATA_LED_DEEP_DIVE` |
| 4 | Meta 营收增 28%、成本增 55%，AI 投资回报怎么判断？ | 86 | 财报仍处当前科技财报季，收入与成本分化提供清楚实验题。 | `FORMAT_04_CONSENSUS_CHALLENGE` |
| 5 | 就业减少 2.3 万、失业率 4.1%，坏消息会变成股市利多吗？ | 85 | 最新就业数据与通胀、Fed 投票分歧共同决定政策讨论。 | `FORMAT_04_CONSENSUS_CHALLENGE` |
| 6 | NVIDIA 财报前，AI 需求要由哪三项数据验证？ | 85 | 财报日距本工件 9 天，适合做明确标注的预览与观察清单。 | `FORMAT_01_SINGLE_DECISION_QUESTION` |
| 7 | 美国 GDP 放缓到 1.5%，为何内需指标反而加速？ | 84 | 8 月 26 日将发布第二次估计，当前分项矛盾具持续解释价值。 | `FORMAT_04_CONSENSUS_CHALLENGE` |
| 8 | 台积电 3Q 指引：高成长能否覆盖海外厂稀释？ | 84 | 3Q 指引仍待实际营收和利润率验证，海外厂稀释是明确限制。 | `FORMAT_01_SINGLE_DECISION_QUESTION` |
| 9 | 台湾出口增 40.3%，台股景气真的全面转强吗？ | 83 | 高出口增长与更快的进口增长同时出现，需要解释结构而非只看单一增速。 | `FORMAT_03_MACRO_TO_MICRO_CHAIN` |
| 10 | 2GW 的 AMD–Anthropic 合作，订单、部署与收入差在哪？ | 83 | 2Q 财报再次披露合作，市场需要区分容量框架与已实现收入。 | `FORMAT_04_CONSENSUS_CHALLENGE` |

## NEXT 12 VIDEOS

| # | Track | Topic | Score | Primary title | Status |
|---:|---|---|---:|---|---|
| P05-01 | TRACK_A_TAIWAN | 台积电 3Q 指引：高成长能否覆盖海外厂稀释？ | 84 | 台积电 3Q 指引很强，海外厂会吃掉多少利润？ | `READY` |
| P05-02 | TRACK_A_TAIWAN | AMD Venice 上台积电 2nm，台湾供应链真正新增了什么？ | 82 | AMD Venice 上 2nm，台湾供应链能确认哪些订单？ | `READY` |
| P05-03 | TRACK_A_TAIWAN | 台湾出口增 40.3%，台股景气真的全面转强吗？ | 83 | 台湾出口增 40.3%，台股景气真的全面转强？ | `READY` |
| P05-04 | TRACK_A_TAIWAN | 联电提高资本支出，是需求确认还是周期高点信号？ | 80 | 联电扩产又看好利用率，成熟制程周期真的回来了？ | `READY` |
| P05-05 | TRACK_A_TAIWAN | 台积电营收增长之后，利润与估值要看哪一层？ | 81 | 台积电营收年增 36%，这份财报的增长质量够好吗？ | `READY` |
| P05-06 | TRACK_B_US_AI | NVIDIA 财报前，AI 需求要由哪三项数据验证？ | 85 | NVIDIA 财报前，哪三项数据会真正改变 AI 叙事？ | `READY` |
| P05-07 | TRACK_B_US_AI | Meta 营收增 28%、成本增 55%，AI 投资回报怎么判断？ | 86 | Meta 营收增 28%、成本增 55%，AI 回报看哪里？ | `READY` |
| P05-08 | TRACK_B_US_AI | AMD 营收增 50%，数据中心翻倍后下一道考题是什么？ | 87 | AMD 数据中心翻倍，下一季还能继续兑现吗？ | `READY` |
| P05-09 | TRACK_B_US_AI | 特斯拉交付 48 万辆，为什么还不能直接判断财报？ | 80 | 特斯拉交付 48 万辆，为什么还不能判断财报？ | `READY` |
| P05-10 | TRACK_C_MACRO | Fed 按兵不动却出现三票加息，市场该看哪条传导链？ | 88 | Fed 不加息却有三票反对，股票投资者该看什么？ | `READY` |
| P05-11 | TRACK_C_MACRO | CPI 月增 0.1%、年增 3.4%，降息还是加息更有根据？ | 87 | CPI 月增 0.1%、年增 3.4%，Fed 应该看哪一个？ | `READY` |
| P05-12 | TRACK_C_MACRO | 美国 GDP 放缓到 1.5%，为何内需指标反而加速？ | 84 | 美国 GDP 降到 1.5%，为什么内需却加速？ | `READY` |

完整 Brief、标题/封面/Hook 与证据见 `production_queue.json`；当前源注册表见 `evidence_registry.json`。
