# Repository Agent Instructions

These instructions apply to the entire repository.

## Project memory files

Maintain exactly these repository-level memory sources:

- `AGENTS.md`
- `docs/PROJECT_CONTEXT.md`
- `docs/DECISIONS.md`
- `docs/TASKS.md`
- `docs/CHANGELOG_WORK.md`
- `docs/HANDOFF.md`

Project memory is orientation, not the final source of truth. Current user instructions and task specifications take precedence; current code, configuration, deliverables, Git state, and test results decide factual conflicts.

## 任务启动协议（Task Start Protocol）

Before every new task:

1. Read all six project memory files listed above.
2. Run `git status --short --branch` and note whether history or a clean baseline exists.
3. Check the timestamp and claims in `docs/HANDOFF.md`; never treat an outdated handoff as fact.
4. Verify task-relevant claims against current code and actual test results. Mark anything unverified as `UNKNOWN` or `NEEDS_CONFIRMATION`.
5. Before substantive work, summarize in no more than 10 lines: project goal, completed work, current blockers, current task, and next step.

## Work rules

- Do not infer completed work solely from chat history or memory prose.
- Do not modify database business logic or schemas unless the current task explicitly requires it.
- Preserve user-authored files and unrelated working-tree changes.
- Keep `docs/PROJECT_CONTEXT.md` limited to durable, stable facts.
- Use `.agents/skills/project-memory/` only as a repo-local skill; do not install it globally.
- Run the checks proportionate to the change. The full existing project check is `powershell -ExecutionPolicy Bypass -File scripts/check.ps1`.
- For BEN Radar snapshots, preserve item-level pipeline trace, market-qualified security IDs, prior-session-only baselines, and source-concentration metadata; never convert missing market data to zero or stale news to current news.

## 任务结束协议（Task End Protocol）

At the end of every completed task:

1. Update `docs/TASKS.md` so `NOW`, `NEXT`, `LATER`, `BLOCKED`, and `DONE` reflect current evidence.
2. Add new formal decisions to `docs/DECISIONS.md`; do not log routine implementation details as decisions.
3. Append actual completed work and verification to `docs/CHANGELOG_WORK.md`.
4. Refresh `docs/HANDOFF.md` and keep it short, dated, and explicit about blockers, unfinished work, risks, and the recommended next Codex task.
5. Run `powershell -ExecutionPolicy Bypass -File scripts/project-memory-check.ps1` plus relevant project tests, and report the real result.

Never copy full chat transcripts into project memory. Never record API keys, cookies, tokens, passwords, personal identity documents, or other sensitive credentials. It is acceptable to state that a credential was configured or checked without storing its value.
