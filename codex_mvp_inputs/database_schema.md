# MVP Database Schema Contract

数据库可使用 SQLite 或 PostgreSQL；MVP 优先选择最简单、可迁移的实现。所有主表使用不可变 UUID/ULID 主键，并保存 `created_at`、必要时保存 `updated_at`。

## markets

`id, country_code UNIQUE, country, primary_language, timezone, currency, status`

## market_pack_versions

`id, market_id FK, version, schema_version, config_json, status, effective_at, created_at`

## sources

`id, source_id UNIQUE, source_url, publisher, publisher_group, market_id FK, source_type, signal_role, reliability_level, verified_at, evidence_url, registry_status, collection_status, metadata_json`

ACTIVE 校验：`source_url, publisher, publisher_group, market_id, verified_at, evidence_url` 全部非空。

## collection_runs

`id, market_id FK, source_id FK, started_at, finished_at, status, item_count, error_code, error_message, collector_version`

## raw_items

`id, collection_run_id FK, source_id FK, original_url, canonical_url, original_content, published_at, fetched_at, content_hash, mime_type, raw_payload_json, data_label`

约束：`original_url` 或 `content_hash` 用于精确去重；已经保存的 `original_content` 与 `raw_payload_json` 不允许被 AI 输出覆盖。

## normalized_items

`id, raw_item_id FK UNIQUE, language, title, body, author, normalized_published_at, normalization_version, metadata_json`

## entities

`id, entity_type, canonical_name, market_id FK NULL, identifiers_json`

## item_entities

`item_id FK, entity_id FK, relation_type, confidence, PRIMARY KEY(item_id, entity_id, relation_type)`

## topics

`id, market_id FK, topic_key, title, status, first_seen_at, last_seen_at, clustering_version`

## topic_items

`topic_id FK, normalized_item_id FK, relevance_score, PRIMARY KEY(topic_id, normalized_item_id)`

## trend_snapshots

`id, topic_id FK, measured_at, trend_score, audience_fit, commercial_fit, commercial_fit_type, compliance_risk, independent_source_count, metrics_json, scoring_version`

约束：`commercial_fit_type = PREDICTED`。

## claims

`id, topic_id FK NULL, normalized_item_id FK NULL, claim_text, claim_type, status, subject_entity_id FK NULL, asserted_at, extractor_version`

允许状态：`UNVERIFIED, SUPPORTED, REFUTED, SOURCE_CONFLICT, UNKNOWN`。

## evidence_links

`id, claim_id FK, raw_item_id FK, relation, excerpt, source_url, observed_at`

允许 relation：`SUPPORTS, CONTRADICTS, CONTEXT`。同时存在可靠的 SUPPORTS 与 CONTRADICTS 时 Claim 必须为 `SOURCE_CONFLICT`。

## content_drafts

`id, market_id FK, topic_id FK, account_profile_id NULL, draft_type, body, cta, commercial_fit_type, commercial_fit_score, status, generation_version`

`draft_type = ORGANIC | PROMOTED`；第一阶段可以只建表，不生成内容。

## verification_runs

`id, content_draft_id FK NULL, topic_id FK NULL, verifier_type, started_at, finished_at, result, findings_json, evidence_read_json`

## policy_snapshots

`id, market_id FK NULL, policy_name, policy_url, fetched_at, content_hash, content_text, status`

## compliance_checks

`id, content_draft_id FK, policy_snapshot_id FK NULL, result, risk_level, findings_json, checked_at`

允许 result：`PASS_PRECHECK, REVIEW_REQUIRED, BLOCKED, UNKNOWN`。缺少产品、广告主体或牌照信息时不能为 `PASS_PRECHECK`。

## review_decisions

`id, content_draft_id FK NULL, topic_id FK NULL, reviewer, decision, notes, decided_at`

## 最低索引与唯一约束

- `sources(source_id)` UNIQUE
- `markets(country_code)` UNIQUE
- `raw_items(source_id, original_url)` UNIQUE（URL存在时）
- `raw_items(source_id, content_hash)` UNIQUE
- `normalized_items(raw_item_id)` UNIQUE
- `market_pack_versions(market_id, version)` UNIQUE
- 为所有时间字段、外键和 `publisher_group` 建普通索引。
