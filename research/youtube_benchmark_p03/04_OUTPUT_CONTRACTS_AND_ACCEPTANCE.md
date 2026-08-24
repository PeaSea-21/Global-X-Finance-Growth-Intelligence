# 输出字段、文件结构与验收标准

## 1. 建议运行产物目录

以下是未来实施建议，不是本轮已创建的运行系统：

```text
research_runs/youtube_benchmark/<run_id>/
  manifest.yaml
  inputs/
    research_brief.yaml
    channel_candidates.csv
    factpack.yaml
  governance/
    source_governance.csv
    rights_review.md
  discovery/
    channels.csv
    videos_snapshot.csv
    selection.csv
  analysis/
    video_features.jsonl
    channel_profiles.yaml
    cross_creator_matrix.csv
    composite_style_pack.yaml
  generation/
    claim_source_map.csv
    youtube_outline.md
    youtube_script.md
    x_posts.md
  qa/
    acceptance.json
    similarity_report.md
    fact_check_report.md
    human_approval.yaml
  ephemeral/                 # gitignored; run-end deletion
    transcripts/
```

## 2. `manifest.yaml`

必需字段：

```yaml
run_id: string
created_at: datetime
created_by: string
skill_version: string
analysis_version: string
mode: discover | benchmark | compose-style | generate | evaluate
market: TW
language: zh-Hant-TW
as_of: datetime
status: COMPLETE | PARTIAL | BLOCKED | FAILED
limitations: [string]
cost_budget:
  currency: USD
  max: number
  actual: number | UNKNOWN
network_calls:
  count: integer
  providers: [string]
ephemeral_cleanup_status: COMPLETE | NOT_REQUIRED | FAILED
```

## 3. 频道字段 `channels.csv`

- `channel_id`, `channel_url`, `channel_title`
- `identity_status`, `creator_type`, `market_scope`, `topic_scope`, `language`
- `discovery_source_url`, `discovered_at`
- `latest_publication_at`, `sample_available_count`
- `terms_status`, `commercial_use_status`, `analysis_eligibility`
- `exclusion_reason`, `notes`

## 4. 视频快照字段 `videos_snapshot.csv`

- `video_id`, `channel_id`, `video_url`, `title`
- `published_at`, `captured_at`, `duration_seconds`, `format_type`
- `view_count`, `like_count`, `comment_count`（允许为空）
- `metadata_provider`, `metadata_status`, `metadata_age_hours`
- `is_live`, `is_short`, `promotion_signal`, `major_event_context`
- `rights_status`, `retention_deadline`, `refresh_required_at`

## 5. 视频选择字段 `selection.csv`

- `video_id`, `selection_role`: WINNER / TYPICAL / FLOP / OUTLIER_CANDIDATE / FORMAT_VARIANT
- `selection_method`: HUMAN / PROVIDER_LABEL / APPROVED_INTERNAL_DERIVED
- `comparison_bucket`, `baseline_count`
- `velocity`, `robust_z`（若未批准必须为空）
- `confounders`, `confidence`, `selected_by`, `selected_at`
- `why_selected`, `not_quality_or_truth_signal=true`

## 6. 视频特征 `video_features.jsonl`

```json
{
  "video_id": "...",
  "transcript": {
    "status": "AVAILABLE|UNAVAILABLE|PARTIAL",
    "provider": "...",
    "language": "zh-Hant",
    "sha256": "...",
    "fetched_at": "...",
    "body_persisted": false
  },
  "narrative": {
    "packaging_promise": "...",
    "hook_type": "...",
    "central_question": "...",
    "chapters": [],
    "open_loops": [],
    "rehooks": [],
    "payoff": "...",
    "cta": "..."
  },
  "finance_reasoning": {
    "creator_opinion_claims": [],
    "evidence_mention_count": 0,
    "uncertainty_markers": [],
    "unsupported_claim_count": 0
  },
  "rhythm": {
    "ideas_per_minute": 0,
    "numbers_per_minute": 0,
    "sources_per_minute": 0,
    "questions_per_minute": 0,
    "rehook_interval_seconds_median": null,
    "loop_close_rate": null
  },
  "copyright": {
    "verbatim_quote_count": 0,
    "long_excerpt_present": false
  }
}
```

## 7. 频道画像字段

- `profile_id`, `channel_id`, `sample_count`, `sample_window`
- `status`: PROVISIONAL / EVIDENCE_SUFFICIENT
- `core_audience_promise`
- `winning_patterns[]`, `failure_patterns[]`
- `hook_distribution`, `structure_patterns`, `evidence_order_patterns`
- `pacing_profile`, `uncertainty_profile`, `cta_profile`
- `anti_patterns[]`, `signature_elements_do_not_reuse[]`
- `source_video_ids[]`, `analyst_confidence`, `limitations[]`

## 8. 生成字段

### YouTube

- `script_id`, `title_variants[]`, `thumbnail_briefs[]`
- `target_runtime`, `audience`, `single_sentence_promise`
- `hook`, `setup`, `chapters[]`, `rehooks[]`, `payoff`, `cta`
- `fact_ids[]`, `inference_ids[]`, `source_gap_ids[]`
- `risk_disclosure`, `as_of`, `language`, `originality_declaration`
- `estimated_words`, `estimated_runtime_minutes`

### X

- `x_package_id`, `format`: SINGLE / THREAD
- `posts[]`: `sequence`, `text`, `fact_ids`, `source_urls`, `character_count`
- `as_of`, `risk_disclosure`, `originality_declaration`

## 9. 自动验收标准

### 研究完整性

- 每个入选频道至少 8 个可用视频样本；不足则强制 `PROVISIONAL`。
- 频道画像必须含赢家、普通和失败样本，不能只研究爆款。
- Composite Style Pack 至少 3 个频道，单一频道权重 ≤0.40。
- 每条高层结论至少关联 2 个 `source_video_id` 或明确标低置信度。

### 数据与条款

- 所有数据行有 provider、captured_at、rights/terms 状态。
- `UNKNOWN` 不得通过权限闸门。
- 未批准衍生指标时 `velocity/robust_z` 必须为空。
- 非授权公开 API 数据超过允许期限前必须 refresh/delete；保留策略必须可配置并有清理日志。
- 完整字幕不能出现在永久目录、日志、Git 或最终报告。

### 版权与原创

- `verbatim_quote_count = 0` 为默认验收值。
- 不出现长段来源文本、逐句翻译、近义改写全文。
- 不出现来源频道标志性开场、口头禅、个人故事或唯一比喻。
- 对最终脚本与临时来源片段做 n-gram/语义近似检查；阈值需由人工金标集校准，不能凭空设为“绝对安全”。
- 高相似片段必须有定位、来源和重写结果；未解决则 `BLOCKED`。

### 财经事实

- 每个外部可核验 claim 有 `fact_id`；覆盖率必须 100%。
- 每个数字有单位、币种、市场、`as_of` 和来源。
- 博主视频只可产生 `CREATOR_OPINION`，不能成为 `OFFICIAL/FACT`。
- `STALE`、`SOURCE_CONFLICT`、`UNKNOWN` 不得作为确定陈述进入脚本。
- 不包含收益承诺、确定性涨跌预测、个性化买卖建议。

### 台湾本地化

- 默认繁体中文与台湾常用金融用语。
- 交易日期、台北时间、UTC 和美东时间不混淆。
- 台股代码、TWD/新台币、張/股、億元等单位一致且可追溯。
- 海外公司/指标保留原文名或标准译名，避免自造译名。

### 结构与可拍摄性

- 首 30 秒明确兑现标题/封面承诺。
- 每个章节有一个工作目标和所用 fact_ids。
- 开环最终有回收；未回收项为 0。
- 目标时长与估算字数偏差在人工批准范围内。
- X 内容与 YouTube 使用同一 FactPack，不新增无来源事实。

## 10. 人工验收

至少两人签核：

```yaml
content_lead:
  status: APPROVED | CHANGES_REQUESTED | REJECTED
  reviewer: string
  reviewed_at: datetime
  notes: string
finance_reviewer:
  status: APPROVED | CHANGES_REQUESTED | REJECTED
  reviewer: string
  reviewed_at: datetime
  notes: string
final_status: READY_FOR_MANUAL_PRODUCTION | BLOCKED
```

`READY_FOR_MANUAL_PRODUCTION` 仅表示可以进入人工制作，不表示投资建议、事实永久有效、平台合规获批或自动发布授权。

## 11. 未来测试夹具

- 3 个授权/人工准备频道，每频道 10 条元数据和结构标注。
- 至少 2 条无字幕、1 条直播、1 条 Shorts、1 条重大事件视频。
- 1 个包含提示注入文本的合成字幕夹具，验证不会执行其中指令。
- 1 个事实冲突、1 个过期数字、1 个单位混淆 FactPack。
- 1 个过度贴近单一创作者的故意失败脚本。
- 1 个通过全部检查的原创繁中台湾财经脚本与 X thread 金标。
