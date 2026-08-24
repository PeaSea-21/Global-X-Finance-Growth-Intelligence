# CODEX TASK P07 - YouTube 文字层自动化与原创叙事校准

你正在 `C:\Users\yinen\Documents\ChatGPT\全球财经热点采集 Agent` 工作。

## 目标

在不模仿具名创作者、不把创作者观点当财经事实、不保存完整逐字稿的前提下，自动检查代表视频是否存在可用文字稿；对成功样本提炼真实 Hook、正文结构、证据顺序、观点边界、节奏与结尾；对失败样本保留明确状态。随后把至少三个来源家族的抽象机制与独立 FactPack 组合，生成原创财经 YouTube 方案。

## 启动要求

1. 完整执行仓库 `AGENTS.md` 的 Task Start Protocol。
2. 读取 `research/youtube_benchmark_p03/p04/`、`p05/`、`p06/` 和 `skills/finance-youtube-inspiration/` 的当前成果。
3. 检查 Git 状态，保留全部既有未提交改动。
4. 不把历史报告状态当成当前事实；重新验证目标视频和 FactPack 时效。

## 样本策略

1. 第一轮只选 3 个频道角色各 1 条：台股决策、科技更新、宏观解释。
2. 优先选择 P04 中 `ABOVE_BASELINE` 或 `BREAKOUT`，同时保留一条普通样本作对照。
3. 第一轮至少 2/3 成功取得合法文字输入后，才扩到每类 3-5 条。
4. 聚合结论必须至少由 3 条视频重复支持；单例只记为观察。

## 文字输入分流

按以下顺序执行，每条视频只走第一个可用路径：

1. `USER_PROVIDED_TEXT`：用户或频道自行导出的字幕、摘要或笔记。
2. `YOUTUBE_VISIBLE_TRANSCRIPT_UI`：使用当前浏览器可见的 YouTube“内容转文字”界面。不得读取 Cookie、密码或隐藏会话数据，不执行登录，不调用未公开接口。
3. `LOCAL_AUDIO_PROVIDED_BY_USER`：仅当用户提供本地音频或视频时，使用获准的本地转写能力。
4. `UNAVAILABLE`：入口不存在、持续空载、字幕不可用或被权限阻止时立即停止并记录。

不得自行使用 `yt-dlp`、InnerTube、登录绕过、Cookie 导出、代理轮换或未经审查的第三方 Transcript API。第三方服务必须另行完成条款、费用、凭据和商业使用审查并取得用户批准。

## 数据最小化

- 完整文字只允许存在于当前分析上下文或临时文件中。
- 正式成果只保存 `source_id`、URL、获取方式、状态、时间、语言、文本哈希、时间点、结构特征和短证据指针。
- 不保存完整逐字稿，不输出大段原文，不收集评论区个人资料。
- 创作者视频始终是 `STYLE_EVIDENCE / OPINION`，不能写入财经 FactPack。

## 八维分析

逐条输出 Topic、Title、Hook、Copy Structure、Evidence、Viewpoint、Rhythm、Ending。每一维必须包含：

- `status`: `OBSERVED | INFERRED | UNAVAILABLE`
- `finding`
- `evidence_pointer`
- `confidence`: `HIGH | MEDIUM | LOW`
- `transferable_mechanism`
- `do_not_copy`

只有文字成功取得后，Hook、正文结构、观点、节奏和结尾才能标为 `OBSERVED`。

## 原创生成闸门

1. 每项财经事实必须来自独立且在制作日复核过的 FactPack。
2. 至少融合三个来源家族的功能性机制，任何一个来源不得贡献超过 40% 的参数。
3. 禁止频道人格、节目名、肖像、口头禅、固定开场、个人经历、原标题和原缩略图文案。
4. 输出 3 个标题、2 个封面概念、0-10 秒 Hook、10-30 秒 Hook、正文大纲、证据顺序、下一验证点和 Finance QA。
5. 缺少当前 FactPack 时只交付结构 Brief，不生成带数字的成稿。

## 状态定义

- `AVAILABLE`: 成功读取可见文字内容并完成哈希与结构分析。
- `UI_PRESENT_BUT_UNAVAILABLE`: 入口存在但面板持续空载或播放器显示字幕不可用。
- `NO_TRANSCRIPT_CONTROL`: 页面没有可见文字稿入口。
- `BLOCKED_AUTH_OR_RIGHTS`: 需要新增登录、凭据、付费服务或未获批准的数据路径。
- `UNAVAILABLE`: 其他真实失败，不得改写成成功。

## 交付与验收

1. 更新结构化试跑记录，不保存 transcript body。
2. 校正与真实 UI 证据冲突的画像字段，并记录依据。
3. 输出成功率、失败类型、可扩展性判断和下一最小动作。
4. 运行 JSON 解析、无 transcript body、凭证扫描、原创性和 Project Memory 检查。
5. 执行 Task End Protocol，只记录实际完成与真实阻塞。
