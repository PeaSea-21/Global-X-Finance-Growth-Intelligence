---
name: finance-youtube-inspiration
description: Turn lawful transcript, summary, notes, or creator-benchmark inputs into creator-neutral finance YouTube inspiration, narrative analysis, titles, hooks, evidence order, outlines, endings, and originality checks. Use when Codex is asked for 财经 YouTube 灵感、选题、标题、Hook、口播结构、博主叙事拆解、多博主优点融合、原创脚本大纲，或需要把真实财经 FactPack 转成不模仿具体人格的中文视频方案。
---

# Finance YouTube Inspiration

Create inspiration, not a creator clone. Keep creator-derived structure separate from finance facts.

## Workflow

1. Require a verified `FactPack` for factual claims. Treat creator material as style evidence only.
2. Accept transcript, summary, notes, or benchmark cards. If a local text file exists, run:

   `python scripts/text_features.py features <text-file>`

   Do not persist the source body.
3. Analyze the eight fields in [workflow.md](references/workflow.md). Mark every field `OBSERVED`, `INFERRED`, or `UNAVAILABLE`.
4. Select one audience task and one primary structure from [patterns.md](references/patterns.md). Blend at least three source families when claiming a composite style; no family may supply more than 40% of parameters.
5. Produce the compact contract in [output-contract.md](references/output-contract.md).
6. Compare any draft against source text before delivery:

   `python scripts/text_features.py compare <source-text> <draft-text>`

7. Block named-persona imitation, signature phrases, personal stories, unsupported facts, deterministic forecasts, and investment recommendations.

## Input fallback

- Transcript available: analyze wording, Hook, pacing, transitions, evidence order, uncertainty, CTA, and ending.
- Summary or notes only: analyze only supported semantic structure; exact wording and rhythm remain `UNAVAILABLE`.
- Metadata only: analyze topic/title/thumbnail packaging; do not invent Hook, script structure, viewpoint, rhythm, evidence use, or ending.

## Finance gate

Label output claims `FACT`, `INFERENCE`, or `OPINION`. Attach an authoritative URL to every important `FACT`. Attribute company guidance and keep it conditional. Creator statements never populate FactPack facts.

## Originality gate

Use new wording, new examples, and a new evidence sequence. Report comparison metrics as heuristic QA signals, not legal safe harbors. If source text is unavailable, report `ORIGINALITY_CHECK=PARTIAL`.
