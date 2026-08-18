# Freestyle Beats — Technical Decisions

## 2026-08-17 — Package-local personal scheduler

Freestyle Beats ships its own personal scheduler state and lifecycle. The default export
does not depend on an external/shared scheduler or any private schedule artifact.

Canonical state lives at:

```text
<WORKSPACE>/.claude/freestyle-beats/schedule.json
```

The installing workspace therefore contains the exact schedule needed to restore after
session death, a fresh conversation, compaction loss, or seven-day runtime expiry.

## 2026-08-17 — Persisted state is canonical; runtime IDs are not

State preserves stable entry IDs, work/personal labels, exact cron expressions, exact
literal prompts, enabled state, local-time contract, ownership material, and
reconciliation/refresh receipts. Goal files generate only first setup or explicit
replacement. Runtime cron IDs change across restoration and are not persisted as truth.

Writes validate the complete schema before a same-directory atomic replacement. Invalid
state blocks cron mutation instead of triggering generative reconstruction.

## 2026-08-17 — Runtime registry accessed only through supported tools

Claude Code documents that it stores task state under `.claude`, but not a stable file
format/path contract for third-party mutation. Freestyle Beats never reads or edits that
internal file. `CronList`, `CronCreate`, and `CronDelete` are the only live interfaces.

Python hooks cannot call agent tools. They validate state metadata and inject a request;
the installed skill performs tool orchestration.

## 2026-08-17 — Instance-scoped signed ownership markers

Exact matching requires a compact field that survives model-visible `CronList` output.
Each installation generates a random instance ID and ownership key. Runtime prompts
begin with a 61-character HMAC marker over instance, entry token, and canonical payload
digest.

The digest covers the hidden exact cron and full prompt, so the model never reconstructs
them from human-readable schedule text or a truncated preview tail. This prevents public
lookalikes and markers from another installation from being classified as owned. It is a
collision/ownership mechanism, not a security boundary against an actor that can already
read/modify the state file. Normal `show` output redacts the key.

## 2026-08-17 — Complete CronList input and create-first replacement

The planner receives the complete normalized `CronList` result. This enables the
50-task capacity check and prevents model-side prefiltering from becoming the authority
on ownership.

Replacement/refresh creates canonical tasks before deleting old tasks. A second complete
CronList plus `verify-predelete` must observe the required exact-task counts before any
planned delete. If creation reports failure or the observation fails, deliberate deletes
stop. If deletion fails after creation, a duplicate may remain and the next reconcile
removes it. The observation cannot make separate runtime tool calls atomic; final exact
verification remains required. Plans that would exceed the 50-task peak are blocked
without actions rather than falling back to destructive delete-first replacement.

Uninstall uses `uninstall-plan` to classify this instance's signed markers and emit the
only allowed delete IDs. It does not require exposing the ownership key or manually
interpreting public marker text.

## 2026-08-17 — Daily maintenance with five-day age threshold

Recurring Claude Code tasks expire seven days after creation. A day-of-month step such
as `*/5` does not mean every five elapsed days and can cross a month boundary badly.
Maintenance therefore runs daily at `17 4 * * *` (local time, subject to runtime jitter).

`/freestyle-beats maintain` reconciles while the last verified refresh is under five
days old and selects create-first refresh at five days. This preserves margin before
expiry without recreating every task daily. If the session was closed/busy and
maintenance did not run, the next session event requests restore from disk.

## 2026-08-17 — Model-visible CronList preview is the supported input

Live Claude Code 2.1.233 proved the model-facing result contains canonical IDs and
recurring status but human-readable schedule text and prompt previews truncated near 78
characters. The raw stream has full structured fields, but the model cannot use that
out-of-band object. Schema 2 therefore places the entire signed digest marker first,
accepts truncated tails, and rejects a cut/malformed marker. Claude Code 2.1.233 passed
the installed compact-prefix and full reconciliation path on 2026-08-17.

## 2026-08-17 — Self-contained skill installation

Install `SKILL.md` and the complete `src/` tree together. `${CLAUDE_SKILL_DIR}` locates
the bundled scheduler and template; `${CLAUDE_PROJECT_DIR}` locates personal state.
Hooks are registered from the installed skill directory with an absolute Python
interpreter path. This removes the former live dependency on a separate shared package
directory.

## Retained runtime compatibility decisions

### Separate SessionStart and PostCompact entrypoints

SessionStart names the start source; PostCompact states that live cron survival is
indeterminate. Both load the same canonical schedule path.

### PostCompact registration emits `SessionStart` in hook output

Observed 2026-05-31: the runtime validator dropped `additionalContext` when output used
`hookEventName: "PostCompact"`. The registered PostCompact command therefore emits
`hookEventName: "SessionStart"`. Claude Code 2.1.233 revalidated delivery with a real
`/compact` on 2026-08-17.

### Literal prompts for user beats

An ancestor installation measured approximately 11,200 characters attached per skill
invocation; seven daily skill-invocation beats produced approximately 78,000 characters
per day. User beats therefore keep literal task text. The single maintenance task invokes
this skill once per daily check because reconciliation logic is the intended operation.
