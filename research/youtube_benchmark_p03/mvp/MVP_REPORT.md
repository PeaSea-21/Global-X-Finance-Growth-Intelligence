# P03 Finance YouTube Benchmark MVP

> 最终状态：**P03 BENCHMARK MVP BLOCKED**
> 原因：实现与结构测试通过，但真实字幕、封面观察、来源侧原创性、条款/商业使用批准和人工双签尚未完成。

## 频道核验表

| 角色 | 频道 | 身份 | Feed端点/方法 | 条款 | 商用 | 选择理由 |
|---|---|---|---|---|---|---|
| 台股盘面/个股 | [老王愛說笑](https://www.youtube.com/channel/UCvnLmiWt_zIVIh0zUm_j4Hw) | VERIFIED | VERIFIED / SUCCESS | UNKNOWN | UNKNOWN | 高频台股、个股与题材对照；身份由浦惠投顾页面交叉确认 |
| 半导体/科技 | [M觀點](https://www.youtube.com/channel/UCT3uWFvKLVpRnEealmRwvrw) | VERIFIED | VERIFIED / SUCCESS | UNKNOWN | UNKNOWN | 官方网站明确定位科技、商业与投资频道 |
| 全球宏观联动 | [MacroMicro財經M平方](https://www.youtube.com/channel/UC6LU7FUBvbFCh_cQasrHZ_Q) | VERIFIED | VERIFIED / SUCCESS | UNKNOWN | UNKNOWN | 宏观数据、全球资产、台美股与半导体传导 |

没有按订阅量排序；三者是按角色互补、身份可核验、近期有足够公开样本和叙事差异入选。

## 九条视频采样表

| 频道 | 角色 | 视频 | 发布时间（台北） | 快照播放 | 日均候选值 | 基线 |
|---|---|---|---|---:|---:|---:|
| 老王愛說笑 | 近期 | [現在可以全壓0050正2嗎？](https://www.youtube.com/watch?v=vdW1eELwnsk) | 2026-08-16 19:00 | 4,740 | 4,740.0 | 15 |
| 老王愛說笑 | 高表现候选 | [被動元件哪些漲？哪些不漲？](https://www.youtube.com/watch?v=sgHsCaH2umQ) | 2026-08-15 19:00 | 39,159 | 37,408.1 | 15 |
| 老王愛說笑 | 典型 | [台積電再漲一倍？](https://www.youtube.com/watch?v=8GxNAzIg3CM) | 2026-08-11 14:00 | 47,686 | 9,073.6 | 15 |
| M觀點 | 近期 | [EP327](https://www.youtube.com/watch?v=3tAUC5Zg8rw) | 2026-08-10 13:28 | 6,407 | 1,020.6 | 15 |
| M觀點 | 高表现候选 | [EP326](https://www.youtube.com/watch?v=RolkbaZOwQg) | 2026-08-07 00:10 | 5,884 | 598.5 | 15 |
| M觀點 | 典型 | [EP320](https://www.youtube.com/watch?v=fT4GIObuq-s) | 2026-07-16 23:13 | 5,015 | 162.4 | 15 |
| 財經M平方 | 近期 | [After Meeting EP.210](https://www.youtube.com/watch?v=4gEpLNIRhhk) | 2026-08-16 09:00 | 12,095 | 12,095.0 | 15 |
| 財經M平方 | 高表现候选 | [從金融海嘯到AI浪潮](https://www.youtube.com/watch?v=Iv66HJtx2AY) | 2026-08-09 09:00 | 76,761 | 10,284.5 | 15 |
| 財經M平方 | 典型 | [After Meeting EP.206](https://www.youtube.com/watch?v=i_gEGJDcWu8) | 2026-07-12 09:00 | 7,642 | 215.5 | 15 |

日均候选值使用 `views / max(age_days, 1)`。Feed 缺少时长和格式，所以三个“高表现”都只是 `PROVISIONAL` 候选，不是质量或正确性判断。

## 交付索引

- 9 条结构化分析卡：`analysis/video_analysis_cards.json`
- 3 份频道叙事画像：`analysis/channel_profiles.json`
- 跨频道矩阵：`analysis/cross_creator_matrix.md`
- 叙事模板库：`analysis/narrative_template_library.md`
- 三份 YouTube/X 样稿：`generation/youtube_and_x_samples.md`
- FactPack 与映射：`evidence/factpack.json`, `evidence/fact_source_map.csv`
- 原创性报告：`qa/originality_report.md`
- API/缓存/额度：`API_CACHE_BUDGET_REPORT.md`
- Skill 使用：`SKILL_USAGE.md`
- 真实限制：`LIMITATIONS.md`
- 验收：`qa/acceptance_report.md`

## 事实与风格隔离

所有三稿使用同一份台积电 2Q26 官方 FactPack，来源仅为台积电投资人关系页面、盈余新闻稿与管理报告。频道视频只提供高层叙事观察，未被用作事实证据。
