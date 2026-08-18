# Freestyle Beats

**Status:** 1.1.0 release-verified. Required local/live acceptance, independent review,
sanitization, and link/version gates pass.

**Purpose:** Persist and restore one installing workspace's 2–8 personal scheduled
prompts across fresh conversations, session loss, indeterminate compaction behavior, and
the runtime's seven-day recurring-task expiry.

**Runtime:** Claude Code 2.1.196+ · Python 3.8+ · `CronList` · `CronDelete` ·
`CronCreate`.

**Canonical state:**

```text
<WORKSPACE>/.claude/freestyle-beats/schedule.json
```

**Entrypoints:**

- `/freestyle-beats setup`
- `/freestyle-beats reconcile`
- `/freestyle-beats maintain`
- `/freestyle-beats refresh`
- `/freestyle-beats replace`
- `src/scheduler.py` (`create`, `show`, `validate`, `maintain`, `plan`,
  `verify-predelete`, `verify`, `uninstall-plan`)
- SessionStart and PostCompact hook wrappers under `src/hooks/`

**Behavior:** Canonical state is written before runtime tasks. Instance-scoped HMAC
prefix markers identify package jobs and exact canonical payload digests inside the
model-visible truncated prompt preview. The planner consumes the complete CronList result,
creates replacements, requires a post-create re-list before deletes, blocks above the
50-task peak limit, preserves foreign tasks, and records success only after final exact
verification. Daily maintenance chooses refresh when the last verified refresh is five
days old. Uninstall uses a generated HMAC-verified delete plan.

**Not included:** shared/family scheduling, another agent's state, cloud/OS scheduling,
or direct access to Claude Code's internal task file.

**Live acceptance:** Claude Code 2.1.233 passes schema-2 setup, compact-prefix visibility,
SessionStart/PostCompact delivery, fresh-conversation restore, idempotence, scheduled
maintenance self-refresh, literal user firing, partial loss, duplicate/error/cap handling,
upgrade, and full uninstall.

Install/rollback: `!INSTALL.md` · engineer contract: `!SPECS.md` · tests:
`tests/SMOKE_TESTS.md` · failures: `!BUGS.md`.
