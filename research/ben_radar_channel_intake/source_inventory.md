# P06A 频道输入盘点

## 结论

- 输入文件：`C:\Users\yinen\.codex\attachments\7d3e19f0-9589-41cc-a0f2-1e586a952303\pasted-text.txt`
- SHA-256：`E5BB9A17F5CAC49DDF8469CD8A56A2E85CE27B94DD19CAC27CA64C429732A182`
- 输入行数：496
- 实际识别频道：**20**
- 唯一频道名：**20**；重复：**0**；无法识别：**0**；缺失：**0**
- 输入状态：`COMPLETE_COUNT_WITH_TAXONOMY_CONFLICT`
- 原文最后更新：`2026-08-12`（来自附件正文，不代表本仓库数据时点）

## 文件范围

本次用户明确表示频道资料只有这一份附件。本审计没有把当前 Top20 股票、29 个 X 账号、23 条实时来源或既有 Style Pack 当作输出频道。

## 对账问题

1. 目录六大分类声称 `5 + 5 + 4 + 1 + 1 + 2 = 18` 个频道，但正文与跨分类矩阵实际各有20个唯一频道。
2. `半導體駭客` 与 `華爾街溫度計` 位于正文“理财教育/定投策略”段下，但跨分类矩阵分别归为“半导体”和“美股资金”；两条 Profile 标为 `CONFLICT`。
3. `鏈上顯微鏡` 使用“每交易日收盘后”，但加密市场24/7，业务截止时点为 `NEEDS_CONFIRMATION`。
4. 多数频道给了“常讲什么”，但没有明确负例、负责人、优先级、近30天采用历史和实际采用/拒绝样例。
5. 原文统一风险提示已逐条保存在 `source_fields_raw.global_risk_template_raw`；不得把它替代成投资建议。

## 解析与保真

- 每个 Profile 保存完整 `raw_channel_block`、原始简介、内容板块、受众、更新频率、标签、SEO、跨分类矩阵原始行与品牌家族字段。
- 生成字段使用 `SUPPLIED / DERIVED_FROM_SUPPLIED / PROPOSED / UNKNOWN / CONFLICT` 标注 provenance。
- 未提供的正/负样例保持空数组并列入 `missing_fields`。
