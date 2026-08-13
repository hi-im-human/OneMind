# Freestyle Beats — Dependencies

## Hard requirements

| dependency | why | fails how without it |
|---|---|---|
| Claude Code runtime | the whole substrate | package is inapplicable |
| in-session cron tools (`CronList`, `CronCreate`) | beats ARE crons | skill step 3 has nothing to call |
| Python 3 on the runtime's PATH | both hooks | hooks silently never fire (runtime logs the spawn failure, agent sees nothing) |
| workspace `.claude/settings.json` | hook registration | no reminders; skill still works if run manually |
| workspace `.claude/skills/` directory | skill installation | `/freestyle-beats` unavailable |

## Soft requirements

| dependency | why | degradation without it |
|---|---|---|
| `WORK_GOALS.md` + `PERSONAL_GOALS.md` at workspace root | input for slot selection | skill has nothing to choose against; slots become generic. Templates ship in `src/templates/` |
| a notes file the agent keeps | breadcrumb step | beats still fire; continuity between sessions weakens |

## Runtime behaviors this package depends on (observed, not contractual)

These are properties of the Claude Code runtime as observed through 2026-08. They are
load-bearing assumptions, and any of them changing means revisiting the affected part:

1. **In-session crons are session-scoped and auto-expire at 7 days.** The whole
   re-run-at-session-start pattern exists because of this.
2. **Compaction unpredictably kills or keeps crons.** Both outcomes observed on one
   runtime in one day. The PostCompact hook's check-don't-assume wording depends on
   this staying unpredictable; if the runtime ever makes it deterministic, tighten the
   wording.
3. **Hook `additionalContext` requires `hookEventName: "SessionStart"`** — the
   validator drops `"PostCompact"` payloads silently. Both hooks emit `SessionStart`
   for this reason. If the runtime later accepts `"PostCompact"`, the workaround keeps
   working but stops being necessary.
4. **Skill invocations attach the full skill file to the fired prompt.** The basis of
   the literal-prompt-text rule and its ~78k chars/day measurement.

## Canonical dependency sweep

The full surface, stated explicitly rather than left to inference:

**Paths read at runtime**
- `<WORKSPACE>/.claude/skills/freestyle-beats/SKILL.md` (installed skill copy)
- `<WORKSPACE>/WORK_GOALS.md`, `<WORKSPACE>/PERSONAL_GOALS.md`
- `<PACKAGE_ROOT>/src/hooks/session_start_reminder.py` and
  `post_compact_reminder.py` — **read from package home on every hook fire**
- in-session cron state, via `CronList`

**Paths written / generated** (none by the package itself at runtime)
- installed skill copy (install step 1)
- goal files copied from templates (install step 2)
- two hook entries in `<WORKSPACE>/.claude/settings.json` (install step 3)
- in-session cron registrations (the agent, via the skill — never on disk)

**Tools / calls** — `CronList`, `CronCreate`, `python` (both hook commands)

**Consumers / triggers** — the SessionStart and PostCompact hook registrations in
`settings.json`, and `/freestyle-beats` invocation by the user or agent

**Config source** — `<WORKSPACE>/.claude/settings.json` and the chosen skill scope
(`!INSTALL.md` Runtime home)

## What depends on this package

**The agent's `settings.json` hook registrations are live consumers of both hook
scripts in package home.** Removing or moving `<PACKAGE_ROOT>` breaks both reminders —
silently, because hook failure is invisible to the agent (`!BUGS.md`). Moving the
package requires updating the two hook paths; removing it cleanly means the full
uninstall in `!INSTALL.md`, hook entries first.

Beyond its own installed pieces, nothing else consumes this package.
