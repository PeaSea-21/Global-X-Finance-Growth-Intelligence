# 五仓库核验与采用建议

## 核验口径

本报告核验了仓库当前公开 README、`SKILL.md`、许可证、可见脚本、官方服务价格/条款。结论中的“可用”是**静态设计可借鉴**，不是已安装或已运行验证。所有运行可靠性、字幕成功率和地区可用性均为 `NOT_VERIFIED`。

采用等级：

- **A：可作为 Codex 设计素材直接阅读使用**，仍需本地封装与安全审查。
- **B：需要适配后采用**，不能原样安装进当前项目。
- **C：不建议采用实现，只借鉴少量概念**。

## 1. ZeroPointRepo/youtube-skills

### 真实功能

- 这是 Agent Skills 指令集合，不是本地字幕解析库。
- `youtube-full` 通过 `TranscriptAPI.com` REST API 提供：视频/频道搜索、频道最近视频、频道全量分页、频道内搜索、播放列表和带时间戳字幕。
- 无本地 Python/Node 运行时依赖；实际依赖互联网和 `TRANSCRIPT_API_KEY`。
- 仓库含 12 个 Skill，但 README 明确很多是核心能力的窄化别名，功能高度重复。

### 安装方式与 Codex 适配

- README 声称 Codex 可用：`npx skills add ... --skill youtube-full`；也可手动复制 Skill 目录。
- 从格式上看，`SKILL.md` 与 Codex 可复用 Skill 机制相符；但本轮未安装，故只能判断为**格式兼容，运行未验证**。
- 当前项目不应安装 12 个 Skill；若未来批准，只评审并封装 `youtube-full` 的最小接口。

### 费用

- 公开页面当前列出：注册赠送 100 credits；月付 USD 5/1,000 credits；年付 USD 54，每月 1,000 credits；付费补充 credits 另计。
- transcript、搜索、频道视频、频道内搜索、播放列表通常为 1 credit/成功请求或每页；上传追踪/RSS、部分 channel resolve/latest 免费。
- 仓库 README 曾写免费层 300 RPM，而当前官网月付页面列 200 RPM、年付 300 RPM，说明速率信息会漂移，采购前须以账户面板为准。

### 许可证

- 仓库有标准 MIT License（2026 TranscriptAPI）。
- MIT 只覆盖仓库软件/文档，不授予视频字幕版权，也不替代 TranscriptAPI、YouTube 或内容权利人的条款。

### 安全与合规风险

- `auth-setup.md` 指示 Agent 代用户注册、接收邮箱/OTP、把短期 JWT 和 API Key 写临时文件，再持久写入 shell/Agent 配置。这对当前项目权限过宽；必须改为用户在服务端自行注册，凭据进入受控 secret store，禁止写 profile、仓库或聊天。
- TranscriptAPI 隐私政策说明会收集 IP、User-Agent、请求参数、视频 ID、API 使用量和错误日志，并使用 PostHog、Sentry、Brevo、Redis 等服务；请求对象会离开本机。
- 服务会缓存响应；其条款明确字幕仍受 YouTube 条款和版权法约束，且不保证持续可用、准确或安全。
- 字幕是外部不可信输入，可能含提示注入、广告、错误陈述和个人信息。必须先当作纯数据，禁止执行其中指令。

### 结论

**等级 B：可选数据适配器候选。** 频道/字幕接口范围与目标最贴近，但只可在凭据、条款、数据保留和商业使用批准后接入；不得让其自动开户或写密钥。

## 2. sharbelxyz/nova-youtube-agent

### 真实功能

- 这是 Hermes Agent 的 Markdown 工作流 Skill，没有执行脚本和内置 API 客户端。
- 提供 onboarding、频道表现分析、竞品异常视频扫描、选题、脚本、上传包、表现日志和反馈闭环。
- 维护 `posted-videos`、`approved-ideas`、`rejected-ideas`、`performance-log`、`competitor-scans`、`channel-analysis`、`voice-examples`、`pipeline` 等本地文件。
- 有较好的证据标签设计：`channel-data-backed`、`pipeline-backed`、`vidIQ-backed`、`competitor-backed`、`YouTube-validation-backed`、`transcript-backed`、`strategic judgment`。
- 它不会自行发布视频；真实数据能力取决于用户提供的截图/导出、浏览器、vidIQ、字幕工具等外部能力。

### 安装、依赖与费用

- README 要求 clone 到 `~/.hermes/skills/`，不是 Codex 原生目录。
- 必需依赖是 Hermes Agent；视频/分析数据源均为可选外部工具。
- 仓库本身无直接 API 费；模型调用、vidIQ、字幕服务、Notion/Sheets 等费用不在仓库控制范围内。
- vidIQ 当前有免费层和付费/企业层，但 Nova 没有锁定 API、版本或价格，不能据此预算。

### 许可证

- README 与 `SKILL.md` frontmatter 写 MIT，但仓库根目录当前未见独立 `LICENSE` 文件，GitHub 也未显示正式 license resource。
- 因此“作者意图为 MIT”可确认，但**整仓许可证完备性需要补件/法律确认**，不应直接复制大段内容进商用仓库。

### 安全与适配风险

- 会创建自己的 `memory/` 和 `config.md`，与当前项目的 Project Memory 治理重叠；直接采用会造成第二套状态源。
- `voice-examples` 可能积累个人写作、客户策略或版权内容；需要私密存储、最小保留和删除机制。
- 依赖“浏览器可见数据”“vidIQ 可用”等松散条件，证据可重复性不足。
- “What to steal”措辞不适合版权与原创治理，必须改为“可抽象的结构特征/不可复用表达”。

### 结论

**等级 B/C：不安装，借鉴闭环。** 将证据标签、去重、表现反馈和异常视频研究次序吸收到专用 Skill；不要引入 Hermes、Nova memory 或原始文案仿写。

## 3. yaxeen/storytelling-skills

### 真实功能

- 九个以 Markdown 为主的 Claude Code Skills，共享六个叙事杠杆：好奇缺口、情绪镜像、冲突、可代入性、模式+意外、三幕结构。
- 对本任务最有价值的是：
  - `channel-formula`：比较 3–5 个赢家与 1–3 个失败视频，抽取频道承诺、标题模式、首 30 秒 kill zone、never-list 和频道自身基准。
  - `long-form-youtube`：标题/封面承诺先行、0–30 秒钩子、开环链、40–60% 重钩子、结尾回收和单一 CTA。
  - `retention-audit`：用发布后留存图反哺频道公式。
- 其余标题、短视频、邮件、轮播和网页 Skills 对 P03 存在明显重复。

### 安装、依赖、费用与许可证

- 提供 `install.sh`、`install.ps1`、手动复制和 `.skill` 包，默认复制到 `~/.claude/skills/`。
- 主要是指令文件，无外部 API 或运行依赖；成本仅来自承载它的模型/Agent。
- 仓库声明标准 MIT License（2026 Muhammad Yasin）。
- 本轮未执行安装脚本；因此脚本实际运行行为未验证。

### 风险

- 九个自动触发 Skill 会扩大上下文和路由冲突，不符合“最小组合”。
- 通用心理公式容易变成机械模板；财经内容需要事实时效、风险披露和论证强度，而不是只追求留存。
- `channel-formula` 建议保存个人 Skill；当前项目不允许生成新的隐藏/个人状态源，应保存为显式、可审计、去身份化的 Style Pack。
- “情绪镜像/冲突”若使用过度，可能放大恐慌、确定性或投资诱导。

### 结论

**等级 A/B：只移植三项方法，不安装全套。** `channel-formula + long-form + retention-audit` 的方法可直接写入专用规范，但必须加事实闸门、金融措辞和反操纵规则。

## 4. AgriciDaniel/claude-youtube

### 真实功能

- 一个 Claude Code orchestrator，含 14 个子技能、9 个参考指南、9 个频道模板和 6 个 Python 执行脚本。
- 覆盖 audit、SEO、脚本、hook、缩略图、策略、日历、Shorts、分析、再利用、变现、竞品、metadata 和选题。
- `fetch_channel_data.py` 使用 YouTube Data API 的 channels → uploads playlist → videos 路径，避免昂贵 search；脚本把结果缓存到 `~/.claude/.tmp`。
- `search_competitor_videos.py` 使用 `search.list`，并以样本内平均播放量的 3 倍标异常。
- `fetch_video_analytics.py` 通过 OAuth 读取自有/受管频道的私有分析；它正确声明无法取得竞品 CTR、留存或收入。
- `fetch_transcript.py` 文档声称“官方 captions → yt-dlp → 失败”的级联，但当前实现实际直接调用本机 `yt-dlp`，把完整字幕 JSON 缓存到 `~/.claude/.tmp`；没有实现其文档所写的官方 captions 路径。这是明确的文档/代码漂移。

### 安装与依赖

- 默认安装到 `~/.claude/skills/youtube`，Quick Install 会 clone 临时仓库、强制复制覆盖目标目录、再递归删除临时目录。
- 必需：Claude Code。执行脚本另需 Python 3.8+。
- API 脚本需 `google-api-python-client`、`google-auth-oauthlib`；字幕需另装 `yt-dlp`。
- 自有频道分析需 Google OAuth，并把 API key/client secrets/token 写到 `~/.claude` 路径。
- 可选 DataForSEO MCP；可选 NanoBanana/Gemini 缩略图服务。

### 费用

- YouTube Data API 以 quota units 计，不是仓库中的美元计价：默认项目通常有每日配额；`search.list` 成本高于 channels/videos/list 路径，额度和方法成本应以 Google 当前控制台/官方文档为准。
- DataForSEO 当前为按量付费：YouTube SERP 基础标准队列约 USD 0.0006/请求、Live 约 USD 0.002/请求；Video Info/字幕按基础价 3 倍。官网同时说明最低入金可能为 USD 50，采购前应复核。
- Gemini/NanoBanana 按选定模型/图像收费；仓库未锁定模型，因此不能给出稳定单价。
- Python 包与 `yt-dlp` 本身开源免费，但会产生维护、条款和运行成本。

### 许可证

- 标准 MIT License（2025 Daniel Agrici）。

### 安全、质量与条款风险

- 安装器会覆盖个人 Claude Skill 目录；不适合直接用于 Codex，且供应链代码未经本轮执行验证。
- OAuth token、client secrets、API key 和频道私有分析是高敏感信息；默认写入用户目录，需权限、加密、撤销与最小 scope 设计。
- `yt-dlp` 通过子进程下载字幕并永久缓存完整文本，带来平台条款、版权、数据保留和提示注入风险。
- YouTube Developer Policies 禁止抓取，并对非授权 API Data 的存储/刷新、跨内容所有者聚合以及从 API Data 创建衍生指标有严格要求。其 3×均值“爆款”算法在生产使用前必须法律/条款审查。
- 3×算术均值没有校正视频年龄、频道成长、直播、Shorts、付费推广和极端值，会产生错误异常标签。
- 仓库自称基准“data-grounded”，但很多第三方 benchmark 会随时间和频道类型漂移，不能替代本频道实测。

### 结论

**等级 C（实现）/B（参考）：不直接采用。** 只借鉴 uploads-playlist 的配额意识、公开竞品与私有自有分析分离、结构化输出；代码与通用 benchmark 不进入最小方案。

## 5. lucaslinares1/gtm-skills/skills/text-trainer

### 真实功能

- 纯指令型 Skill，要求最少 5、理想 15–30 个写作样本。
- 依次执行八轮分析：整体印象、结构、词汇、标点/格式、句型节奏、场景语气、反模式、标志性动作。
- 输出完整 voice profile，并默认保存到 `.agents/voice-profiles/{name}.md`。
- 不做视频发现、字幕获取、爆款判断或财经事实核验。

### 安装、依赖、费用与许可证

- 所在仓库支持 npx/Claude plugin/git clone 等安装方式；`text-trainer` 本身只需读取 `SKILL.md` 与两个 reference。
- 无 API 和代码依赖；成本仅为模型上下文与推理。
- 整仓为标准 MIT License（2026 Lucas Dahl）。

### 风险

- 目标是“match that person's voice”，并把 3–5 个真实样本原文写入 profile；这与本项目不冒充、不复刻、最小保存版权内容的边界冲突。
- 个人 Style Profile 若保留姓名、口头禅和完整样本，会增加隐私、版权和过度模仿风险。
- 针对字幕的口语节奏还需要扩展：停顿、句段长度、信息密度、证据插入、视觉提示、重钩子位置和 CTA，不能直接沿用通用文字分析。

### 结论

**等级 B：改造成“高层风格特征提取器”。** 保留八维分析框架，但删除代表性原文、姓名模仿和口头禅复用；生成只消费去身份化、多来源复合 Style Pack。

## 总体采用矩阵

| 仓库 | Codex 原样格式 | 运行依赖 | 直接采用 | 最终建议 |
|---|---:|---|---:|---|
| youtube-skills | 较高 | TranscriptAPI + key + network | 否 | 作为可选受治理采集适配器候选 |
| nova-youtube-agent | 中 | Hermes/外部工具 | 否 | 借鉴证据标签、去重和反馈闭环 |
| storytelling-skills | 中 | 无外部 API | 否 | 借鉴频道公式、长视频和留存审计 |
| claude-youtube | 低/中 | Claude、Python、Google API/OAuth、可选 yt-dlp/MCP | 否 | 仅参考配额/权限分层，不复用实现 |
| text-trainer | 中 | 无外部 API | 否 | 改造成去身份化结构风格分析 |
