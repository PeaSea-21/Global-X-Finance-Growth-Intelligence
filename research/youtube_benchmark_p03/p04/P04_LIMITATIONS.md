# P04 Limitations and Call Ledger

## 真实限制

1. `duration`、`likes`、`comments` 未由本轮批准的官方公开缓存可靠提供，30/30 均为 `UNAVAILABLE`。
2. `video_type` 未经官方字段确认，30/30 为 `UNKNOWN`；另保留 `format_signal`，仅表示标题或缩略图出现 Shorts、Podcast、直式切片等信号，不能替代正式类型。
3. `caption_status` 为 `NOT_RUN`，不是 `no_caption`。没有调用字幕端点、没有播放视频、没有保存完整字幕。
4. 因此 first 30s、真实章节顺序、句式节奏、转折、风险提示与 CTA 均为 `UNAVAILABLE`，Channel Profile V2 的 Narrative 层维持 LOW。
5. 播放数是 2026-08-16 捕获时点快照，不是实时值；没有 impressions、CTR、watch time、retention 或 subscriber exposure。
6. Performance baseline 只控制发布年龄；duration、正式视频类型、发布时间段、流量来源与主题时点仍是混杂变量。标签只表示同频道相对表现，不表示内容质量、真实性或投资价值。
7. 每频道 10 条仍是小样本。主题多标签会重复计数；财报、利率等小组不宜泛化。
8. 缩略图 30/30 已实际查看，但视觉编码是人工高层分类；没有 OCR 置信度或多人复核。
9. Title/thumbnail 与播放表现只有相关关系；没有随机实验或 CTR，不能归因因果。
10. 创作者内容没有进入 FactPack。V2 生产只复用 P03 已锁定的 `TSMC-2Q26-OFFICIAL-v1`；P04 没有重新抓取或重新验证该 FactPack。

## Adapter / evidence 状态

| 路径 | identity_verified | endpoint_verified | extraction_method_verified | terms_status | commercial_use_status | backend_status | actual_run_status |
|---|---|---|---|---|---|---|---|
| P03 频道身份记录 | VERIFIED | VERIFIED | VERIFIED | UNKNOWN | UNKNOWN | AVAILABLE | SUCCESS_REUSED |
| YouTube 官方公开 Atom 缓存 | VERIFIED | VERIFIED | VERIFIED | UNKNOWN | UNKNOWN | AVAILABLE | SUCCESS_CACHE_HIT |
| `i.ytimg.com` 公开缩略图 | N/A | VERIFIED | VERIFIED | UNKNOWN | UNKNOWN | AVAILABLE | SUCCESS_30_OF_30 |
| local_text/manual_transcript | N/A | VERIFIED | VERIFIED | APPROVED | UNKNOWN | AVAILABLE | NOT_RUN |
| TranscriptAPI | N/A | NOT_RUN | DISABLED | UNKNOWN | UNKNOWN | DISABLED | NOT_RUN |

`UNKNOWN` 不代表获准商用；技术成功不会自动升级 terms 或 commercial-use 状态。

## 外部调用、缓存与估算费用

| 调用类别 | P04 网络调用成功数 | cache hit | 本地失败尝试 | 估算费用 | 说明 |
|---|---:|---:|---:|---:|---|
| YouTube Atom metadata | 0 | 3 个频道 | 0 | USD 0.00 | 直接复用 P03 官方 feed 缓存，未重复请求 |
| Public thumbnails | 30 | 0 | 30 | USD 0.00 | 首批 30 次在执行环境网络沙箱内被阻断、未到端点；获准后每图只成功请求一次 |
| Transcript/caption | 0 | 0 | 0 | USD 0.00 | TranscriptAPI 保持 DISABLED；每视频请求次数 0 |
| Fact sources | 0 | 1 个 FactPack | 0 | USD 0.00 | 沿用 P03 已锁定台积电官方证据包 |
| Paid API / account / login | 0 | 0 | 0 | USD 0.00 | 未注册、未付费、未登录、未使用 API key |

“本地失败尝试”指沙箱在 HTTP 出站前拦截的尝试，不计为成功外部调用；为了审计透明仍单列。

## 真正阻碍下一阶段的事项

- 若要把 Narrative/Hook/Profile 升级为 READY，需要一个用户已授权、条款明确、无需绕权且不永久保存完整字幕的合法字幕或人工文本输入路径。
- 若要把 Metadata/Performance 升级为 READY，需要官方授权渠道提供 duration、正式视频类型、likes/comments（如适用）、以及最好包含 impressions/CTR/watch time 的频道自有数据。没有这些数据时无法可靠拆分“题材、封面、时长、分发”的影响。
- 若要从相关研究升级为增长因果，需要在自有频道做受控标题/封面实验；Benchmark 观察本身不能证明因果。

这些限制不阻碍当前团队使用 Topic、Title、Thumbnail、Pattern Library 与原创 V2 进行下一批内容测试。
