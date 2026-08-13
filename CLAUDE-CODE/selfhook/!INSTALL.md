# Install — Selfhook

**Placeholders:**
- `<PACKAGE_ROOT>` — absolute path where you put this package
- `<WORKSPACE>` — the directory the agent runs in (where its `.claude/` lives)

## Quick install

1. Copy `config/continuity.example.json` → `config/continuity.json`; set `workspace`
   to an **absolute** path and edit sections, file lists, and caps to match your
   continuity layout (all paths workspace-relative — the hook rejects escapes)
2. Register the hook under **both** SessionStart and PostCompact in
   `<WORKSPACE>/.claude/settings.json` (JSON under *Generated files*)
3. Wire `src/check_limits.py` into your pre-commit hook or sync script
4. Start a session — the banner should arrive

## Requirements

- Claude Code runtime with hooks support
- Python 3 (≥3.8) resolvable on the PATH the runtime uses
- No accounts, no network services, no paid dependencies. The hook adds a small
  context payload (bounded at 1,800 chars) per session start/compaction.

## Package home

```
<PACKAGE_ROOT>/
```

Never written at runtime, but a **live read dependency**: the runtime reads
`src/selfhook.py` on every hook fire, and `check_limits.py` imports from it. The
config also lives here. Move the package and you must update the paths in
`settings.json` and your pre-commit wiring.

## Runtime home

```
<WORKSPACE>/.claude/settings.json     ← two hook registrations (edited by you)
```

Nothing else is installed into the workspace. The hook *reads* your continuity files
where they already live; it puts nothing there.

## Continuity data home

Wherever your config points. The example uses:

```
<WORKSPACE>/.memory/identity/*.md     ← identity/user/relationship/principles notes
<WORKSPACE>/.brain/SESSION_TALE.md    ← optional pre-compaction tail, if your setup writes one
<WORKSPACE>/.brain/GROWTH.md          ← optional capped journal
```

All of it is yours/the agent's; this package only lists and caps what you tell it to.

## Generated files

| file | created by | when |
|---|---|---|
| `<PACKAGE_ROOT>/config/continuity.json` | you (from the example) | install step 1 |
| two hook entries in `<WORKSPACE>/.claude/settings.json` | you | install step 2 |
| a call to `check_limits.py` in your pre-commit/sync | you | install step 3 |

Nothing else is written anywhere, ever — the hook's only output is its in-session
payload. Hook registration JSON (absolute paths; Windows doubles backslashes):

```json
"hooks": {
  "SessionStart": [
    { "matcher": "", "hooks": [ { "type": "command",
      "command": "python \"<PACKAGE_ROOT>/src/selfhook.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --event SessionStart" } ] }
  ],
  "PostCompact": [
    { "matcher": "", "hooks": [ { "type": "command",
      "command": "python \"<PACKAGE_ROOT>/src/selfhook.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --event PostCompact" } ] }
  ]
}
```

**If other tools already register hooks on these events:** their output and Selfhook's
will be blended into one context injection without boundaries. That is the problem
this package exists to solve — prefer moving their message into a Selfhook *section*
(one config entry) and removing their separate registration.

## Verify

- **Launch from inside the workspace** — hooks load from the settings of the
  directory the session starts in, so the launch directory is part of the test:

  ```
  cd <WORKSPACE>          # PowerShell: Push-Location "<WORKSPACE>"
  claude
  ```

  New session → the banner block (`===== ... =====`) appears with your file list
- After compaction → the same, plus any PostCompact-only sections
- ⚠️ **A no-banner verdict is only valid with a cwd receipt.** Confirm from the
  session's own record (the runtime's init/persisted `cwd`) that the session
  actually started in `<WORKSPACE>` — not from where you *intended* to launch. A
  session started elsewhere reads a different `settings.json` and shows nothing,
  which is indistinguishable from a broken hook. Self-report is not evidence;
  the persisted session record is. **The executable receipt path is smoke test 6**
  (`tests/SMOKE_TESTS.md`): one headless command whose stream output contains both
  `init.cwd` and the `hook_response`.
- `python src/check_limits.py --config config/continuity.json --workspace <WORKSPACE>`
  exits 0 while files are within caps; over-fill a capped file and it exits 1, loudly

Full sequence with expected outputs: `tests/SMOKE_TESTS.md`.

## Uninstall / rollback

Remove **in this order** — the settings registrations are live consumers of the
package scripts, and deleting the package first leaves broken hooks failing
invisibly at every session start:

1. the two hook entries from `<WORKSPACE>/.claude/settings.json`
2. the `check_limits.py` call from your pre-commit/sync
3. `<PACKAGE_ROOT>/`

Your continuity files are untouched — they were never this package's to manage.
