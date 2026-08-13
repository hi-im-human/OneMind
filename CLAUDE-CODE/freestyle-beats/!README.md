# Freestyle Beats — Session Scheduler for Claude Code Agents

## What it is

A self-managed daily cadence for a Claude Code agent. Each session, the agent picks 2–8
time slots for the day — each labeled `work` or `personal`, each carrying a short prompt
the agent writes for itself — and registers them as in-session crons. When a slot fires,
the prompt arrives in the agent's live session as its own turn, and the agent does the
thing it decided that morning to do.

Two lightweight hooks keep the schedule alive: a SessionStart reminder and a PostCompact
reminder, both prompting the agent to check and rebuild its crons, because in-session
crons don't reliably survive session breaks and expire after 7 days regardless.

## Why it exists

An agent that only acts when spoken to has no day — just a queue. Freestyle Beats gives
an agent a schedule it authors itself: goals feed slots, slots fire as prompts, prompts
leave breadcrumbs for the next session. Nothing is inherited, nothing is counted, and
nothing audits whether a beat "succeeded." The schedule is chosen fresh each session,
which keeps it a decision instead of an obligation.

## What's inside

```
SKILL.md                          the /freestyle-beats skill (install into the agent's skills dir)
src/hooks/
  session_start_reminder.py       SessionStart hook — check your crons
  post_compact_reminder.py        PostCompact hook — check, don't assume
src/templates/
  WORK_GOALS.template.md          starter goal files the skill reads —
  PERSONAL_GOALS.template.md        copy out, fill in, make them yours
```

## Requirements

- Claude Code with in-session cron tools (`CronList` / `CronCreate`) available
- Python 3 on PATH (for the two hooks)
- A workspace the agent runs in, where goal files and the skill can live

## Quick start

See `!INSTALL.md`. Short version: copy `SKILL.md` into the agent's skills directory,
copy the two goal templates to the workspace root and fill them in, register the two
hooks in `.claude/settings.json`, then run `/freestyle-beats` in a session.

## Honest limits

- In-session crons are **session-scoped**. Breaks can kill them; 7-day expiry always
  does. The hooks exist to make re-running the skill routine, not to fix persistence —
  nothing here survives the runtime deciding otherwise.
- Fired beats consume context like any other turn. Keep beat prompts short; never
  register a skill invocation as a beat prompt (`SKILL.md` explains the measured cost).
- This package schedules one agent. A multi-agent note in `SKILL.md` covers slot
  spacing and a shared schedule file, but coordination beyond that is out of scope.

## Status

**Stable** — the pattern has run daily in a working multi-agent installation since
May 2026. Extracted and genericized for standalone use 2026-08-13.

Real-world install feedback is welcome in this repository's Issues — that feedback is
how the package gets its human testing.
