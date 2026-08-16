---
name: project-memory
description: Restore and maintain this repository's durable project context. Use when starting or finishing a task, opening a new Codex chat, preparing a handoff, checking project status, or reviewing/repairing the repository memory files.
---

# Project Memory

Keep repository memory concise, evidence-based, and safe.

## Start a task

1. Resolve the Git repository root.
2. Read `AGENTS.md`, `docs/PROJECT_CONTEXT.md`, `docs/DECISIONS.md`, `docs/TASKS.md`, `docs/CHANGELOG_WORK.md`, and `docs/HANDOFF.md` completely.
3. Run `git status --short --branch`.
4. Verify task-relevant claims against current source, configuration, deliverables, and test output. Treat `HANDOFF.md` as a dated lead, not as authority.
5. Give the user a context recovery summary of no more than 10 lines covering the project goal, completed work, blockers, current task, and next step.

If a required file is absent or contradictory, label the gap `UNKNOWN` or `NEEDS_CONFIRMATION` and continue from stronger local evidence when safe.

## Maintain memory

- Put only long-lived facts in `PROJECT_CONTEXT.md`.
- Record formal decisions in `DECISIONS.md` with date, decision, reason, impact, status, and basis.
- Keep work state in `TASKS.md` under `NOW`, `NEXT`, `LATER`, `BLOCKED`, and `DONE`.
- Append concise, dated, actually completed work and verification to `CHANGELOG_WORK.md`.
- Replace `HANDOFF.md` with a short current handoff after meaningful work.
- Prefer correcting an existing entry over adding a duplicate.
- Use current user instructions, task specifications, code, configuration, and checks as higher authority than memory.

## Finish a task

1. Update task state and blockers in `TASKS.md`.
2. Add only newly adopted formal decisions to `DECISIONS.md`.
3. Record actual changes and verification in `CHANGELOG_WORK.md`.
4. Refresh `HANDOFF.md`, including one recommended next Codex task.
5. Run `powershell -ExecutionPolicy Bypass -File scripts/project-memory-check.ps1` and relevant project tests.
6. Report any failed or skipped verification without converting it into a success claim.

Never copy a full chat transcript into memory. Never store API keys, cookies, tokens, passwords, personal identity documents, or other sensitive credentials. Keep this skill only under this repository's `.agents/skills/project-memory/`; do not install or synchronize it to a user or global skills directory.
