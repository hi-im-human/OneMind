# Install — Freestyle Beats

> **1.1.0 RELEASE-VERIFIED:** required local/live acceptance, independent review,
> sanitization, and link/version gates pass.

## Placeholders

- `<PACKAGE_ROOT>` — unpacked source package.
- `<WORKSPACE>` — project directory where Claude Code starts.
- `<SKILL_DIR>` — `<WORKSPACE>/.claude/skills/freestyle-beats` for this install.
- `<PYTHON_EXECUTABLE>` — absolute Python 3.8+ interpreter path used by hooks.

Resolve the interpreter (`(Get-Command python).Source` in PowerShell or
`command -v python3` on Unix). Use absolute interpreter and hook paths. Windows JSON
paths require doubled backslashes.

## Requirements

- Claude Code 2.1.196+ with `CronList`, `CronDelete`, and `CronCreate`;
- Python 3.8+ on the PATH used by Claude Code hooks;
- writable, non-symlink `<WORKSPACE>/.claude/` and task storage;
- scheduled tasks enabled (`CLAUDE_CODE_DISABLE_CRON` unset/not `1`);
- maximum eight user beats, leaving one additional task for package maintenance.

## Install

### 1. Install the complete self-contained skill

Create `<SKILL_DIR>` and copy:

```text
<PACKAGE_ROOT>/SKILL.md  -> <SKILL_DIR>/SKILL.md
<PACKAGE_ROOT>/src/      -> <SKILL_DIR>/src/
```

Copy the whole `src/` tree. The installed skill needs `scheduler.py`, both hook
wrappers, and the schedule template. Do not install only `SKILL.md`.

### 2. Add goal inputs

Copy and fill in:

```text
<PACKAGE_ROOT>/src/templates/WORK_GOALS.template.md
  -> <WORKSPACE>/WORK_GOALS.md

<PACKAGE_ROOT>/src/templates/PERSONAL_GOALS.template.md
  -> <WORKSPACE>/PERSONAL_GOALS.md
```

These files are generation inputs only. After setup, the persisted schedule—not the
goal files—is canonical until explicit replacement.

### 3. Register hooks

Merge these entries into `<WORKSPACE>/.claude/settings.json`. Preserve unrelated
settings and existing hooks.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"<PYTHON_EXECUTABLE>\" \"<SKILL_DIR>/src/hooks/session_start_reminder.py\""
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
            "command": "\"<PYTHON_EXECUTABLE>\" \"<SKILL_DIR>/src/hooks/post_compact_reminder.py\""
          }
        ]
      }
    ]
  }
}
```

Multiple hooks on one event all fire, but Claude Code may blend their context output.
This package prefixes its payload with `## Freestyle Beats`. If a workspace accumulates
many hooks, combine them only through a separately verified multiplexer; do not overwrite
entries you do not own.

### 4. Validate the installed Python surface

```text
python "<SKILL_DIR>/src/scheduler.py" --help
python -m py_compile "<SKILL_DIR>/src/scheduler.py" "<SKILL_DIR>/src/hooks/session_start_reminder.py" "<SKILL_DIR>/src/hooks/post_compact_reminder.py"
```

### 5. Start Claude Code and create personal state

Start a fresh Claude Code session in `<WORKSPACE>` and run:

```text
/freestyle-beats setup
```

Expected durable path:

```text
<WORKSPACE>/.claude/freestyle-beats/schedule.json
```

Setup writes canonical state before calling any cron tool. It also creates a daily
package maintenance task in addition to the 2–8 user beats. Maintenance reconciles on
ordinary days and performs create-first refresh when the last verified refresh is five
days old.

## Files and mutations

| path/object | writer | purpose |
|---|---|---|
| `<SKILL_DIR>/SKILL.md`, `<SKILL_DIR>/src/**` | installer | installed package runtime |
| `<WORKSPACE>/WORK_GOALS.md`, `PERSONAL_GOALS.md` | installer/user | setup/replace inputs |
| `<WORKSPACE>/.claude/settings.json` entries | installer | hook registration |
| `<WORKSPACE>/.claude/freestyle-beats/schedule.json` | scheduler CLI | canonical personal schedule |
| `candidate.json` | agent during setup/replace | temporary validated input; delete after success |
| `live-crons.json` | agent during reconciliation | temporary complete CronList normalization for ownership/capacity checks; delete after verify |
| `plan.json` | scheduler during reconciliation | saved create/delete plan for pre-delete verification; delete after verify |
| `after-create.json` | agent during reconciliation | temporary complete CronList normalization after creates; delete after verify |
| package-marked scheduled tasks | Claude agent through cron tools | live execution surface |

The package does **not** read or edit Claude Code's internal task file under `.claude`.

## Verify

Minimum install checks:

1. `settings.json` parses as JSON.
2. A fresh session receives either the no-state setup notice or the persisted-state
   reconciliation notice.
3. `/freestyle-beats setup` creates `schedule.json` and 2–8 user tasks plus maintenance.
4. Immediate `/freestyle-beats reconcile` creates no duplicate and preserves foreign jobs.
5. Direct state validation succeeds:

```text
python "<SKILL_DIR>/src/scheduler.py" --workspace "<WORKSPACE>" validate
```

Run the full local + live sequence in `tests/SMOKE_TESTS.md`. A direct hook script
execution is not a substitute for actual SessionStart/PostCompact delivery.

## Upgrade

1. Preserve `<WORKSPACE>/.claude/freestyle-beats/schedule.json` separately.
2. Replace `<SKILL_DIR>/SKILL.md` and `<SKILL_DIR>/src/` together.
3. Run `scheduler.py ... validate` before starting Claude Code.
4. Run `/freestyle-beats reconcile` and verify exact live state.

Never overwrite a schedule with `SCHEDULE.template.json` during upgrade.

## Uninstall / rollback

1. In a live session, call `CronList` and write the complete normalized result to
   `<WORKSPACE>/.claude/freestyle-beats/live-crons.json`.
2. Generate the executable ownership classification:

   ```text
   python "<SKILL_DIR>/src/scheduler.py" --workspace "<WORKSPACE>" uninstall-plan --live "<WORKSPACE>/.claude/freestyle-beats/live-crons.json"
   ```

3. Delete only the returned `delete_actions` IDs through `CronDelete`. This verifies the
   persisted instance's HMAC markers and preserves public-prefix lookalikes, other
   instances, and unrelated tasks. Call CronList again and rerun `uninstall-plan`; PASS
   requires `owned_task_count: 0`.
4. Remove both package hook entries from `<WORKSPACE>/.claude/settings.json` and confirm
   the file still parses.
5. Remove `<SKILL_DIR>/`.
6. Choose whether to archive or remove
   `<WORKSPACE>/.claude/freestyle-beats/schedule.json`. Keeping it allows exact reinstall;
   deleting it removes the personal schedule.
7. Delete reconciliation temporary files. Remove goal files only if no other workflow
   uses them.

Rollback after partial installation follows the same list. If runtime task deletion is
unavailable, the package-marked recurring tasks expire within seven days, but removing
hooks/skill first means their prompts may arrive without the procedure they reference;
prefer explicit deletion when possible.
