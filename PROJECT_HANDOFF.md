# Global X Finance Growth Intelligence - Project Handoff

更新时间：2026-08-24（Asia/Shanghai）
交接基线：`main` @ `f64eacf`

> 本文用于把项目迁移到另一台 Windows 电脑继续开发。它记录当前可验证状态，不包含任何密码、API Key、Cookie 或 Token。迁移前请通过受控渠道单独传输本地数据和凭据。

## 1. 项目目标和业务背景

本项目是面向约 10-15 人财经内容团队的“证据优先”热点采集、研究与审稿工作台。业务目标是：

- 从台股、美股、全球宏观、加密货币等市场采集新闻、官方数据和市场异动。
- 将同一热点按不同频道定位生成不重复的选题和完整口播文稿。
- 让 Ben 哥通过公网内容工作台审阅频道、选题、选题理由、信源、抓取时间、原文发布时间、完整稿件和历史回顾。
- 在数据不足、交易日不匹配或来源未通过时明确输出 `UNKNOWN`、`UNAVAILABLE` 或 `SOURCE_PENDING`，不把旧数据伪装成当日结论。
- 通过生成、审计、发布三段式流程控制 GitHub Pages 公网发布。

公开内容工作台：

- <https://peasea-21.github.io/Global-X-Finance-Growth-Intelligence/ben-content-studio/>

仓库：

- <https://github.com/PeaSea-21/Global-X-Finance-Growth-Intelligence>

## 2. 当前已经完成的功能

### 数据与雷达

- 台湾官方市场数据接入和本地 SQLite 数据库。
- BEN Radar 台股研究工作台、快照、候选事件、证据链和审核门禁。
- 每日 X 热点收集入口，以及外部 `X-HotTopic` 项目的衔接。
- 周日到周五的内容任务设计；周日也会执行采集/研究，而不是只覆盖交易日。
- 同日数据门禁：没有同日合格来源时，不生成或发布伪当日稿件。

### 频道内容工作台

- 后端已定义 20 个频道及各自的频道定位、更新频率、Style Pack 和内容约束。
- 11 个有真实样稿/转录参考的频道会显示；9 个没有完整真实样稿的频道暂时隐藏。
- 已生成并审计 55 篇按目标时长控制的完整文稿，不再使用“约 600 字”作为统一标准。
- 已整理 134 张带时间信息的信源卡片。
- 选题契约已升级到 v2：选题、为什么现在做、为什么适合该频道、证据和完整文稿保持对应。
- 已加入历史回顾能力：保留各频道过去的选题、文稿、看涨/看跌观点及后续可验证结果，不再每天清空。
- 当前存在 11 份追加式历史快照。
- 页面支持来源抓取时间、原文发布时间和人可读的原文链接。
- 页面支持反馈/审稿状态的浏览器本地保存。

### 构建、审计与发布

- 内容工作台构建脚本和独立审计脚本已完成。
- 发布前准备和 `gh-pages` 发布脚本已完成，支持仅校验模式。
- GitHub Pages 已有可公开访问版本，但当前公网分支仍是较早版本，详见第 3、5 节。
- Windows 计划任务安装脚本已完成。

## 3. 当前正在做到哪一步

当前 `main` 已完成频道历史回顾、信源时间、完整文稿和选题对应关系等近期优化，并已推送到 `origin/main`。

当前内容状态：

- 20 个频道已在后端建模。
- 11 个频道有真实完整样稿，当前可展示。
- 9 个频道因没有真实完整样稿而隐藏。
- 55 篇完整稿件和 134 张信源卡已在本地工作流中形成。
- 2026-08-24 当日 Phase A 数据没有形成；后续 enrichment 状态为 `SOURCE_PENDING`，因此当天没有生成新稿，也没有发布。

当前发布状态：

- `main`：`f64eacf`，与 `origin/main` 一致。
- 远端 `gh-pages`：`f80a5fa`，仍是 2026-08-21 左右的公开内容，不包含 `main` 最新改动。
- 本地 `gh-pages`：`0e607b8`，比远端更旧，不能作为公网发布真相源。

因此，新电脑接手时应先在 `main` 上恢复开发和验证，不要从本地旧 `gh-pages` 分支继续工作。

## 4. 尚未完成的 TODO（按优先级）

### P0 - 恢复可重复运行环境

1. 安全迁移 `data/` 中的主数据库，以及确有审计价值的 `outputs/` 日产物。
2. 在新电脑重建 Python 虚拟环境和 Node 依赖，不复制旧 `.venv`、`node_modules`。
3. 配置外部 `X-HotTopic` checkout 路径及公司中转站/模型提供方设置。
4. 跑完整检查，确认本地数据日期、来源门禁和稿件审计都通过。
5. 检查后再重新安装 Windows 计划任务和 Codex 自动化。

### P1 - 恢复每日可靠生产

1. 修复或替换 TPEx 目前返回 HTTP 403 的来源。
2. 补齐同交易日市场广度、三大法人、融资融券、借券等关键数据。
3. 为美股安装授权稳定的 EOD 数据源。
4. 验证 FxTwitter/X 热点链路的连续性、字段契约和商业使用权。
5. 在同日来源门禁通过后，验证“采集 -> 研究 -> 完整文稿 -> 审计 -> 公网发布”的整链路。

### P2 - 扩展频道覆盖

1. 为 9 个隐藏频道补齐真实、完整、可验证的参考样稿，再开放页面展示。
2. 补 TAIFEX、借券、暗池、完整期权链、链上地址和 ETF 资金流等专业来源。
3. 加强跨频道热点复用：允许覆盖同一事件，但标题、切入角度、论证和结论必须匹配各自 Style Pack，不能重复稿。
4. 为历史观点增加自动结果核验和“说中/说错”的回顾证据。

### P3 - 合规与运维

1. 明确 TWSE、TPEx、MOPS 数据在公网展示和再分发方面的授权边界。
2. 明确所有第三方新闻、转录和 X 数据的商业使用权。
3. 建立数据库、日产物和审稿反馈的加密备份与恢复演练。
4. 增加生产运行告警和公网版本/数据日期提示。

## 5. 当前已知 bug / 阻塞问题

- TPEx 部分端点返回 `HTTP 403 Forbidden`，导致部分台股数据缺失。
- 同日市场广度、法人流、融资融券等数据不完整时，系统会正确停在 `SOURCE_PENDING`；这不是成功状态。
- 2026-08-24 没有可用 Phase A，同日内容没有生成或发布。
- 9 个频道没有真实完整样稿，按当前决策必须隐藏，不能用臆造风格补齐后上线。
- TAIFEX、借券、暗池、完整期权链、链上地址、ETF flow 等来源尚未接入。
- 尚无稳定且授权明确的美股日终行情源。
- FxTwitter/X-HotTopic 的连续可用性和商业使用权仍为 `UNKNOWN`。
- TWSE、TPEx、MOPS 公网展示/再分发权利仍为 `UNKNOWN`。
- 公网页面仍来自远端 `gh-pages` 的 `f80a5fa`，没有自动包含 `main` 的最新功能和内容。
- 页面中的审稿反馈主要存在浏览器 `localStorage`；换电脑或换浏览器不会自动恢复。

## 6. 重要架构和技术决策

### 证据优先，缺失不补零

市场数据缺失时保留 `UNKNOWN`/`SOURCE_PENDING`，不把缺失值写成 0，也不拿上一交易日新闻冒充今天。原因是该系统用于真实内容生产，错误的确定性比暂时缺稿风险更高。

### 生成、审计、发布分离

构建内容、审计内容、推送 `gh-pages` 是三个独立步骤。发布脚本提供 `-ValidateOnly`。原因是公网发布是外部状态变更，必须在来源、日期、稿件和合规门禁通过后单独授权。

### 频道 Style Pack 独立

同一新闻可以服务多个频道，但每个频道必须有独立受众、角度、标题、节奏和论证。原因是业务需要热点覆盖率，同时避免频道矩阵出现重复标题和换皮稿。

### 按口播时长控制完整稿件

稿件以频道目标时长和可读语速为门禁，不再用统一 600 字下限。原因是 3 分钟快讯与 15 分钟盘后节目本来就不应使用相同长度标准。

### 无真实样稿的频道隐藏

20 个频道全部保留在后端，但只有 11 个有真实完整样稿的频道对审稿人展示。原因是频道真人化模仿需要真实参考，不能凭名称臆造风格。

### 历史快照追加保存

每日选题和稿件不覆盖前一天内容，而是追加快照，用于后续判断观点结果并制作回顾。原因是内容团队需要积累可验证记录和复盘素材。

### 主代码与发布分支分离

开发以 `main` 为准，静态公网内容由 `gh-pages` 承载。原因是避免构建产物、私有输出和开发代码混在一个分支，也便于发布前验证。

## 7. 项目启动、测试、构建、部署命令

以下命令均在 PowerShell 中执行。

### 克隆与安装

```powershell
git clone https://github.com/PeaSea-21/Global-X-Finance-Growth-Intelligence.git
cd "Global-X-Finance-Growth-Intelligence"

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

当前已验证工具版本：Python `3.11.15`、Node `v24.16.0`、Git `2.55.0.windows.3`、PowerShell `7.6.4`。新电脑可使用兼容版本，但首次运行必须重新跑全部检查。

### 启动台湾 Demo

```powershell
.\启动台湾Demo.bat
```

### 项目检查

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
powershell -ExecutionPolicy Bypass -File scripts/project-memory-check.ps1
```

### 每日频道流水线

```powershell
.\.venv\Scripts\python.exe scripts\run_daily_channel_brief.py `
  --max-attempts 4 `
  --retry-seconds 300 `
  --review-json sites\ben-channel-review\brief.json

.\.venv\Scripts\python.exe scripts\run_close_talk_enrichment.py
.\.venv\Scripts\python.exe scripts\run_ben_weekend_crawl.py
```

### 内容工作台构建与测试

```powershell
.\.venv\Scripts\python.exe scripts\build_all20_content_studio.py
.\.venv\Scripts\python.exe scripts\audit_all20_content_studio.py

node --test sites/ben-channel-review/tests/page.test.mjs `
  sites/ben-content-studio/tests/page.test.mjs
```

### 发布前验证

```powershell
.\.venv\Scripts\python.exe scripts\prepare_ben_content_studio_publish.py `
  --trade-date YYYY-MM-DD

powershell -ExecutionPolicy Bypass `
  -File scripts/publish_ben_content_studio.ps1 `
  -TradeDate YYYY-MM-DD `
  -ValidateOnly
```

去掉 `-ValidateOnly` 会实际修改并推送 `gh-pages`。只有在当日来源和稿件审计通过、且得到明确发布授权后才能执行。

### Windows 计划任务

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_daily_x_collection_task.ps1
powershell -ExecutionPolicy Bypass -File scripts/install_realtime_radar_task.ps1
```

安装前先检查脚本参数、路径和新电脑账户环境。不要在恢复数据和测试通过前安装。

## 8. 当前 Git branch 和最近重要 commit

当前可验证 Git 状态：

- 当前分支：`main`
- 当前 HEAD：`f64eacf`
- 上游：`origin/main`
- 与上游关系：一致
- 创建本文件前：工作树干净，暂存区和普通 diff 均为空

最近重要提交：

```text
f64eacf docs: record main consolidation
d2bb199 feat: add BEN channel content workflow
0f61e3c docs: record BEN Radar remote publication
af0f478 feat: deliver BEN Radar stock workbench v0.1
```

发布分支注意事项：

- 远端 `gh-pages`：`f80a5fa`
- 本地 `gh-pages`：`0e607b8`（已过期）

## 9. 本地存在但可能没有提交 Git 的文件

创建本交接文件前，`git status --short --branch` 显示工作树干净。以下文件/目录因为 `.gitignore`、`.git/info/exclude`、体积、隐私或运行产物原因，可能存在本地但不会随 `git clone` 恢复：

- `PROJECT_HANDOFF.md`：本次新建，除非后续显式提交，否则为未跟踪文件。
- `data/`：本地数据库、smoke 数据库和日志。
- `outputs/`：每日运行、BEN 内容、周末采集、X 日报、渲染及验证产物。
- `.venv/`：Python 虚拟环境，应重建。
- `sites/ben-radar-public/node_modules/`：Node 依赖，应重装。
- `.pytest-tmp/`、`.pytest_cache/`、`work/`、`logs/`、`build/`：测试、缓存和构建产物，多数可丢弃。
- `scripts/probe_t0sk_relay.ps1`：本地中转站探测脚本，不应公开提交。
- `检测中转站.cmd`：本地中转站检查入口，不应公开提交。
- `ersyinenDocumentsChatGPT全球财经热点采集 Agent`：本地异常命名文件，迁移前人工检查，不要直接提交。
- `.git/info/exclude`：仅当前 clone 有效，不随仓库迁移。
- 仓库外的公司中转站、Codex provider 和浏览器配置。

迁移前应使用 `git status --ignored --short` 和按目录核对的方式再次确认，不要把密钥、Cookie、Token 或私人配置打包进 Git。

## 10. 依赖的环境变量名称

只记录名称和用途，不记录值：

- `X_HOTTOPIC_ROOT`：外部 `X-HotTopic` checkout 的绝对路径。未设置时，实时脚本可能回退到 `%USERPROFILE%\Desktop\code\X-HotTopic`。
- `TRANSCRIPT_API_KEY`：可选；仅用于 YouTube benchmark research adapter。
- `USERPROFILE`：Windows 系统提供，用于默认用户目录路径。

核心每日流水线当前不要求 `OPENAI_API_KEY`。公司中转站/API provider 的地址、模型和认证配置在仓库外管理；新电脑需要单独配置，但绝不能写入本文件或提交 Git。

## 11. Git 无法自动恢复的本地数据和状态

### 必须评估是否安全迁移

- `data/`：7 个文件，约 340 MB。
  - `data/taiwan-demo.db`：约 198,946,816 bytes。
  - `data/taiwan-demo.pre-p06b-20260819.db`：约 139,374,592 bytes。
  - `data/mvp.db`：约 1,150,976 bytes。
  - 其余 smoke 数据库和本地日志。
- `outputs/`：184 个文件，约 29.7 MB。
  - `ben_channel_daily/`
  - `ben_all20_editorial/`
  - `ben_weekend_crawl/`
  - `x_daily/`
  - 验证和文档渲染目录。
- 外部 `X-HotTopic` checkout，通常位于 `%USERPROFILE%\Desktop\code\X-HotTopic`。

这些内容可能包含来源快照或业务数据。应通过加密、受控渠道传输，并在传输前检查是否包含个人或公司敏感信息。

### 应在新电脑重建，不建议复制

- `.venv/`：约 61.7 MB。
- `sites/ben-radar-public/node_modules/`：约 829.5 MB。
- `.pytest-tmp/`：约 81.9 MB。
- `work/`：约 21.2 MB，多数为测试或缓存材料。
- `.pytest_cache/`、`logs/`、`build/`。

### 浏览器和应用状态

- 浏览器 Cookie、登录会话、打开的标签页不会由 Git 恢复。
- 内容工作台浏览器本地状态，例如 `ben-channel-review.feedback.v1`。
- BEN Radar 队列/测试状态和其他 `localStorage` 数据。
- GitHub 登录、Git credential helper、SSH key/HTTPS token。
- Codex 登录状态、公司中转站配置和 Chrome 登录状态。

### 自动化任务

Windows 任务计划程序中的任务不会由 Git 恢复：

- `Global X Finance - Daily X Collection`：每天 13:05；当前机器最近结果为 `0`。
- `Global X Finance - Taiwan Realtime Radar`：每 10 分钟；当前机器最近结果为 `0`。

Codex 自动化位于 `%USERPROFILE%\.codex\automations\`，也不在 Git 中：

- `ben-radar`：启用，周日至周五 13:35。
- `ben-radar-14-45`：启用，周日至周五 14:45。

自动化中只应迁移任务定义，不应复制或记录真实凭据。新电脑安装后先手动跑一次，再启用定时执行。

## 12. 下一台电脑接手后建议执行的第一步

第一步不是立即发布，而是建立一个可验证的本地基线：

1. 克隆仓库并切到 `main`，确认 `git rev-parse --short HEAD` 为 `f64eacf` 或更新且已审核的提交。
2. 通过安全渠道恢复 `data/taiwan-demo.db` 和确需保留的 `outputs/`，不要覆盖前先校验文件大小/哈希并留备份。
3. 重建 `.venv` 和 Node 依赖，设置 `X_HOTTOPIC_ROOT`，单独恢复公司中转站/模型提供方配置。
4. 运行 `scripts/project-memory-check.ps1` 和 `scripts/check.ps1`，再执行一次内容构建与审计。
5. 核对数据日期、`SOURCE_PENDING` 状态和公网 `gh-pages` 版本；所有门禁通过后，再考虑重装定时任务或申请发布授权。

推荐的首次核验命令：

```powershell
git status --short --branch
git rev-parse --short HEAD
powershell -ExecutionPolicy Bypass -File scripts/project-memory-check.ps1
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
```

预期：代码检查通过；如果本地数据库或当天来源尚未恢复，内容流水线可以明确停在 `SOURCE_PENDING`，但不能把这种状态报告成生产成功。

## 本次交接文件生成后的仓库预期状态

- 只新增未跟踪文件 `PROJECT_HANDOFF.md`。
- 现有已跟踪文件没有被修改。
- `git diff` 仍可能为空，因为默认 `git diff` 不显示未跟踪文件；应同时查看 `git status --short --branch`。
- 本次不提交、不推送、不更新 `gh-pages`。
