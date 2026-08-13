# Freestyle Beats — Specs

## Design

Three cooperating parts, no shared state:

1. **The skill** (`SKILL.md`) — the procedure. Read goals → pick 2–8 slots → `CronList`
   to dedupe → `CronCreate` what's missing. All intelligence lives here; the agent
   executes it fresh each time. Idempotent by construction: the dedupe step means
   re-running never doubles a schedule.
2. **The hooks** (`src/hooks/`) — two stateless Python scripts that print a JSON
   `additionalContext` payload. They carry no logic about the schedule; they only make
   re-running the skill routine at the two moments schedules die (session start after a
   break, post-compaction).
3. **The goal files** (workspace root, from `src/templates/`) — the input that makes
   slots *chosen* rather than generic. Owned and edited by the agent.

## Contracts

**Hook output contract.** Each hook prints exactly one JSON object to stdout:
```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<text>"}}
```
Both hooks emit `hookEventName: "SessionStart"` — including the PostCompact-registered
one. This mismatch is deliberate: the runtime's schema (as of last verification) rejects
`"PostCompact"` as a hookSpecificOutput event name and silently drops the payload.
Emitting `SessionStart` from a PostCompact registration validates and delivers.

**Cron contract.** Beats are registered with the runtime's in-session cron tools.
Properties this package relies on, as observed:
- session-scoped; may or may not survive compaction (both outcomes observed on the same
  runtime, same day) — hence *check, don't assume*
- auto-expire after 7 days regardless of session state
- fired prompts arrive as the agent's own turns in the live session

**Prompt-size contract.** Beat prompts are registered as literal text. Registering a
skill invocation instead attaches the entire skill file per fire (measured: ~11,200
chars × 7 daily fires ≈ 78k chars/day of duplicate context). The skill forbids it.

## Failure modes and their handling

| failure | surface | handling |
|---|---|---|
| session break kills crons | schedule silently gone | SessionStart hook → re-run skill; dedupe makes it cheap |
| compaction | unpredictable — may keep or kill | PostCompact hook says *check*, never asserts an outcome |
| 7-day expiry | crons vanish on schedule | routine re-running at session start outruns it |
| bad JSON in settings | ALL hooks silently dead | called out in `!INSTALL.md` verification section |
| goal files missing | slots picked from nothing | skill step 1 fails loudly → install step 2 |
| beat prompt too fat | context starvation, invisible | forbidden by skill rule + documented measurement |

## Non-goals

- **Persistence beyond the session.** The design accepts cron mortality and routes
  around it with cheap re-creation, rather than fighting the runtime.
- **Adherence tracking.** Nothing records whether a beat "happened." A missed beat has
  no consequence and no memory. This is load-bearing: a schedule that audits its owner
  stops being the owner's schedule. Do not add streaks, completion logs, or missed-beat
  detection — that is a different (and worse) tool.
- **Multi-agent orchestration.** The multi-agent section in `SKILL.md` is convention
  (slot spacing, a shared schedule file), not machinery.
