# Install — Freestyle Beats

**Placeholders used throughout:**
- `<PACKAGE_ROOT>` — the absolute path where you put this package
  (e.g. `C:\tools\freestyle-beats` or `/opt/agent-tools/freestyle-beats`)
- `<WORKSPACE>` — the directory the agent runs in (where its `.claude/` lives)

## Quick install

1. Copy `SKILL.md` → `<WORKSPACE>/.claude/skills/freestyle-beats/SKILL.md`
2. Copy both files in `src/templates/` → `<WORKSPACE>/WORK_GOALS.md` and
   `<WORKSPACE>/PERSONAL_GOALS.md`, then fill them in
3. Register both hooks in `<WORKSPACE>/.claude/settings.json` (JSON below)
4. In a live session, run `/freestyle-beats`

Details for each step follow; the hook JSON is under *Generated files*.

## Requirements

- Claude Code with in-session cron tools (`CronList` / `CronCreate`) available
- Python 3 (≥3.8) resolvable on the PATH the runtime uses (for the two hooks)
- A workspace the agent runs in, with a `.claude/` directory
- No accounts, no network services, no paid dependencies — nothing beyond the runtime
  you already have. The package costs nothing to run; fired beats consume session
  context like any other turn.

## Package home

```
<PACKAGE_ROOT>/          ← this package, wherever you unpacked it
```

The package directory is never written at runtime, but it stays a **live read
dependency**: the runtime reads both hook scripts from here on every hook fire. The
skill and templates, by contrast, are *copied out* at install and read from their
copies. Keep the package where it is so the hook paths stay valid; move it and you must
update the two hook paths in settings.json.

## Runtime home

```
<WORKSPACE>/.claude/skills/freestyle-beats/SKILL.md    ← the skill the agent runs
<WORKSPACE>/.claude/settings.json                      ← hook registration lives here
```

These instructions choose **project scope** — the skill installs into this one
workspace. Claude Code also supports other skill scopes (e.g. personal skills at
`~/.claude/skills/`, available across all projects); if you want the skill everywhere,
install it there instead and the rest of these steps are unchanged. Either way, updating
the package later means re-copying `SKILL.md` — installed copies do not update themselves.

## Continuity data home

```
<WORKSPACE>/WORK_GOALS.md          ← the agent's own goals; the skill reads these
<WORKSPACE>/PERSONAL_GOALS.md
```

These are the only continuity-bearing files, they belong to the agent, and they are
yours/its to edit at any time. The schedule itself is deliberately NOT persisted —
crons are in-session only, chosen fresh each session (see `!DECISIONS.md` for why).

## Generated files

Everything this package puts anywhere, and who puts it there:

| file | created by | when |
|---|---|---|
| `<WORKSPACE>/.claude/skills/freestyle-beats/SKILL.md` | you | install step 1 |
| `<WORKSPACE>/WORK_GOALS.md`, `PERSONAL_GOALS.md` | you (from templates) | install step 2 |
| two hook entries in `<WORKSPACE>/.claude/settings.json` | you | install step 3 |
| in-session crons | the agent, via `/freestyle-beats` | each session — never on disk |

Nothing else is written anywhere, ever. The hook registration JSON (add to
`settings.json`; **absolute paths required**; on Windows double the backslashes):

```json
"hooks": {
  "SessionStart": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "python \"<PACKAGE_ROOT>/src/hooks/session_start_reminder.py\""
        }
      ]
    }
  ],
  "PostCompact": [
    {
      "matcher": "",
      "hooks": [
        {
          "type": "command",
          "command": "python \"<PACKAGE_ROOT>/src/hooks/post_compact_reminder.py\""
        }
      ]
    }
  ]
}
```

If the agent already has hooks on these events, adding these as additional matcher
entries works — multiple hooks on one event all fire. **But their outputs are blended
together into one context injection, without clear boundaries between them** — several
hooks' reminders arrive as one run-on block the agent has to untangle. **If you
accumulate more than a couple of hooks on the same event, combine them into a single
script that prints one payload with a short header per concern** (e.g. `## Schedule`,
`## Continuity`) — the headers preserve the boundaries the runtime doesn't. Either way,
don't replace existing entries you didn't write.

## Verify

- **New session** → the freestyle-beats reminder appears in the agent's context
- **After compaction** → the check-your-crons reminder appears
- **After running `/freestyle-beats`** → `CronList` shows the day's 2–8 slots

If hooks aren't firing: check `settings.json` parses as valid JSON first — **one bad
comma silently kills the whole hooks block**. Then confirm `python` resolves on the
runtime's PATH, and that both hook paths are absolute and correct.

Full test sequence with expected outputs: `tests/SMOKE_TESTS.md`.

## Uninstall / rollback

Remove, in any order:

- the two hook entries from `<WORKSPACE>/.claude/settings.json`
- `<WORKSPACE>/.claude/skills/freestyle-beats/`
- the goal files, if unwanted: `WORK_GOALS.md`, `PERSONAL_GOALS.md`
- `<PACKAGE_ROOT>/` itself

In-session crons need no cleanup — they die with the session or expire within 7 days.
Rollback after a partial install is the same list; nothing this package does has
side effects beyond the files above.
