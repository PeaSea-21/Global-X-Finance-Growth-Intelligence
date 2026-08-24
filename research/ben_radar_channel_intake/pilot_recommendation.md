# P06A 三频道试点建议

> 所有选择均为 `RECOMMENDED_PENDING_APPROVAL`。本文件不代表 P06B 已批准或实现。

## 推荐结论

| 类型 | 频道 | 当前可复用 | 关键前提 |
|---|---|---|---|
| SIGNAL_HEAVY | 資金雷達 | 台股 EOD、历史基线、Anomaly Engine | 不把量价异动写成真实资金净流入 |
| EVENT_HEAVY | 個股顯微鏡 | 有限 MOPS 重大讯息、台股 EOD | 首版接受窄事件范围与真实短缺 |
| CROSS_ENTITY | 產業透視鏡 | 台股 EOD、事件关系框架 | Industry Mapping 审阅后使用，共现不写成因果 |

## SIGNAL_HEAVY：資金雷達

- 状态：`RECOMMENDED_PENDING_APPROVAL`
- 推荐理由：现有 TWSE/TPEx EOD 和 Anomaly Engine 最接近其每日扫描节奏。；可直接验证 Market Signal 是否能变成有 Why Now/Why Channel 的 Topic。；能够暴露成交异动与真正资金流数据之间的边界。
- 反对理由：现有 EOD 量价异常不是法人、ETF 或产业指数的净资金流。；Industry Mapping 仅有未提交实现，数据库与 Topic 流程尚未接入。
- P06B 前置：业务确认首版允许使用‘量价/成交异动’而不是声称‘资金净流入’。；行业映射在独立审阅后才可成为试点输入。
- 替代项：收盤夜話；若业务更重视大盘盘后摘要，可替换，但三大法人/融资券仍是缺口。

## EVENT_HEAVY：個股顯微鏡

- 状态：`RECOMMENDED_PENDING_APPROVAL`
- 推荐理由：现有有限 MOPS 重大讯息可以与 EOD 异动组成公司事件包。；可验证官方披露 Event 与市场变化在不臆测因果时如何形成选题。；与资金雷达的快速扫描、产业透视镜的多公司视角差异明确。
- 反对理由：频道核心还包括月营收、财报、法说与 Guidance，当前均未完整接入。；频道原定每周1-2集，与每日5个候选的默认目标是否一致尚未确认。
- P06B 前置：确认试点可以先以 MOPS 重大讯息 + EOD 为窄范围。；允许合格候选不足5条时显示 HONEST_SHORTAGE。
- 替代项：財報獵人；但 SEC、财报日历和美股 EOD 均未接入，现阶段缺口更大。

## CROSS_ENTITY：產業透視鏡

- 状态：`RECOMMENDED_PENDING_APPROVAL`
- 推荐理由：可验证同一 Event/Signal 如何分配到多公司产业频道，而不是复制单股标题。；能检验 SAME_EVENT、RELATED_BUT_DISTINCT 与仅共现不等于因果的边界。；以台股为主，避免第一轮被美股数据与来源授权完全阻断。
- 反对理由：官方行业码不等于供应链关系；BB值、库存、产能利用率等尚未接入。；Industry Mapping 未提交且未进入当前数据库/Topic 流程。
- P06B 前置：首版只将官方行业分组用于候选召回，不宣称上下游传导已确认。；所有产业催化剂必须有独立 Evidence，否则标为 UNKNOWN。
- 替代项：半導體駭客；其跨台美特征更强，但美股 EOD 和技术/供应链来源尚未接入。

## 为什么不是一个频道或直接20个

一个频道无法验证同一共享事件如何产生不同 Why Channel；直接20个会把尚未确认的频率、禁区、数据权利和分类冲突固化成20套低质量规则。三个试点覆盖 Signal、公司 Event 和跨实体三种核心路径，同时把第一轮限制在台股，避免被尚未接入的美股/全球/链上数据完全阻断。

## 五日 Replay 的边界

P06A 只定义验收，不执行 Replay。P06B 获批后应使用最近五个完整台股交易日；所有候选必须显示时段、Evidence、未知与短缺，不得因目标5条而补造事件。
