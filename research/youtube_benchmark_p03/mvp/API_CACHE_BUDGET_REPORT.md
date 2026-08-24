# API、缓存与额度报告

## 实际调用

| 类型 | 实际外部调用 | 缓存命中 | 直接项目费用 | 状态 |
|---|---:|---:|---:|---|
| YouTube 公开 Atom feed | 3 | 6 | USD 0.00 | 3/3 `SUCCESS` |
| Web 公开研究工具 | 6 个批次（16 个查询、3 个页面打开） | 不适用 | 项目未购买 API；平台计量 `UNKNOWN` | `SUCCESS` |
| TranscriptAPI | 0 | 0 | USD 0.00 | `DISABLED / NOT_RUN` |
| 字幕请求 | 0 | 0 | USD 0.00 | `NOT_RUN` |
| local_text 合成测试 | 0 个网络调用 | 不适用 | USD 0.00 | `SUCCESS` |

YouTube Feed 的三次真实请求发生于 2026-08-16 20:04:48 +08:00，三个频道各一次。之后两轮解析复用了缓存，共六次缓存命中、零额外网络请求。原始调用记录位于 `calls_tw_stock.jsonl`、`calls_tech.jsonl` 与 `calls_macro.jsonl`。

## 后端状态

| 后端 | identity_verified | endpoint_verified | extraction_method_verified | terms_status | commercial_use_status | backend_status | actual_run_status |
|---|---|---|---|---|---|---|---|
| local_text/manual_transcript | 不适用 | VERIFIED | VERIFIED | APPROVED（用户提供文本路径） | UNKNOWN | AVAILABLE | SUCCESS（合成测试） |
| public_youtube_feed | 频道层 VERIFIED | VERIFIED | VERIFIED | UNKNOWN | UNKNOWN | AVAILABLE | SUCCESS |
| TranscriptAPI | 不适用 | NOT_RUN | DISABLED | UNKNOWN | UNKNOWN | DISABLED | NOT_RUN |

## 额度结论

- 没有注册账号、购买套餐、读取或写入 API Key。
- 每个视频字幕请求数均为 0，没有超过“一条视频最多一次”。
- `estimated_cost_usd=0.00` 只表示本轮没有产生可识别的第三方 API 采购费用；Codex/Web 工具自身平台计量不可见，保留 `UNKNOWN`。
