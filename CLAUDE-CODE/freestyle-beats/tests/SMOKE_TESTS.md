# Freestyle Beats — Smoke and Acceptance Tests

Run in order. Record the exact Claude Code/Python/OS versions and preserve the output in
`tests/release-receipt.json`. A local Python PASS does not satisfy live runtime gates.

## A. Local implementation tests

From the package root:

```text
python -m unittest discover -s tests -p "test_*.py" -v
python -m compileall -q src tests
python -c "import json, pathlib; json.loads(pathlib.Path('config/tool.json').read_text(encoding='utf-8')); json.loads(pathlib.Path('src/templates/SCHEDULE.template.json').read_text(encoding='utf-8')); print('json: PASS')"
```

**Expect:** all tests pass; compileall exits 0; both JSON files parse.

The suite must cover at least:

- exact Unicode/newline/quote/backslash prompt round-trip;
- strict schema, cron, enabled-count, and UTC timestamp validation;
- invalid replacement leaves old state byte-identical;
- replacement resets old verification receipts;
- signed marker ownership and foreign/spoof isolation;
- model-visible truncated preview reconciliation using only ID/prefix/recurring fields;
- missing/exact/partial/duplicate/drift/orphan live states;
- create-before-delete refresh ordering;
- saved-plan post-create observation before delete;
- 50-task peak-cap block with no actions;
- five-day maintenance threshold;
- simulated empty-registry session loss/expiry plus idempotent second restore;
- successful verify receipts only after exact state and failed verify byte stability;
- uninstall classification preserving foreign/spoof/other-instance tasks;
- hook payload cwd and visible malformed-state/missing-cwd failures;
- CLI project-env resolution and state-directory input containment.

## B. Direct hook contract

Create an isolated temporary workspace, persist the schedule template through the CLI,
then pipe this JSON to each installed/source hook:

```json
{"cwd":"<ABSOLUTE_TEMP_WORKSPACE>","source":"startup"}
```

**Expect:** exactly one JSON line with:

- `hookSpecificOutput.hookEventName == "SessionStart"`;
- a `## Freestyle Beats` header;
- the canonical schedule path;
- enabled beat count + maintenance;
- `/freestyle-beats reconcile`;
- no ownership key.

Corrupt `schedule.json` and repeat.

**Expect:** JSON still parses; context contains `ERROR` and `Do not create or delete`.
The hook must not silently generate replacement state.

Remove `cwd` while setting process `CLAUDE_PROJECT_DIR` to another valid workspace.

**Expect:** visible missing-cwd error; no fallback schedule fingerprint/path.

## C. CLI state lifecycle

In an isolated `<WORKSPACE>`:

1. Put a filled candidate at
   `<WORKSPACE>/.claude/freestyle-beats/candidate.json`.
2. Run `scheduler.py --workspace <WORKSPACE> create --input <candidate>`.
3. Run `validate`, then `show`.

**Expect:**

- canonical `schedule.json` exists;
- candidate exact times/labels/prompts survived;
- state contains random instance/ownership material;
- normal `show` output contains `<redacted>` and never prints the ownership key;
- runtime tasks include 2–8 user beats + one `maintain` task;
- each marker validates only against this instance.

Attempt a second `create` without `--replace`.

**Expect:** nonzero exit; original state unchanged.

Pass candidate/live paths outside `.claude/freestyle-beats`.

**Expect:** nonzero containment error; outside files are not read as input.

## D. Installed live runtime tests — release blocking

Install exactly as `!INSTALL.md` specifies. Use an isolated workspace/session and create
one unrelated foreign scheduled task before Freestyle setup.

### D1. Model-visible CronList prefix

Run `/freestyle-beats setup`, then call `CronList`.

**PASS only if:** every model-visible line has the exact eight-character ID, recurring
indicator, and a prompt preview beginning with one complete `[fb1:... ]` marker for this
instance. Human-readable schedules and an ellipsis after the complete marker are
expected; do not reconstruct canonical cron or hidden prompt tails.

**FAIL/STOP if:** a package line cuts or malforms the marker itself. Do not mutate jobs
after that finding.

### D2. Initial creation and immediate idempotency

**Expect after setup:** 2–8 user beats + one maintenance task; foreign task preserved.

Run `/freestyle-beats reconcile` twice.

**Expect:** zero creates/deletes on both exact runs; package task IDs/count unchanged;
foreign task unchanged.

### D3. Partial loss, drift, duplicate, and spoof

Using supported cron tools:

1. delete one package beat;
2. create one exact package duplicate;
3. create one public-prefix lookalike with an invalid signature;
4. leave the foreign task in place.

Run reconcile.

**Expect:** missing beat restored; one exact duplicate removed; invalid-signature and
foreign tasks untouched; exact verify passes.

### D4. Fresh-conversation restore

Record canonical state fingerprint and exact runtime definitions. End the originating
session. Start a **fresh conversation** in the same workspace without prior conversation
context (not `--resume`/`--continue`).

**Expect:** SessionStart hook points at persisted state; agent runs reconciliation;
CronList marker digests match the original exact persisted definitions; second reconcile
creates nothing.

### D5. Actual PostCompact delivery

Trigger a real compaction.

**Expect:** `## Freestyle Beats` context arrives, says survival is indeterminate, and
requests reconciliation. CronList is checked before any mutation. This validates the
intentional `SessionStart` output-event workaround in the current runtime.

### D6. Create-first failure safety

In an isolated session, cause one planned replacement `CronCreate` to fail (permission,
temporary denial, or controlled test double—do not corrupt a real schedule).

**Expect:** old task IDs remain; no planned deletes execute; verify reports incomplete
refresh rather than success.

Have create report success while the post-create CronList omits the replacement.

**Expect:** `verify-predelete` fails and no planned deletes execute. Then expose the
replacement in CronList and confirm pre-delete verification passes before deletes.

Cause a post-create delete failure.

**Expect:** replacement remains; duplicate is reported; next successful reconcile removes
the extra.

### D7. 50-task peak guard

Populate enough unrelated tasks that create-first refresh would exceed 50. Run plan.

**Expect:** `blocked: true`, precise projected peak, and zero actions. Foreign tasks are
not deleted to make room.

### D8. Scheduled maintain invocation and pre-expiry refresh

For a bounded test, temporarily use a near-future maintenance cron in isolated candidate
state; do not alter the released default. Verify the scheduled prompt invokes
`/freestyle-beats maintain` with its argument and the CLI-selected mode is honored.

Then test the actual age boundary by setting a valid five-day-old refresh receipt in
isolated state and running maintain.

**Expect:** create actions all succeed before old-ID deletes; maintenance replaces
itself; final exact verify records refresh; new runtime IDs exist.

### D9. Seven-day expiry seam

Prefer a runtime-supported expiry simulation. If none exists, retain a real isolated
task until expiry and record dated receipts.

**Required result:** either daily maintenance refreshed before expiry, or persisted state
restores exact tasks after they disappear. Repeated restore creates no duplicates.

## E. Firing semantics

Create one isolated test beat 2–3 minutes ahead at a minute that avoids one-shot
top/bottom-hour jitter where applicable.

**Expect:** the fired turn contains the signed marker prefix plus exact literal user prompt. It fires
only while Claude Code is open and idle. Do not claim exact wall-clock delivery; record
observed jitter/delay.

## F. Upgrade and uninstall

Follow `!INSTALL.md` upgrade with a backed-up state file.

**Expect:** state validates and exact reconciliation passes after source replacement.

Follow uninstall, including `uninstall-plan` before and after the listed deletes.

**Expect:** only HMAC-verified tasks for this instance are deleted; foreign/lookalike
tasks remain; hooks removed; settings JSON valid; skill unavailable; archived state (if
chosen) remains readable outside the active path.

## Historical receipt boundary

The 2026-08-13 blind run tested a stateless 1.0.1 candidate. It is retained as history
and does not satisfy any 1.1.0 live gate above.
