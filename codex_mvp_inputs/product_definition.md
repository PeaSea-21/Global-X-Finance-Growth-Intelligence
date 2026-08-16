# Global X Finance Growth Intelligence — MVP Foundation

## 产品目标

建立一个可复用的核心引擎，通过不同 Market Pack 支持台湾、美国及后续市场。第一阶段只保证来源、原始证据、结构化数据和审计可追溯，不生成投资建议，不自动发布。

## 第一阶段范围

1. Market Pack Schema 与校验。
2. 已验证来源注册表导入与状态管理。
3. collection run 记录。
4. raw item 原文、原始 URL、发布时间、抓取时间与哈希的不可覆盖保存。
5. normalized item 与 raw item 的可追溯关系。
6. Claim、Evidence 与冲突状态的数据结构。
7. publisher_group 去重规则。
8. policy snapshot、compliance check 与人工审核结构。
9. 单元测试、安全扫描和非程序员 README。

## 非第一阶段范围

- 自动发帖、自动互动、账号池、代理 IP、设备指纹或平台限制规避。
- 财经观点、喊单、买卖建议或保证收益内容。
- 复杂微服务、实时流处理和全球市场同时接入。
- 广告 PASS 判定；产品、广告主体、牌照未确认时只能 UNKNOWN 或 REVIEW_REQUIRED。

## 市场范围

- 第一市场：Taiwan / TW。
- 第二市场：United States / US，已确认，但本阶段仅建立空白 Market Pack 模板，不接入未核验来源。

## 成功标准

- 台湾与美国走同一代码路径。
- 所有事实能回到 raw item 与 evidence URL。
- 来源字段不完整时不能进入 ACTIVE。
- UNKNOWN、NEEDS_VERIFICATION、SOURCE_CONFLICT 可以正常保存。
- 所有测试数据显式标记 SYNTHETIC_TEST_DATA。
- 仓库无凭据、Token、Cookie 或密码。

## 业务解释

每日每国约 40 条是后续目标，应理解为 8–10 个核验主题乘以 4–5 个账号人格变体，不代表每天发现 40 个独立且可靠的热点。
