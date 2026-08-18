# P04 中文标题与摘要覆盖

验证时间：2026-08-16 20:39:41（UTC+8）  
验证命令：`python scripts/validate_ben_p04.py --db data/taiwan-demo.db`

## 结果

| 指标 | P04 前 | P04 后 |
|---|---:|---:|
| Top 20 中文标题 | 18/20（90%） | 20/20（100%） |
| Top 20 中文摘要 | 20/20（100%） | 20/20（100%） |
| 首页出现“中文摘要生成中” | 2 | 0 |

P04 后 Top 20 状态：`ORIGINAL_CHINESE` 6 条，`TRANSLATION_UNAVAILABLE` 14 条。后者不是 AI 翻译，而是明确标注的 `RULE_FALLBACK` 中文事实提要；英文原文仍只在 Evidence 展开区展示。

## TranslationSummaryAdapter

- 独立模块：`src/global_x_finance/translation_summary.py`，页面模板不承担翻译逻辑。
- 输入：原文、实体、动作、主题、源语言、目标语言。
- 优先级：缓存 → 原文中文 → 可替换模型适配器（含重试）→ 规则摘要 fallback。
- 模型输出只有标题和摘要都含可用中文时才接收。
- 无模型或模型失败时状态为 `TRANSLATION_UNAVAILABLE`、方法为 `RULE_FALLBACK`，不会伪装成翻译。
- 缓存表：`ben_translation_summary_cache`；保存 source hash、语言、标题、摘要、状态、方法、模型名、尝试次数与错误原因，不保存凭据。

## 本地缓存快照

验证时缓存共有 59 条：

- `ORIGINAL_CHINESE`：16
- `TRANSLATION_UNAVAILABLE`：43

缓存数量会随时间窗口与新 Evidence 增长；上述数字只是验证快照。

## 已知限制

- 当前没有配置外部翻译模型，所以不能声称完成逐字翻译。
- 规则摘要针对首页可读性和事实边界，不替代人工核对。
- 人名、机构别名与冷门事件可能只得到通用中文摘要；完整原文保留在 Evidence。
