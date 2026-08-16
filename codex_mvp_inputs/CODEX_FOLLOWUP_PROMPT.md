# 给当前 Codex 会话继续发送的提示词

继续执行 `CODEX TASK 01 — Global X Finance Growth Intelligence MVP Foundation`。

你刚才因缺少已验证来源注册表而正确输出了 `BLOCKED_MISSING_VERIFIED_SOURCE_REGISTRY`。现在我已经把所需输入文件放入当前项目工作区：

- `verified_source_registry.csv`
- `taiwan.market-pack.yaml`
- `us.market-pack.template.yaml`
- `product_definition.md`
- `database_schema.md`
- `x_policy_urls.txt`

请先读取并审计这些文件，再开始实现。第二市场已确认是美国，但美国来源尚未核验，所以本阶段只保留 US Market Pack 模板，不得自行添加美国 API、RSS、KOL、Endpoint 或政策结论。

重要解释：

1. `registry_status=ACTIVE` 仅表示来源身份与入口已经核验存在，不代表已经获得自动采集许可。
2. 是否可以自动采集由 `collection_status` 决定。
3. `BLOCKED_ROBOTS_OR_NEEDS_PERMISSION`、`NEEDS_TERMS_REVIEW`、`NEEDS_LICENSE_OR_TERMS_REVIEW` 不得被实现为绕过限制的采集器。
4. `TWSE OpenAPI` 是当前唯一明确标记 `API_VERIFIED` 的首批结构化接口；不得把其他 HTML 来源自行推断成 API 或 RSS。
5. 台湾来源中相同 `publisher_group` 必须去重，例如 FSC 与 SFB 同属 `fsc`，TWSE 官网、OpenAPI 与 MOPS 同属 `twse`。
6. 本阶段仍然不要生成财经观点、内容草稿或自动发布功能。

开始前请输出一份不超过20行的 Input Audit，列出：已找到文件、注册表行数、ACTIVE行数、API_VERIFIED行数、被条款/robots阻塞的来源、仍为 UNKNOWN 的事项。然后直接实现，不需要再次等待确认。

完成后必须提供：

- 创建/修改的文件清单
- 一条安装命令
- 一条数据库初始化命令
- 一条来源注册表校验与导入命令
- 一条完整测试命令
- 测试结果摘要
- 尚未实现的 NEXT/LATER 清单

原任务的 Acceptance Criteria、Do Not Do 和 Test Cases 继续全部有效。
