# P06 — Finance YouTube Inspiration Distillation

## Status

`P06_PARTIAL_READY`

30 条代表视频已完成逐条八维卡片，但文字层仍被真实访问限制阻塞：公开、无登录探针 3 条，取得文字稿 0 条。没有使用登录 Cookie、YouTube 账号、InnerTube、yt-dlp、浏览器抓取或付费 API，也没有保存完整字幕。

## 样本

| 频道角色 | 视频数 | 可观察层 | 文字层 |
|---|---:|---|---|
| 台股盘面与个股分析 | 10 | 选题、标题、缩略图、相对表现 | Hook、正文、观点、节奏、结尾 UNAVAILABLE |
| 半导体与科技产业链 | 10 | 选题、标题、缩略图、相对表现 | Hook、正文、观点、节奏、结尾 UNAVAILABLE |
| 全球宏观与美台联动 | 10 | 选题、标题、缩略图、相对表现 | Hook、正文、观点、节奏、结尾 UNAVAILABLE |

## 逐条拆解结论

- 30/30：Topic、Title 与 Thumbnail 可依据真实元数据和人工视觉核看标为 `OBSERVED`。
- 30/30：Evidence 只能标为画面/元数据层观察，不能把创作者内容当财经事实。
- 30/30：Hook、Copy Structure、Viewpoint、Rhythm、Ending 保持 `UNAVAILABLE`；没有用标题猜正文。
- 每张卡均保留 source video ID、performance label、可迁移机制与不可复制元素。

## 三类可用灵感

1. **决策压缩**：具体对象 → 单一判断问题 → 条件与风险。
2. **更新账本**：三项科技事件 → 各自影响 → 共同主题。
3. **宏观传导**：宏观事件 → 官方数据 → 金融变量 → 产业/资产 → 下一验证点。

这些是包装与结构假设，不是已验证增长规律。Skill 会进一步组合成 creator-neutral 的七种结构，并强制使用独立 FactPack。

## 可调用 Skill

项目级 Skill：`skills/finance-youtube-inspiration/`

调用示例：

`Use $finance-youtube-inspiration with this transcript and FactPack to produce one original Taiwan-finance YouTube brief.`

当用户提供合法字幕、摘要或文案时，Skill 会补齐 Hook、文案结构、证据顺序、观点、节奏与结尾，并运行非重建式文字特征和原创性检查。

## 下一真实解锁条件

任一条件即可继续文字层：用户提供字幕/摘要；频道自行导出的字幕；或另行批准、明确条款与商业使用状态的 transcript adapter。没有这些输入时，Narrative 层不能升级为 READY。
