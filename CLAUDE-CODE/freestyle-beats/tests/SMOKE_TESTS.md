# Freestyle Beats — Smoke Tests

Run these after install (`!INSTALL.md`) in the order given. Each test names its expected
output; a test whose expectation you didn't observe is a FAIL even if nothing errored.

## 1. Hook syntax + output contract (no runtime needed)

```
python "<PACKAGE_ROOT>/src/hooks/session_start_reminder.py" < /dev/null
python "<PACKAGE_ROOT>/src/hooks/post_compact_reminder.py"  < /dev/null
```
*(Windows: pipe from `NUL` or just press Ctrl+Z then Enter at the waiting prompt.)*

**Expect:** each prints exactly one line of JSON containing
`"hookEventName": "SessionStart"` and a non-empty `"additionalContext"`.
**FAIL if:** any traceback, or the PostCompact hook emits `"PostCompact"` as its event
name (that payload gets dropped by the runtime — see `!DECISIONS.md`).

## 2. Settings registration is intact

Open `<WORKSPACE>/.claude/settings.json` and confirm it parses as JSON (paste into any
JSON validator if unsure).

**Expect:** valid JSON; both hook entries present with absolute paths.
**FAIL if:** parse error — one bad comma disables ALL hooks silently (`!BUGS.md`).

## 3. SessionStart reminder arrives

Start a fresh Claude Code session in the workspace.

**Expect:** the agent's context contains the freestyle-beats reminder — anchor on
*"Check your beats (`/freestyle-beats`) before beginning unrelated work"* — AND the
live-condition override is present (*"pause/hold outranks this"*). Both anchors matter:
the second is the repaired behavior, and its absence means an old hook version is firing.
**FAIL if:** no reminder — check test 2, then that `python` resolves on the runtime's
PATH, then the hook paths. **Also FAIL if** the reminder appears but says "BEFORE
resuming whatever conversation" or "Do NOT message your human" — that's a stale hook.

## 4. Skill runs and registers beats

In the session, run `/freestyle-beats`. Then call `CronList`.

**Expect:** the agent reads `WORK_GOALS.md` / `PERSONAL_GOALS.md`, announces 2–8 slots,
and `CronList` shows them.
**FAIL if:** the skill can't find the goal files (install step 2 skipped) or no crons
appear.

## 5. Idempotency

Run `/freestyle-beats` again immediately.

**Expect:** no duplicate crons — the skill reports the schedule already in place.
`CronList` count unchanged.
**FAIL if:** the slot count doubled.

## 6. A beat actually fires

Register one test slot 2–3 minutes in the future (the skill can do this as a one-off),
then wait with the session idle.

**Expect:** at the scheduled time, the prompt arrives in the session as the agent's own
turn and the agent acts on it.
**FAIL if:** nothing fires — note that crons only fire while the session is idle, and
one-shot timing can slip by a minute or two.

## 7. Uninstall leaves nothing

Follow `!INSTALL.md` uninstall, then start a fresh session.

**Expect:** no reminder appears; `/freestyle-beats` is unavailable; no package files
remain in the workspace beyond the goal files if you chose to keep them.

---

## Record of runs

| date | environment | tester (agent/human) | 1 | 2 | 3 | 4 | 5 | 6 | 7 | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-08-13 | Windows, Python 3.11.9, Claude Code v2.1.231, project-scope | agent | PASS | PASS | PASS | PASS | PASS | PASS | PASS | Independent stateless agent; no source-household knowledge; ~16 min hands-on. Test 3: live SessionStart had corrected wording (both anchors present, stale phrases absent). Test 4: 5 slots created (3 work, 2 personal). Test 5: second invocation created 0 duplicates. Test 6: real beat fired at scheduled time. Test 7: uninstall removed all package-specific installed content. |
