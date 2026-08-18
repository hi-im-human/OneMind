# Freestyle Beats — Technical Specification

## Status

**Durability is release-verified in 1.1.0.** Required local/live acceptance, independent
review, sanitization, and link/version gates pass.

## Components

1. **Skill (`SKILL.md`)** — orchestrates setup, reconciliation, refresh, and explicit
   schedule replacement through Claude Code's cron tools.
2. **Scheduler (`src/scheduler.py`)** — validates and atomically writes the canonical
   personal schedule, emits deterministic runtime definitions, plans package-scoped
   deletes/creates, and verifies post-action live state.
3. **Hooks (`src/hooks/`)** — read hook payload `cwd`, validate persisted state, and
   inject a reconciliation request. They do not call agent tools or mutate state.
4. **Inputs/templates (`src/templates/`)** — goal-file examples plus the candidate
   schedule shape used during first setup or explicit replacement.

## Canonical personal state

Default path:

```text
<WORKSPACE>/.claude/freestyle-beats/schedule.json
```

The state is package-owned and workspace-local. An external/shared scheduler is not a
dependency, fallback, or source of truth.

Persisted schema version 2 contains:

```json
{
  "schema_version": 2,
  "instance_id": "<12 lowercase hex characters>",
  "ownership_key": "<64 lowercase hex characters>",
  "timezone": "local",
  "maintenance_cron": "17 4 * * *",
  "created_at": "<UTC timestamp>",
  "updated_at": "<UTC timestamp>",
  "last_reconciled_at": null,
  "last_refreshed_at": null,
  "entries": [
    {
      "id": "morning-work",
      "label": "work",
      "cron": "17 9 * * *",
      "prompt": "<exact literal prompt>",
      "enabled": true
    }
  ]
}
```

Constraints:

- 2–8 user entries;
- stable lowercase-hyphen IDs, unique within the schedule;
- label exactly `work` or `personal`;
- canonical five-field numeric cron syntax supported by Claude Code; fire time remains
  subject to Claude Code jitter;
- `timezone: local`, matching the runtime contract;
- exact literal user prompt, at most 2,000 characters, not a skill invocation;
- duplicate `(cron, prompt)` user entries rejected;
- unknown schema keys rejected;
- timezone-aware UTC metadata with ordered timestamps;
- at least two enabled user beats;
- writes use a same-directory temporary file, flush/fsync, and `os.replace`.

Setup persists state before creating any runtime jobs. A failed runtime call therefore
does not erase the intended schedule. Explicit replacement preserves the original
`created_at` timestamp and resets prior reconciliation/refresh receipts.

## Runtime task identifiers

Each first install generates a random instance ID and ownership key. Every runtime
prompt begins with a 61-character signed marker:

```text
[fb1:<instance-12>:<entry-token-8>:<payload-digest-12>:<signature-20>] <prompt>
```

The token is derived from entry ID + label. The digest covers entry ID, label, kind,
canonical cron, literal prompt, and recurring state. The HMAC authenticates instance +
token + digest. The complete marker fits inside CronList's model-visible prompt preview
even when the remaining prompt is truncated.

The maintenance task uses:

```text
[fb1:<instance-12>:<token-8>:<digest-12>:<signature-20>] Run the /freestyle-beats skill with argument maintain now.
```

Public-prefix lookalikes, bad signatures, and valid markers from another installation
are foreign tasks. A syntactically cut `[fb1:` prefix is a stop condition, not foreign
input. Runtime cron IDs are ephemeral and are not canonical state. `scheduler.py show`
redacts the ownership key; the marker is a collision/ownership guard, not a security
boundary against an actor that can already read and modify canonical state.

## Reconciliation contract

The skill obtains live state only through `CronList`, normalizes the complete task list,
and passes that data to `scheduler.py plan`.

For each enabled canonical task:

- one valid current token + current payload digest + recurring match → keep;
- no current-digest match → create from persisted state;
- multiple exact matches → keep one deterministic ID and delete extras;
- valid current token carries an old digest or is non-recurring → delete drift and
  recreate;
- valid instance marker carries an unknown token → delete the orphan;
- no valid marker for this persisted instance → never delete or rewrite.

Replacement creates execute before deletes. If a create reports failure, the procedure
stops without deliberate deletion. After reported creates, a second complete `CronList`
plus `verify-predelete` must prove every canonical task exists and each planned
replacement increased the exact-task count. Only then are old/drift/duplicate/orphan IDs
deleted. A failed delete can leave a duplicate; the next reconciliation repairs it. The
pre-delete observation narrows but cannot atomically eliminate a runtime race, so final
verification remains mandatory. The planner blocks before mutation if create-first
replacement would exceed Claude Code's 50-task limit. Final `CronList` plus
`scheduler.py verify` must show exactly one canonical task per enabled beat plus one
maintenance task before the run records success.

## Seven-day refresh contract

Claude Code recurring tasks expire seven days after creation. Freestyle Beats includes
one daily maintenance task using `17 4 * * *`. The maintenance prompt instructs the
agent to run `/freestyle-beats maintain`. The CLI chooses ordinary reconciliation until the last
verified refresh is five days old, then chooses create-first refresh, leaving margin for
runtime jitter before expiry. Refresh:

1. loads persisted state;
2. lists live jobs;
3. creates a replacement for every enabled beat and the maintenance job;
4. re-lists and verifies required exact replacement counts;
5. deletes prior instance-owned IDs only after that observation passes; and
6. verifies the exact result and records `last_refreshed_at`.

This resets runtime creation age before expiry while a session is open and able to run
scheduled prompts. If the session was closed or never idle, SessionStart/PostCompact
requests ordinary reconciliation on return. The schedule file survives both cases.

## Hook contract

Every Claude Code hook event supplies `cwd`; the CLI also accepts
`CLAUDE_PROJECT_DIR`. Package cwd is never used as a silent workspace fallback.

Each hook prints one JSON object:

```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<text>"}}
```

The PostCompact registration deliberately emits `hookEventName: "SessionStart"` in its
output because the last recorded runtime validation dropped literal `PostCompact`
`additionalContext`. The registered event remains PostCompact.

Missing state asks for setup. Valid state reports its path, enabled count, and compact
fingerprint, then requests reconciliation. Invalid state emits a visible error and tells
the agent not to mutate cron jobs.

## Runtime boundaries

- Hooks and Python commands cannot call `CronList`, `CronDelete`, or `CronCreate`; the
  Claude agent performs those tool calls.
- Live reconciliation uses CronList's model-visible ID, recurring indicator, and prompt
  prefix. Human-readable schedule text and truncated prompt tails are not reconstructed.
  The complete signed prefix must be visible; a cut marker is a stop condition.
- The package does not read or edit Claude Code's undocumented task-storage file.
- Tasks fire only while Claude Code is open and idle; missed fires do not catch up.
- A session can hold at most 50 scheduled tasks. This package uses enabled beats + one
  maintenance task (maximum nine).
- Fired user prompts include a compact ownership marker. Daily maintenance loads this
  skill once per maintenance fire, whether it selects reconcile or refresh.

## Uninstall classification

`scheduler.py uninstall-plan --live <complete-list>` verifies this instance's signed
markers and returns only its runtime IDs as delete actions. Uninstall does not manually
inspect/redact keys or infer ownership from the public prefix. The plan is read-only;
the Claude agent executes its listed `CronDelete` calls, re-lists, and confirms zero
remaining current-instance tasks before removing state.

## Failure modes

| failure | effect | handling |
|---|---|---|
| schedule missing | no canonical schedule | hook requests `setup`; no cron mutation |
| schedule malformed/unsupported | canonical state unavailable | visible hook/CLI error; stop all cron mutation |
| goal files missing during setup | cannot select initial entries | stop and report exact path |
| CronList truncates after complete marker | digest still identifies exact canonical payload | preserve visible prefix verbatim and reconcile |
| CronList cuts/malforms marker itself | ownership/content unavailable | stop without mutation |
| create-first plan exceeds 50-task cap | safe replacement unavailable | block with no actions |
| create reports failure | replacement incomplete | stop before deliberate deletes; re-list to determine actual live state |
| post-create observation fails | replacement not proved live | stop before deletes; final state remains unclaimed |
| delete fails after creates | duplicate may remain | persisted state + next reconcile removes extras |
| verification fails | live state differs from canonical | nonzero result; no success receipt |
| maintenance cannot fire while closed/busy | runtime jobs may expire | persisted schedule remains; next session event requests reconcile |
| malformed settings JSON / missing Python | hooks do not run | install-time live hook verification required |
| public marker spoof / another install | could resemble package text | random instance + HMAC verification classifies it as foreign |

## Not implemented

- shared/family scheduling or cross-agent coordination;
- unattended scheduling while Claude Code is closed;
- editing Claude Code's internal task files;
- automatic migration from an external/private scheduler.
