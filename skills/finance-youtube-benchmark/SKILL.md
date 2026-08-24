---
name: finance-youtube-benchmark
description: Research and compare Taiwan and Chinese-language finance YouTube channels, ingest user-provided text without persisting full transcripts, extract narrative and voice features, create de-identified cross-creator style packs, and generate original YouTube and X drafts from separately verified finance facts. Use for channel discovery, video sampling, narrative benchmarking, creator comparisons, finance script generation, evidence validation, or originality review. Never use it to impersonate creators, treat creator opinions as facts, download full transcripts for storage, publish content, or give investment advice.
---

# Finance YouTube Benchmark

Build evidence-linked Taiwan finance video benchmarks and original drafts while separating creator style from financial facts.

## Workflow

1. Create a run from `templates/research_brief.yaml`.
2. Read `references/governance.md`; fail closed on identity, rights, credentials, cost, or retention gaps.
3. For discovery and sampling, read `references/workflow.md` and `references/adapters.md`.
4. For transcript/text analysis and profiles, read `references/analysis.md`.
5. Validate every factual claim against an independent FactPack before generation.
6. Generate only from a de-identified composite style pack; never imitate a named creator.
7. Run structure, schema, credential, evidence, and originality checks before handoff.

## Commands

Use the bundled Python runtime; no third-party packages are required.

```powershell
python scripts/benchmark_mvp.py check-structure --skill-root .
python scripts/benchmark_mvp.py ingest-text --input <local-text-file> --output <analysis.json>
python scripts/benchmark_mvp.py validate --schema <schema.json> --input <record.json>
python scripts/benchmark_mvp.py originality --candidate <draft.txt> --sources <source-a.txt> <source-b.txt>
python scripts/benchmark_mvp.py credential-scan --path <run-directory>
python scripts/benchmark_mvp.py adapter-status
```

Never pass credentials on the command line. The optional TranscriptAPI adapter stays `DISABLED` unless a future separately approved integration supplies a secret outside the repository.

## Required outputs

Produce channel verification, video sampling, analysis cards, channel profiles, cross-creator comparison, reusable narrative templates, FactPack, YouTube/X drafts, originality report, call ledger, limitations, and acceptance status. Use schemas in `schemas/` and templates in `templates/`.

Mark missing or unexecuted values `UNKNOWN`, `UNAVAILABLE`, or `NOT_RUN`. `READY` requires every mandatory automated check; human content and finance approval remain separate and this Skill never publishes.
