# Global X Finance — Taiwan Realtime Source Radar MVP

这是“一个核心引擎 + 多个 Market Pack”的第一阶段基础工程。台湾与美国使用完全相同的代码路径，市场差异只存在于 YAML 配置中。

当前工程在既有 TWSE Evidence、规则卡和冻结的合规模块之上，新增台湾实时来源治理、xHotTopic 只读发现适配器、YouTube Atom 监控、Windows 计划任务、来源健康页和最近两小时内容流。它仍然**不包含**财经观点生成、投资建议、全网覆盖声明、广告生成或提交、自动发帖、账号池、代理或限制规避功能。

## 非技术人员最快用法

在 Windows 中直接双击项目根目录的 `启动台湾Demo.bat`。脚本会自动创建或复用 `.venv`、安装依赖、幂等初始化数据库、校验并导入来源注册表，然后打开 `http://127.0.0.1:8765/`。

进入首页后点击「来源健康」查看实时来源状态，再到「最近两小时」查看发现流。计划任务只需安装一次，详见 `deliverables/实时监控使用说明.md`；演示话术见 `deliverables/老板Demo讲解稿.md`。

## 目录

```text
codex_mvp_inputs/              用户提供且保留原貌的输入包
docs/INPUT_AUDIT.md            输入审计结果
migrations/001_initial.sql     18 张业务表、索引与保护约束
migrations/002_twse_demo.sql   采集批次、数据集与去重计数字段
migrations/003_normalized_signals.sql  标准化字段、实体键和官方信号卡
migrations/004_x_ads_policy_precheck.sql  追加式政策快照、规则和检查清单
migrations/005_realtime_radar.sql  实时来源、周期、统一内容流和调度状态
migrations/006_radar_runtime_lock.sql  防止跨进程重复运行
migrations/007_radar_backfill_marker.sql  区分初始回填与持续监控新增
config/twse_openapi.datasets.json  从 TWSE Swagger 实际发现的可审计配置
config/taiwan_realtime_sources.csv  台湾实时来源治理注册表
config/x_ads_policy.pages.json     六个 X 官方政策页面注册表
config/x_ads_policy.rules.json     可回查快照的结构化规则
schemas/market-pack.schema.json
src/global_x_finance/          统一核心引擎
tests/                         全部使用 SYNTHETIC_TEST_DATA 的测试
scripts/check.ps1              一键测试与凭证扫描
scripts/start_demo.ps1         幂等的一键启动逻辑
scripts/run_realtime_radar.ps1  单次到期来源采集
scripts/install_realtime_radar_task.ps1  安装每 10 分钟 Windows 任务
启动台湾Demo.bat              双击入口
```

美国 Market Pack 当前是 `DRAFT_MISSING_VERIFIED_SOURCES`，来源数组为空。不要在获得已验证注册表前添加美国 API、RSS、KOL 或 Endpoint。

## 第一次运行

需要 Python 3.11 或更高版本。在 PowerShell 中进入本项目目录，然后依次运行：

### 1. 安装

```powershell
python -m pip install -e ".[dev]"
```

这会安装 Flask、YAML/JSON Schema 校验和测试所需的小型依赖。凭证必须通过环境变量提供；项目不读取或保存任何固定密钥。

### 2. 初始化数据库

```powershell
python -m global_x_finance.cli db init --db data/mvp.db --market-pack codex_mvp_inputs/taiwan.market-pack.yaml --market-pack codex_mvp_inputs/us.market-pack.template.yaml
```

此命令先用同一个 Schema 校验两个 Market Pack，再执行 SQLite migration，并登记 TW/US 两个市场及配置版本。重复执行是安全的。Demo 默认数据库是 `data/taiwan-demo.db`。

### 3. 校验并导入来源注册表

```powershell
python -m global_x_finance.cli sources import --db data/mvp.db --registry codex_mvp_inputs/verified_source_registry.csv
```

导入总是先完整校验。任何 `ACTIVE` 行缺少 `source_url`、`publisher`、`publisher_group`、`market`、`market_code`、`verified_at` 或 `evidence_url` 时，整个导入失败，不会部分写入。

请特别注意：

- `registry_status=ACTIVE` 只表示入口已核验存在。
- 是否具备采集条件由独立字段 `collection_status` 决定。
- 当前只有 `TW-A02` 是 `API_VERIFIED`。
- `BLOCKED_ROBOTS_OR_NEEDS_PERMISSION`、`NEEDS_TERMS_REVIEW` 和 `NEEDS_LICENSE_OR_TERMS_REVIEW` 不授权采集。
- 采集器只接受 `API_VERIFIED`，不会绕过 robots、登录、付费墙或授权限制。

只想校验、不导入时：

```powershell
python -m global_x_finance.cli sources validate --registry codex_mvp_inputs/verified_source_registry.csv
```

### 4. 保存并结构化 X 官方政策快照

```powershell
python -m global_x_finance.cli policies snapshot --db data/mvp.db --pages config/x_ads_policy.pages.json --rules config/x_ads_policy.rules.json
```

该命令只向配置中明确列出的 `business.x.com` 官方页面发送普通 GET 请求，要求 HTTP 200 和 HTML 响应，并保存原始响应、SHA-256、核验时间、摘要和版本关系。相同 URL 与相同响应哈希会复用旧记录；响应发生变化则追加新版本并通过 `supersedes_snapshot_id` 指向上一版，绝不覆盖历史。页面未明确提供更新时间时保存 `UNKNOWN`。

政策页面可能包含动态响应内容，因此重复核验即使语义未变也可能生成新版本。它是原始响应证据，不是“政策发生实质变化”的自动判断；差异仍需人工复核。

### 5. 运行完整测试

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check.ps1
```

该命令运行全部单元测试，然后扫描整个仓库中的疑似 API Key、Cookie、Token 或密码。任一步失败都会返回非零状态。

## 台湾实时雷达

校验并导入实时来源治理注册表：

```powershell
python -m global_x_finance.cli radar registry-validate --registry config/taiwan_realtime_sources.csv
python -m global_x_finance.cli radar registry-import --db data/taiwan-demo.db --registry config/taiwan_realtime_sources.csv
```

安装实际计划任务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install_realtime_radar_task.ps1
```

调度器每 10 分钟运行。已列 X 账号每 10 分钟到期，已核验 YouTube 频道每 30 分钟到期。当前只有一个 TWSE 官方 YouTube 频道，页面标为“初始验证覆盖”，不是“台湾 YouTube 覆盖完成”。初次回填不进入平均实时延迟；失败保留上次成功快照。X 使用 xHotTopic 的第三方只读发现适配器，不是官方 X API，也不代表覆盖整个 X 或平台 SLA。

实时注册表把六项状态分开保存：`identity_verified`、`endpoint_verified`、`monitoring_method_verified`、`terms_status`、`commercial_use_status` 和 `monitoring_status`。其中 `monitoring_status` 只允许 `ACTIVE`、`MANUAL_ONLY`、`NEEDS_VERIFICATION`、`BLOCKED`。公开入口可访问不代表已获商业监控授权；条款或商业使用为 `UNKNOWN` 时，系统不会推断为允许。最近一次运行结果另存在 `runtime_status`，不会覆盖治理状态。

## Evidence 保存接口

应用代码通过 `EvidenceStore` 写入原始证据：

```python
from global_x_finance.db import connect
from global_x_finance.evidence import EvidenceStore

database = connect("data/mvp.db")
result = EvidenceStore(database).save_raw_item(
    source_id="已导入的来源 ID",
    original_url="原始内容 URL",
    original_content="未经 AI 改写的原始内容",
    published_at="2026-01-01T00:00:00+00:00",
    fetched_at="2026-01-01T00:01:00+00:00",
    raw_payload={"保存": "原始响应或元数据"},
    data_label="RAW_EVIDENCE",
)
```

接口自动计算 SHA-256 `content_hash`。相同原始 URL 或相同哈希只返回已有记录，不新增副本。数据库触发器禁止更新 `original_content`、`raw_payload_json`、`original_url` 和 `content_hash`，因此后续 AI 输出无法覆盖原始证据。

测试构造的内容必须使用 `data_label="SYNTHETIC_TEST_DATA"`，不得伪装成真实行情。

## TWSE 官方资料发现与采集

实际使用的端点、资料集名称、字段、发现时间、查询时间及官方文件 URL 都保存在 `config/twse_openapi.datasets.json`。配置来自 TWSE 官方入口声明的 Swagger 文件，不使用猜测端点。

当前最多接入三项：每日收盘行情大盘统计、集中市场外资及陆资投资类股持股比率、上市个股日成交资讯。当前官方 Swagger 未列出三大法人净买卖资料集，因此本阶段明确跳过，不虚构替代端点。

## 标准化与规则卡

运行以下命令可幂等标准化现有 TWSE Evidence，并建立研究卡：

```powershell
python -m global_x_finance.cli normalize twse --db data/taiwan-demo.db --dataset-config config/twse_openapi.datasets.json
```

股票／证券记录保留市场、官方代码、官方名称、资料日期、开高低收、成交量、成交金额、涨跌和 `raw_item_id`。不存在的字段保存为 `UNKNOWN`。规则卡只做同一官方资料日期内的成交量前 10、成交金额前 10、绝对日涨跌幅前 10，以及官方外资及陆资持股比例展示；它们不是实时热点或投资建议。

## 数据规则

- IndependentSources 使用 `COUNT(DISTINCT publisher_group)`；同集团转载不增加数量。
- KOL、论坛、社交或社区来源默认 Claim 类型为 `OPINION`。
- A/B 可靠度证据同时存在 `SUPPORTS` 与 `CONTRADICTS` 时，Claim 更新为 `SOURCE_CONFLICT`。
- `commercial_fit_type` 在趋势和草稿表中只能是 `PREDICTED`，不能保存成实际转化率。
- 缺少六个已核验政策页面、产品类别、广告主体、牌照、X 预授权或关键检查资料时，合规检查不能写入 `PASS_PRECHECK`。
- 预检查只会输出 `PASS_PRECHECK`、`REVIEW_REQUIRED`、`BLOCKED` 或 `UNKNOWN`；即使通过也不表示 X 一定批准，且不替代台湾或美国法律意见。
- `UNKNOWN`、`NEEDS_VERIFICATION` 等未决状态会原样保存，不会被猜测性结论替代。

## 范围边界

`content_drafts` 仅为未来阶段保留数据表；当前没有生成入口。政策快照必须通过显式命令核验和追加，不会自动申请认证、生成广告或提交广告。当前四类模板中的实际广告主体、产品、牌照、X 预授权和落地页资料均为 `UNKNOWN`，因此不能把模板状态解释为可投放结论。

详见 [输入审计](docs/INPUT_AUDIT.md)、[产品定义](codex_mvp_inputs/product_definition.md) 与 [数据库契约](codex_mvp_inputs/database_schema.md)。
