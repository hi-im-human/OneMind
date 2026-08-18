# Freestyle Beats — Reference

## Primary runtime documentation

- **Claude Code scheduled tasks:**
  `https://code.claude.com/docs/en/scheduled-tasks`
  - session-scoped jobs;
  - fresh conversation vs `--resume`/`--continue` behavior;
  - `CronCreate`, `CronList`, `CronDelete`;
  - local-time five-field cron syntax;
  - deterministic jitter;
  - seven-day recurring expiry;
  - 50-task cap;
  - open/idle requirement and no missed-fire catch-up;
  - internal `.claude` storage is runtime-owned.
- **Claude Code hooks:** `https://code.claude.com/docs/en/hooks`
  - common hook input includes `cwd`;
  - SessionStart sources include startup/resume/clear/compact/fork;
  - `${CLAUDE_PROJECT_DIR}` is provided to hooks.
- **Claude Code skills:** `https://code.claude.com/docs/en/skills`
  - `${CLAUDE_SKILL_DIR}` and `${CLAUDE_PROJECT_DIR}` substitutions;
  - project skill installation/discovery;
  - scheduled skill invocation behavior.

These URLs were opened during the 2026-08-17 implementation. Re-open them before
changing runtime claims.

## Package-local evidence

- `src/scheduler.py` — executable state/reconciliation contract.
- `tests/test_scheduler.py` — local unit/integration fixtures.
- `tests/SMOKE_TESTS.md` — commands and live acceptance gates.
- `tests/release-receipt.json` — scoped release evidence; never stronger than its
  `verified`/`not_verified` fields.
- `!DECISIONS.md` — architecture choices and retained runtime workarounds.
- `!BUGS.md` — release blockers and documented boundaries.

## Historical observations retained with scope

- Live Claude Code 2.1.233 on 2026-08-17: model-visible CronList content contained exact
  task IDs/recurring labels, human-readable schedules, and prompt previews truncated near
  78 characters. The outer stream event contained full structured jobs, but that object
  was not in the model-facing tool content. This directly caused the schema-2 compact
  marker-prefix design; the revised candidate passed live revalidation the same day.
- Both cron survival and cron loss were observed after compaction on the ancestor
  runtime. The package therefore verifies with CronList rather than asserting either.
- Observed 2026-05-31: PostCompact `additionalContext` was delivered only when the hook
  output declared `hookEventName: "SessionStart"`. Claude Code 2.1.233 revalidated this
  workaround with a real `/compact` on 2026-08-17.
- An ancestor scheduled skill invocation attached approximately 11,200 characters per
  fire; seven daily fires produced approximately 78,000 characters/day. User beats use
  literal prompts; one maintenance skill invocation remains intentional and disclosed.
- The 2026-08-13 blind install/session/uninstall run verified the stateless 1.0.1
  candidate only. It is not evidence for 1.1.0 durability.
- One ancestor deployment restored from an external persisted schedule. That showed the
  needed state shape (exact schedule material) but did not test this package's former
  stateless path and is not a dependency of the public implementation.

## Out of scope

- external/shared schedule paths or content;
- direct parsing/editing of Claude Code's internal scheduled-task file;
- another agent's runtime IDs or personal state;
- Routines, Desktop scheduled tasks, OS task schedulers, or cloud services;
- broad claims from one local observation to every Claude Code version/provider.
