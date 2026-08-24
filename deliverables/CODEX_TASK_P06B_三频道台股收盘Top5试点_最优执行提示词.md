# CODEX TASK P06B：三频道台股收盘 Top 5 试点

> 执行方式：完整读取本提示词后，直接在当前仓库实施、验证并交付。不要只给方案，不要停在伪数据页面，不要把未实现写成已完成。

## 一、业务目标

为财经内容团队实现一个可运行的 Channel-driven 收盘选题工具：

1. 台股正常交易日收盘后，等待各批准来源的 EOD 数据达到可用状态。
2. 默认在 `15:05 Asia/Taipei` 生成当日主版本；时间必须可配置，不能写死在业务代码中。
3. 将真实新闻、公司事件、市场话题和股票异常转换成对应频道的选题候选。
4. 每个试点频道展示排序 `1–5` 的主榜；有更多合格候选时可保留备选。
5. 每条候选必须解释为什么今天讲、为什么适合该频道，并展示相关个股详情和 Evidence。
6. 第一阶段只做三个已批准台股试点，不扩到全部 20 频道：
   - `資金雷達 / SIGNAL_HEAVY`
   - `個股顯微鏡 / EVENT_HEAVY`
   - `產業透視鏡 / CROSS_ENTITY`

## 二、当前事实基线

- 仓库已有 TWSE/TPEx 统一 EOD、历史基线、Anomaly Engine V0.1、Stock Workbench、有限 MOPS、新闻/X 事件路径。
- P06A 已生成 20 个有 provenance 的 `ChannelProfile v0.1 DRAFT`，三个试点已获用户批准。
- 当前运行库尚无 Channel Profile、Channel Assignment 或 Channel Daily Brief 实现。
- Industry Mapping 的 migration/module/tests 位于未提交工作树中；使用前必须测试并应用到当前运行库，且只可用于候选召回。
- 当前没有生产 LLM Provider。不得把规则排序伪装成 AI 排序。
- 台股当前运行库的最新完整 EOD 日期、事件日期和来源就绪状态必须在执行时重新查询，不得照抄本提示词中的历史日期。

## 三、不可突破的边界

1. 不修改 Anomaly Engine V0.1 阈值和排名。
2. 不把价量异常写成法人、ETF 或机构资金净流入。
3. 不把同产业共现写成订单、上下游、供应链或因果关系。
4. 新闻、X、KOL 和媒体材料不得自动升级成财经事实；保留 `OPINION / UNKNOWN / SOURCE_CONFLICT`。
5. 不补造新闻、公告、股票、数字、Evidence、来源可用性或模型结果。
6. 不用旧闻、重复事件或弱证据强行凑足五条。少于五条时显示真实数量和 shortage reason。
7. 不接入新美股、加密、付费行情、自动发帖或自动互动。
8. 不创建公网分享，不安装系统计划任务，除非用户另行明确授权。
9. 保留用户和并行任务的未提交改动，特别是 Industry Mapping 与 YouTube/X 产物。

## 四、收盘就绪合同

必须把“时间到了”和“数据真的可用”分开。

### 4.1 状态

- `WAITING_FOR_CLOSE`：台股尚未收盘。
- `SOURCE_PENDING`：已收盘，但必要 EOD 来源尚未出现当日完整数据。
- `READY`：必要 EOD 覆盖通过，可以生成主版本。
- `DEGRADED`：主版本已生成，但可选事件来源缺失或延迟；页面必须显示缺口。
- `FAILED`：必要数据或生成过程失败，不能复用旧简报冒充今日结果。

### 4.2 就绪字段

每个 Brief 至少保存并展示：

```text
market
market_session_date
session_state
scheduled_for
generated_at
data_as_of
source_readiness[]
coverage_status
brief_version
```

### 4.3 生成规则

- 默认主构建时间为 15:05，但以最新完整 EOD session 和最低市场覆盖门槛为事实条件。
- 迟到来源可触发同一 `channel × market_session_date` 的新版本；旧版本保留审计信息。
- 所有候选只允许使用 `published_at / announced_at / trade_date <= data_as_of` 的数据。
- Replay 必须以固定历史 as-of 运行，禁止使用未来 Evidence。

## 五、统一候选池

所有输入先转成一个受控 `TopicCandidate`，再做频道分配：

```text
candidate_id
candidate_type: MARKET_SIGNAL | DISCLOSURE | NEWS_EVENT | X_EVENT | CROSS_ENTITY
title
market_session_date
data_as_of
security_ids[]
industry_keys[]
facts[]
evidence[]
opinion_evidence[]
unknowns[]
risk_flags[]
freshness_state
```

候选来源：

- Anomaly Engine 中命中至少一个规则的真实 EOD 股票。
- MOPS 重大讯息；事件日期和发布时间必须明确。
- 在 Replay as-of 前已存在的新闻/X 统一事件；独立 publisher group 继续去重。
- Industry Mapping 中 `MAPPED_COMMON_STOCK` 的官方产业分组，仅用于将多个股票异常召回到同一产业候选。

## 六、三个频道的差异

### 6.1 資金雷達

- 主输入：EOD 量价异常。
- 选择偏好：多规则、量价共振、异常放量、突破、相对成交量和可见流动性。
- 必须显示：收盘价、涨跌幅、成交量、20 日成交量中位数、RVOL、规则、历史比较。
- 固定边界文案：这是价量/成交异动，不是机构或 ETF 净流入。

### 6.2 個股顯微鏡

- 主输入：MOPS/新闻公司事件 + 同一股票的 EOD 表现。
- 有官方披露时标 `READY_TO_PITCH`；只有异常、催化剂未确认时标 `NEEDS_RESEARCH`。
- 必须显示：事件标题、公告/新闻时间、关键事实、个股 EOD 详情、催化剂状态、未知和 Evidence。
- 月营收、完整财报、法说和 Guidance 未接入时保持 shortage，不得生成替代事实。

### 6.3 產業透視鏡

- 主输入：同一官方产业分组内的多个真实 EOD 异常，辅以独立事件 Evidence。
- 至少两个映射证券才能形成 `CROSS_ENTITY` 候选；否则保持单股候选或 shortage。
- 必须显示：官方产业名称、异常公司列表、各股票指标、共同点和差异点。
- 固定边界文案：官方产业共现只用于候选召回，不证明供应链传导或共同催化剂。

## 七、排序合同

### 7.1 硬门槛先于排序

候选必须先通过：

- 当日/Replay 时点有效性。
- 至少一个可回链 Evidence。
- 股票 ID 为市场限定 ID，例如 `TWSE:2330`。
- Channel Profile 命中。
- 同频道重复/近似候选去重。
- 财经事实与观点分离。

### 7.2 排序维度

合格候选按以下顺序解释排序，不生成虚假的 0–100 投资分：

1. `channel_fit`：与频道定位的匹配程度。
2. `why_now_strength`：当日变化或事件强度。
3. `evidence_strength`：官方/独立 Evidence 和未知程度。
4. `talkability`：是否能形成明确、不同于其他候选的内容问题。
5. `novelty_and_duplication`：是否重复、是否只是同一事件改标题。
6. 稳定候选 ID 作为最终 tie-breaker。

### 7.3 AI 与回退

- 提供结构化 `ChannelRanker` 接口。模型只接收候选 ID 和已验证字段，只能返回已有候选 ID 的顺序及理由。
- 模型不得新增事实、股票、数字、因果关系或 Evidence。
- 模型真实调用成功才标 `AI_RANKED`，并保存 provider/model/prompt/profile 版本。
- 没有 Provider、超时或返回无效时使用 `RULE_BASED_FALLBACK`，保存失败/不可用原因，页面不得显示“AI 已排序”。

## 八、持久化与审计

新增 migration，至少包含：

- `ben_channel_profiles`
- `ben_channel_brief_runs`
- `ben_channel_daily_briefs`
- `ben_channel_topic_assignments`

要求：

- Profile 版本化，不覆盖原始 P06A 资料。
- Brief 按频道、交易日和版本保存。
- Assignment 保存候选类型、排名、理由、状态、事实、Evidence、股票详情、未知和风险。
- 同一生成输入应幂等；新来源到达时产生可审计的新版本，不原地篡改旧版本。
- 缺失值保存为 null/UNKNOWN，不转成 0。

## 九、可运行入口

1. 新增可重复命令，例如 `scripts/generate_channel_briefs.py`：
   - 可指定数据库、Replay 日期、生成时点。
   - 可选择只预览或持久化。
   - 输出三频道 JSON/Markdown 审计产物。
2. 如 Industry Mapping 尚未同步，提供受 registry `API_VERIFIED` 约束的官方映射同步命令；保存 Raw Evidence。
3. 新增 `/channel-radar` 页面：
   - 首屏就是三个频道及其合格数、状态和数据时间。
   - 点击频道切换该频道 Top 5。
   - 每条显示排名、类型、标题、Why Now、Why Channel、股票详情、Evidence 和风险。
   - 不把内部采集诊断堆在主页面；详细 Evidence 可展开。
   - 桌面和移动端无横向溢出、无文字重叠、无控制台错误。

## 十、真实执行与验收

必须完成：

1. 最近五个完整台股交易日 Replay。
2. 当前最新完整 EOD 日期的三频道 Brief。
3. 每个 Replay 的所有候选都满足 prior-only 与 as-of 约束。
4. `資金雷達`、`個股顯微鏡`、`產業透視鏡` 的 Top 5/shortage 与理由明显不同。
5. 产业候选不出现未映射证券或因果式供应链结论。
6. 没有模型时所有产物明确为 `RULE_BASED_FALLBACK`。
7. 新 migration、核心算法、幂等、短缺、未来数据阻断、Web route 均有测试。
8. 运行相关测试和完整 `scripts/check.ps1`。
9. 启动本地服务，用浏览器检查桌面和移动端；保存必要截图/审计产物。
10. 运行 `scripts/project-memory-check.ps1` 和 `git diff --check`。

## 十一、交付物

- 本提示词。
- P06B migration、配置、模块、脚本、页面和测试。
- `research/ben_radar_channel_p06b/` 下的五日 Replay、最新简报、source readiness 和验收报告。
- `deliverables/BEN_RADAR_P06B_三频道台股收盘Top5试点报告.md`。
- 更新后的 Project Memory 与短交接。

## 十二、完成定义

只有在真实运行库产生可审计的三个频道收盘简报、相关测试通过、页面经桌面/移动检查后，才能称 `P06B_IMPLEMENTED_READY_FOR_HUMAN_PILOT`。

如果真实数据覆盖导致某频道不足五条，这不是失败；必须显示 `HONEST_SHORTAGE`、实际数量和具体原因。若核心链路仍未实现，则报告 `PARTIAL / BLOCKED`，不得为了完成感伪造数据或状态。
