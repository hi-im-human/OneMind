---
name: freestyle-beats
description: Create, persist, reconcile, and pre-expiry refresh 2–8 personal Claude Code cron prompts from one workspace-local schedule.
argument-hint: setup | reconcile | maintain | refresh | replace
---

# Freestyle Beats

Freestyle Beats keeps one canonical personal schedule at:

```text
${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/schedule.json
```

The schedule file—not goal files, conversation context, or runtime cron IDs—is the
source of truth after setup. Runtime prompts begin with a compact signed marker that fits
inside CronList's model-visible prompt preview. The marker carries a digest of the exact
canonical cron, prompt, label, and kind, so reconciliation does not reconstruct hidden
prompt text or human-readable schedules.

## Choose the mode

- `setup` — create the first persisted schedule. Use only when no schedule exists.
- `reconcile` (default) — restore missing jobs, remove exact package duplicates,
  replace drifted package jobs, and leave unrelated jobs untouched.
- `maintain` — daily maintenance entrypoint. Run `scheduler.py ... maintain`; use the
  returned mode (`reconcile` or `refresh`) for this invocation.
- `refresh` — create replacement jobs first, then delete prior package-owned jobs. The
  maintenance path chooses this when the last verified refresh is five days old.
- `replace` — explicitly replace the persisted schedule, then reconcile it. Never
  replace state merely because live jobs are absent.

## 1. Load or create canonical state

Run:

```text
python "${CLAUDE_SKILL_DIR}/src/scheduler.py" --workspace "${CLAUDE_PROJECT_DIR}" validate
```

### If state validates

Do not read goal files to reconstruct it. Continue to reconciliation.

If invoked as `maintain`, run:

```text
python "${CLAUDE_SKILL_DIR}/src/scheduler.py" --workspace "${CLAUDE_PROJECT_DIR}" maintain
```

Use the returned `mode` for the rest of this invocation. Add `--refresh` to the plan only
when the returned mode is `refresh`.

### If state is missing and mode is `setup`

1. Read `${CLAUDE_PROJECT_DIR}/WORK_GOALS.md` and
   `${CLAUDE_PROJECT_DIR}/PERSONAL_GOALS.md`. Stop and report the missing path if
   either is unavailable.
2. Select **2–8 user beats once**. Each needs:
   - a stable lowercase-hyphen `id`;
   - label `work` or `personal`;
   - a canonical five-field cron expression interpreted in local time and subject to
     Claude Code's runtime jitter; and
   - short literal prompt text. A user beat prompt must not be a skill invocation.
3. Copy `${CLAUDE_SKILL_DIR}/src/templates/SCHEDULE.template.json` to
   `${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/candidate.json` and replace the
   examples with the selected entries. Keep `timezone` equal to `local`.
4. Persist before calling any cron tool:

```text
python "${CLAUDE_SKILL_DIR}/src/scheduler.py" --workspace "${CLAUDE_PROJECT_DIR}" create --input "${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/candidate.json"
```

5. Delete `candidate.json` only after the command succeeds. Continue with
   `reconcile` using the just-written state.

If state exists, `setup` must stop rather than overwrite it. Use `replace` only when a
schedule change was explicitly requested; pass `create --replace` after preparing and
reviewing the complete candidate.

## 2. Produce a deterministic reconciliation plan

1. Run `scheduler.py ... show`. This returns the canonical state and the exact
   tool-ready runtime tasks, including compact prefix markers.
2. Call `CronList`.
3. Use the complete model-visible list. CronList may show human-readable schedules and
   truncated prompt previews; that is expected. For each line, preserve the exact
   eight-character ID, whether it says recurring, and the verbatim visible prompt
   preview after the colon. Do not convert display schedules back into cron expressions
   and do not reconstruct truncated prompt tails.
4. Write the complete `CronList` result to:

```text
${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/live-crons.json
```

Use this normalized shape:

```json
{
  "tasks": [
    {"id": "1234abcd", "prompt": "[fb1:<complete marker>] <visible preview>…", "recurring": true}
  ]
}
```

This temporary contains the complete authoritative list because capacity checks and
ownership classification must not depend on model-side filtering. Delete it after
verification. A valid current-instance marker is fully visible before any truncated
tail. If a marker itself is cut or malformed, it is foreign and must never authorize a
delete. Public-prefix lookalikes and markers from another installation are foreign.

5. Generate the plan:

```text
python "${CLAUDE_SKILL_DIR}/src/scheduler.py" --workspace "${CLAUDE_PROJECT_DIR}" plan --live "${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/live-crons.json" --output "${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/plan.json"
```

For `refresh`, add `--refresh`.

If the plan returns `"blocked": true` or `"ok": false`, stop without cron mutations.
Create-first replacement would exceed Claude Code's 50-task cap; remove unrelated tasks
only by their owner's procedure or reduce this schedule before retrying.

## 3. Apply the plan through Claude Code tools

1. Execute every `create` action with `CronCreate`, passing its exact `cron`, full
   `prompt`, and `recurring: true` values. Do not rewrite prompts or markers.
2. If any create reports failure, stop before deletes. Existing tasks have not been
   deliberately deleted by this procedure.
3. Call `CronList` again and write the complete model-visible ID/prompt-preview/recurring
   result to
   `${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/after-create.json`.
4. Verify the replacements are actually visible before deleting anything:

```text
python "${CLAUDE_SKILL_DIR}/src/scheduler.py" --workspace "${CLAUDE_PROJECT_DIR}" verify-predelete --live "${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/after-create.json" --plan "${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/plan.json"
```

5. If this returns nonzero or `"ok": false`, stop before deletes. A reported create is
   not treated as durable until the re-list proves the required exact task count.
6. Only after that PASS, execute every planned `delete` with `CronDelete`, passing its
   returned `cron_id` value as the tool's `id` input. A failed delete may leave a
   duplicate; report and reconcile again.
7. Do not delete a task unless the saved scheduler plan classified its instance-scoped,
   signed marker as owned. Same time with a different prompt is not a duplicate.

The pre-delete check narrows the create/delete gap; it is not an atomic runtime
transaction. Final verification remains required because a task could change after the
pre-delete re-list.

## 4. Verify and record

1. Call `CronList` again.
2. Rewrite `live-crons.json` with the complete model-visible normalized result.
3. Run:

```text
python "${CLAUDE_SKILL_DIR}/src/scheduler.py" --workspace "${CLAUDE_PROJECT_DIR}" verify --live "${CLAUDE_PROJECT_DIR}/.claude/freestyle-beats/live-crons.json" --record-mode reconcile
```

Use `--record-mode refresh` after refresh **and after first setup**, because setup created
the full runtime set at that time. A nonzero exit or `"ok": false` is a failure; report
the listed problem rather than claiming restoration.

4. Delete `live-crons.json`, `after-create.json`, and `plan.json` after verification.
5. Report the schedule fingerprint, kept tasks, deletes, creates, and final verified
count.

## Maintenance and runtime limits

- The scheduler adds one daily package-owned maintenance task. Its default cron,
  `17 4 * * *`, carries a literal instruction to run `/freestyle-beats maintain`; the
  compact ownership marker remains the visible prompt prefix. The maintain command
  reconciles on ordinary days and chooses a create-first refresh once the last verified
  refresh is five days old, leaving margin before seven-day expiry and runtime jitter.
- The maintenance fire loads this skill once. User beats always store literal prompt
  text; they never invoke skills.
- Tasks run only while Claude Code is open and idle. There is no catch-up for missed
  fires. If the maintenance task did not fire, the next SessionStart/PostCompact hook
  requests reconciliation from the persisted schedule.
- Fresh conversations clear session-scoped jobs. `--resume`/`--continue` only restore
  unexpired jobs. Neither behavior changes the canonical schedule file.
- This package never reads or edits Claude Code's internal task-storage file. All live
  state comes from `CronList`; all mutations use `CronDelete` and `CronCreate`.
- A malformed canonical schedule is a stop condition. Do not generate replacement
  state from goal files unless setup/replace was explicitly requested.
