---
description: Durable personal scheduler for Claude Code session-scoped cron work, with local state recovery and maintenance.
---

# Freestyle Beats

**Personal persisted scheduling for Claude Code's session-scoped cron tools.**

## Status

**1.1.0 is release-verified.** Claude Code
2.1.233 passes installed setup, compact-prefix reconciliation, fresh-conversation restore,
SessionStart/PostCompact hooks, scheduled maintenance self-refresh, literal user fires,
partial-loss/duplicate/failure/cap recovery, upgrade, and full uninstall. Independent
code/security and documentation reviews pass; sanitization and link/version scans pass.

## What it does

1. Reads `WORK_GOALS.md` and `PERSONAL_GOALS.md` only during first setup or explicit
   replacement.
2. Persists 2–8 exact personal beats at
   `<WORKSPACE>/.claude/freestyle-beats/schedule.json`.
3. Prefixes each runtime prompt with a compact instance-scoped, HMAC-signed marker whose
   digest identifies the exact canonical payload inside CronList's truncated preview.
4. Reconciles canonical state through `CronList`, `CronDelete`, and `CronCreate`.
5. Runs daily maintenance and performs a create-first refresh when the last verified
   refresh is five days old, before Claude Code's seven-day expiry.
6. Uses SessionStart/PostCompact hooks to request restore from disk after session loss
   or indeterminate compaction behavior.

The package ships its **own personal scheduler**. It does not require or bundle an
external/shared scheduler, a daemon, cloud service, database, or private schedule.

## Quick start

1. Copy this package's `SKILL.md` and `src/` into
   `<WORKSPACE>/.claude/skills/freestyle-beats/`.
2. Copy the two goal templates to the workspace root and fill them in.
3. Register the two installed hook scripts using absolute paths in
   `<WORKSPACE>/.claude/settings.json`.
4. Start Claude Code in the workspace and run `/freestyle-beats setup`.
5. Run the tests in `tests/SMOKE_TESTS.md`; do not treat the package as released until
   the live-runtime blocking tests pass.

Full commands and rollback: `!INSTALL.md`.

## Runtime state

```text
<WORKSPACE>/.claude/freestyle-beats/
├── schedule.json       canonical durable schedule
├── candidate.json      setup/replace temporary; deleted after success
├── live-crons.json     complete CronList temporary; deleted after verify
├── plan.json           saved reconciliation plan; deleted after verify
└── after-create.json   complete pre-delete CronList temporary; deleted after verify
```

The runtime's internal task file is not a package interface and is never read or edited.
Runtime IDs are ephemeral. Exact cron expressions, labels, literal prompts, enabled
state, and verification timestamps live in `schedule.json`.

## Important files

| file | purpose |
|---|---|
| `SKILL.md` | setup/reconcile/refresh/replace procedure |
| `src/scheduler.py` | validation, atomic state, plan, verify, hook notice logic |
| `src/hooks/` | SessionStart and PostCompact entrypoints |
| `src/templates/SCHEDULE.template.json` | first schedule / replacement input shape |
| `!SPECS.md` | schemas, contracts, failure modes, ownership marker |
| `!INSTALL.md` | installation, settings JSON, verify, rollback |
| `!DEPENDENCIES.md` | every path, tool, trigger, config source, and consumer |
| `tests/SMOKE_TESTS.md` | local and live acceptance tests |

## Safety boundaries

- Persist before runtime creation.
- Never replace state because live jobs are absent.
- Never delete a task without a valid Freestyle Beats marker.
- Stop if state is malformed or CronList cuts/malforms the compact marker itself. A
  truncated tail after a complete marker is expected and sufficient.
- Create replacements, re-list and verify them, then delete old jobs; a reported create
  is not trusted without the pre-delete observation.
- Stop before mutation when create-first replacement would exceed the 50-task cap.
- Verify exact post-action state before recording success.
- Do not claim unattended scheduling while Claude Code is closed.

## Requirements

- Claude Code with `CronList`, `CronDelete`, and `CronCreate`;
- Python 3.8+;
- Claude Code 2.1.196+ for `${CLAUDE_PROJECT_DIR}` skill substitution;
- a writable, non-symlink `<WORKSPACE>/.claude/` directory;
- at most eight user beats (nine runtime tasks including maintenance).

License: Apache-2.0.
