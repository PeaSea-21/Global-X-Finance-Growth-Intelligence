# P04 QA Report

执行日期：2026-08-16（Asia/Shanghai）
范围：仅 `skills/finance-youtube-benchmark/` 与 `research/youtube_benchmark_p03/p04/`；没有运行 P02、全项目检查、数据库、scheduler、UI 或 Git。

## 总结

| 类别 | 结果 | 证据 |
|---|---|---|
| Skill structure | PASS | 必需目录/文件 0 missing |
| P04 video schema | PASS | 30/30 records |
| P04 profile schema | PASS | 3/3 profiles |
| Unit tests | PASS | 9/9 |
| P03 real sample regression | PASS | `pilot-check` 0 errors |
| Data integrity | PASS | 30 unique IDs，0 missing/invalid canonical URL |
| Visual evidence | PASS | 30/30 manual visual review |
| Credential scan | PASS | Skill 与 P04 均 0 findings |
| Peer originality | PASS | A–B、A–C、B–C 均低于阻断阈值 |
| Source-text originality | NOT_RUN | `SOURCE_TEXT_ORIGINALITY_CHECK = NOT_RUN_SOURCE_TEXT_UNAVAILABLE` |
| Named imitation/catchphrase leakage | PASS | 0 hit |
| Finance evidence trace | PASS | F001–F007 全部出现且映射；无意外 fact ID |
| Browser acceptance | NOT_APPLICABLE | 没有页面/UI 交付 |

## 1. Data Integrity

- 视频总数：30。
- 每频道：老王愛說笑 10、M觀點 10、MacroMicro財經M平方 10。
- duplicate video IDs：0。
- missing canonical URLs：0。
- invalid canonical URLs：0。
- metadata 成功：30/30。
- view snapshot 为整数：30/30。
- thumbnail 实际核看：30/30。
- transcript 成功：0/30；所有记录为 `NOT_RUN`，请求次数均为 0。
- Pattern Library 引用不存在的视频 ID：0。
- Channel Profile 引用不存在的视频 ID：0。
- 4 个核心 JSON 均可解析；Schema validator 实际读取并验证了 dataset 与 profiles。

### Missing / unsupported fields

`duration`、`likes`、`comments` 为 `UNAVAILABLE`；`video_type` 为 `UNKNOWN`；`caption_status` 为 `NOT_RUN`。没有用估算值补齐。

### Unsupported claims / invented metrics

- 报告中的样本数、标题特征、视觉计数、topic 计数、ratio 与标签均可回溯 [video_dataset.json](video_dataset.json) 或 [performance_analysis.json](performance_analysis.json)。
- `performance_ratio` 是明确标注的派生指标：同频道 `actual_views / age_expected_views`；期望值来自该频道可比样本的 log-log 年龄模型。
- 阈值来自每频道真实 ratio 分布的 Q25、Q75 与 IQR；没有把任意“2 倍”写成爆款。
- 所有 performance 结论均标注 `PROVISIONAL`、小样本与相关非因果；没有伪造原始播放、CTR、watch time 或 subscriber 数据。

## 2. Schema and Structure

实际命令使用项目已存在的 dependency-free validator：

- `check-structure`：PASS，0 missing / 0 errors。
- `validate-list p04_video.schema.json video_dataset.json`：PASS，30 items。
- `validate-list p04_channel_profile.schema.json profiles_only.json`：PASS，3 items。

P04 新增两个最小 schema 只是覆盖 P04 新字段，没有修改既有 P03 schema、template 或测试行为。

## 3. Unit and Real-sample Tests

- `python -m unittest discover ...`：9 tests，全部 PASS。
- 覆盖：credential scan、local text 不持久化正文、来源复制阻断、不同文本通过、Atom 解析、peer 模式、Schema、Skill 结构、TranscriptAPI 禁用。
- `pilot-check --root research/youtube_benchmark_p03/mvp`：PASS，0 errors。

没有运行 P02 或仓库全局 `scripts/check.ps1`，因为本轮边界明确禁止干扰 P02。

## 4. Originality

阈值：peer longest contiguous match < 80 字符、8-gram Jaccard < 0.15、sequence ratio < 0.70。

| Pair | Longest match | 8-gram Jaccard | Sequence ratio | Result |
|---|---:|---:|---:|---|
| A–B | 40 | 0.079088 | 0.447186 | PASS |
| A–C | 40 | 0.080896 | 0.405956 | PASS |
| B–C | 54 | 0.089431 | 0.333857 | PASS |

人工与自动泄漏扫描：

- named creator imitation：0 hit。
- 节目名/口头禅：0 hit。
- 虚构个人经历：未发现。
- 原缩略图文案复用：未发现。
- `SOURCE_TEXT_ORIGINALITY_CHECK = NOT_RUN_SOURCE_TEXT_UNAVAILABLE`。没有字幕，因此不能声称已与创作者口播做来源相似度 PASS。

启发式相似度不是法律安全港；正式发布前仍需人类编辑与版权审阅。

## 5. Finance QA

- 样稿引用的 fact IDs：F001、F002、F003、F004、F005、F006、F007；无缺失、无意外 ID。
- F001：营收、年增、季增映射 PASS。
- F002：净利、EPS、毛利率、营业利益率映射 PASS。
- F003：2/3/5/7 奈米与 77% 映射 PASS。
- F004：HPC/智慧手机占比与季变动映射 PASS。
- F005：北美客户 78% 映射 PASS。
- F006：446–458 亿美元、利润率区间、汇率假设映射 PASS。
- F007：成本/利用率与海外厂稀释映射 PASS。
- 未发现股票目标价、买入价或卖出价。
- 三组均含非投资建议与前瞻不等于保证的边界。
- 创作者视频没有作为任何财务事实来源。

## 6. Credential, Calls and Retention

- `credential-scan skills/finance-youtube-benchmark`：PASS，0 findings。
- `credential-scan research/youtube_benchmark_p03/p04`：PASS，0 findings。
- 未读取、请求、打印或写入 API key。
- TranscriptAPI：`DISABLED / NOT_RUN`。
- 完整字幕：未请求、未保存。
- 30 张单图只用于人工检查；交付仅保留每频道一张联系图，共 3 张。

## 7. Path and File Check

8 个核心交付：

1. `P04_BENCHMARK_REPORT.md`
2. `video_dataset.json`
3. `channel_profiles_v2.json`
4. `pattern_library.json`
5. `performance_analysis.json`
6. `youtube_x_samples_v2.md`
7. `P04_QA_REPORT.md`
8. `P04_LIMITATIONS.md`

视觉证据附加 3 张联系图，避免保留 30 个不必要的单图文件。

## 8. Readiness QA Verdict

| Dimension | Verdict |
|---|---|
| CORE | READY |
| METADATA | PARTIAL |
| PERFORMANCE | PARTIAL |
| VISUAL | READY |
| TRANSCRIPT | NOT_READY |
| PROFILE | PARTIAL |
| PATTERN_LIBRARY | READY |
| GENERATION | READY |

**Overall：`P04_PARTIAL_READY`。**

该状态不是测试失败：它准确反映 metadata 缺字段、performance 混杂与 transcript 缺失；Topic/Title/Thumbnail/Pattern/Generation 已达到可用于下一批受控内容测试的程度。
