# BEN RADAR 20频道画像与三频道试点建议（P06A）

- 日期：2026-08-18
- 状态：`P06A_COMPLETE_PENDING_HUMAN_APPROVAL`
- 输入：用户提供的《20 頻道分類歸集總覽表（完整版）》
- 边界：本报告完成频道审计与试点建议；P06B 尚未实现

## 一、先说结论

本次实际识别 **20个唯一频道**，没有补造、重复或漏掉频道。频道内容足以建立第一版画像，但还不足以直接开发20频道：原文的分类目录只合计18个，`半導體駭客` 与 `華爾街溫度計` 在正文和矩阵中的归类冲突；绝大多数频道也没有负例、近30天采用历史、负责人和优先级。

第一轮建议只做三个差异频道，并全部等待人工批准：

1. **資金雷達 / SIGNAL_HEAVY**：验证台股 EOD 与异常 Signal 如何变成选题；必须明确“量价异动不等于资金净流入”。
2. **個股顯微鏡 / EVENT_HEAVY**：验证 MOPS 公司 Event + EOD 如何形成单公司选题；先接受月营收/财报/法说缺失和真实短缺。
3. **產業透視鏡 / CROSS_ENTITY**：验证多公司共现、事件关系与频道差异；Industry Mapping 审阅前不能当生产能力，共现不能写成供应链因果。

## 二、20频道按业务与数据成熟度分组

### 台股优先组（6）

`個股顯微鏡、收盤夜話、產業透視鏡、權值旗艦、資金雷達、半導體駭客（台股部分）`

这一组最接近当前能力，但只有 EOD/历史异常最成熟；公司基本面、行业/供应链、机构资金与半导体跨市场资料仍有缺口。

### 美股/中概组（7）

`那指火箭、板塊輪動儀、暗池雷達、期權守門人、財報獵人、中概風向球、華爾街溫度計`

美股 EOD、期权/暗池、ETF 流量、SEC/财报日历、13F 与 DXY/CNH 未接入，国际新闻权利也未确认。当前不适合做首批真实 Replay。

### 全球宏观与商品组（4）

`宏觀天秤、全球資金地圖、地緣炸藥庫、週期航海家`

需要宏观/央行日历、全球资产、商品、库存、运价及合格国际事件 Evidence；当前主要为 `NOT_IMPLEMENTED / BLOCKED_RIGHTS`。

### 链上组（1）

`鏈上顯微鏡` 需要链上、OI、清算和质押数据，当前未接入；24/7 市场的业务截止时点也未确认。

### 理财教育与长期策略组（2）

`財商拆彈組、定投實驗室` 分别缺监管/产品案例来源和10-30年历史/ETF参考数据/回测能力，不能用当天股票异常替代。

## 三、为什么先做这三个

三个试点共用 `Evidence → Signal → Event → Topic → Channel Assignment → Channel Daily Brief`，但分别检验不同环节。它们都以台股为主，能够利用当前真实 EOD；同时又不会把一个页面复制三份。

不先选美股、宏观、期权或链上频道，是因为数据未接入或权利未确认。不是这些频道不重要，而是当前做出来只能依赖结构示例或产生大量真实短缺。

不直接做20个，是因为每日5候选与各频道原定更新频率存在未决冲突：频道中既有每日，也有每周、财报季和事件触发。若不先确认，系统会把“每日监控”和“每日生产”混为一谈。

## 四、最大的三个缺口

1. **业务规则缺口**：每日5候选与实际发布频率的关系、分类冲突、负例/禁区、负责人和近30天采用历史未确认。
2. **台股公司与产业数据缺口**：MOPS 只有有限重大讯息；月营收、财报、法说、Guidance、机构资金、供应链指标未完成；Industry Mapping 仍为未提交且未接入的 `PARTIAL`。
3. **非台股数据与权利缺口**：美股 EOD、期权/暗池、宏观/财报日历、商品/链上数据未实现；台湾及国际新闻生产使用权未确认，X 仍是原型。

## 五、能力事实

- `AVAILABLE_VERIFIED`：TWSE/TPEx EOD 与历史基线；当前只读核对为97,603条、1,087个 TWSE 和889个 TPEx 证券，日期截至2026-08-17。
- `AVAILABLE_VERIFIED`：Anomaly Engine 的先前日期 Replay 与解释性规则；状态仍是 `READY_FOR_HUMAN_REVIEW`，不是业务选题规则已验证。
- `PARTIAL`：MOPS 重大讯息，当前只读核对11条且已映射；不等于月营收/财报/法说完整能力。
- `PARTIAL`：Industry Mapping 的未提交 migration/module/tests 当前存在，但数据库无相关表且未接 Topic 流程。
- `BLOCKED_RIGHTS / AVAILABLE_BUT_PROTOTYPE`：新闻和 X 只能按当前治理状态使用，不能写成生产授权。
- `NOT_IMPLEMENTED`：美股 EOD、财报/宏观日历、频道近30天采用历史、1H/6H/24H反馈。

## 六、P06B 前必须确认

1. 每日5候选是每天都生成，还是只在频道计划发布/事件触发日要求？
2. 是否批准三个试点；尤其是資金雷達能否采用“量价异动、非净资金流”的窄定义？
3. 個股顯微鏡能否先做 MOPS + EOD，还是必须先补月营收/财报/法说？
4. 產業透視鏡能否在独立审阅后使用官方行业码映射进行候选召回？
5. 半導體駭客与華爾街溫度計最终归类是什么？
6. 至少为三个试点补充正例、负例和明确禁区。

## 七、Topic Card 示例边界

本任务生成每个试点5条、共15条结构化样例。它们全部标记 `SCHEMA_EXAMPLE_NOT_REAL_TOPIC`，仅用于确认字段、准备度、Why Now、Why Channel、Evidence、市场时段和风险展示方式，不是今天真实热点。

## 八、建议下一步

业务负责人先确认试点名单与上面少量问题。确认后再写 P06B：仅实现三个频道、最近五个完整交易日 Replay、五个业务日人工试用和真实采用/拒绝记录；不要在 P06B 同时扩美股、20频道、内容生成或实时行情。

## 九、验证结果

- P06A 专用结构校验：通过（20 Profile、20+20矩阵行、3试点、15条 schema 示例、7个实质问题）。
- 当前能力定向测试：19项通过；Industry Mapping 仍仅代表未提交工作树可运行，不代表已接入生产。
- `git diff --check`：通过，仅有 LF→CRLF 提示。
- Project Memory check：通过。
- 完整应用测试：未运行；本任务仅改研究、报告和 Project Memory，且任务书禁止应用实现。

## 技术附录：产物

- `research/ben_radar_channel_intake/source_inventory.md`
- `research/ben_radar_channel_intake/channel_profiles_v0.1.json`
- `research/ben_radar_channel_intake/channel_profiles_human_review.md`
- `research/ben_radar_channel_intake/channel_overlap_matrix.csv`
- `research/ben_radar_channel_intake/channel_data_coverage_matrix.csv`
- `research/ben_radar_channel_intake/pilot_recommendation.md`
- `research/ben_radar_channel_intake/pilot_topic_card_examples.json`
- `research/ben_radar_channel_intake/open_questions.csv`
- `research/ben_radar_channel_intake/acceptance_report.md`
