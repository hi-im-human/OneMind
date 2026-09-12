# Freestyle Beats — Changelog

## Current status

**1.1.1 — persisted-beat ceiling fixed. Patch, NOT release-verified.**

⚑ **What was run for 1.1.1:** both suites on the shipped object (6/6 new red/green
controls, 30/30 existing, 1 skip); the same controls against the pre-fix bytes
(4 red, 2 green), so the instrument is known to discriminate; independent check by a
second agent of the diff, both suites, both directions, and the maintenance
accounting behind the derived ceiling; a doc sweep for the stale number.

⛔ **What was NOT run:** live acceptance, sanitization, and the link/version gates —
i.e. the gates that earned 1.1.0 its banner. *This status originally read
"release-verified" because that phrasing was inherited from the 1.1.0 block rather
than measured. A status field should undersell before it repeats a prior release's
claim on a patch.*

⚑ **Next action:** none outstanding. Pushed to `origin/main` 2026-09-12 at the
repository owner's word, carrying the previously-held local commit `f7c3e7d` with it;
both verified present on the remote. Installed copies should pull to get the fix.

## 2026-09-12 — 1.1.1 persisted-beat ceiling

### Fixed

- **`MAX_USER_ENTRIES` was a number of ours (8) and is now the platform's, less the
  maintenance task (`CRON_TASK_LIMIT - 1` = 49).** The 8 was written 2026-08-18 as a
  "sane day" guideline. It predates schedules that carry seven circadian beats plus
  three assigned project slots, so the structural load — eleven — could not be written
  to the file at all.
- **The cap was not only a limit; it decided what the restore path could know about.**
  `_validate_entries` refuses the FILE WRITE. It does not touch `CronCreate`, so a
  refused beat still registers and still fires. The reconcile restores only what the
  file holds, so the overflow beats vanish at the next restart **and leave no trace on
  either side of the seam**: foreign-task classification detects present-and-unmanaged,
  while this failure is absent-and-unrecorded. *An entry that cannot be written cannot
  be missed.*
- **The write-time refusal now names the consequence** rather than only the bound:
  a live cron absent from this file will not survive a restart.
- **The session notice now states what it cannot vouch for.** It previously reported a
  count taken from the file and instructed the agent not to derive beats from anywhere
  else — correct for preventing drift, and precisely what foreclosed the one recovery
  path that would have noticed a missing beat. The count read as complete while being
  silently partial.

### Tests

- `tests/test_restart_recovery_gap.py` — four red controls (structural load persists;
  ceiling is the platform's; refusal names the restart consequence; notice admits what
  it cannot see) and two green controls (an ordinary schedule stays valid; a count above
  the platform limit is still refused — so the suite cannot pass on a build with no
  validation at all).
- Verified in both directions on the shipped object: with the fix, 6/6 new and 30/30
  existing (1 skip); against the pre-fix bytes, 4 red and 2 green.
- *Recorded because it nearly shipped:* the notice control first scraped module source
  and failed with `ValueError: substring not found` — a fixture failure indistinguishable
  from a real one, which would have gone green as soon as the anchor was corrected,
  fix or no fix. It was rewritten against the rendered `hook_notice` output.

### Notes

- Nothing in the existing suite pinned the old number or the old message text; checked
  before editing.
- Pre-change bytes kept at `src/scheduler.py.bak-20260912-pre-cap-fix`.
- Builder: Cael 🔩 · Reviewer: Haven 💙 (independent check: diff, both suites, both directions,
  and the `expected_tasks` maintenance accounting behind the −1).


## 2026-08-17 — 1.1.0 release promotion

- Promoted the tested 1.1.0-rc.2 implementation to 1.1.0 after final independent
  code/security and documentation review.
- Final sanitization found no credential, private path/account/session identifier,
  generated cache, broken link, or nontechnical prose leak.
- Registry metadata now identifies version 1.1.0 without a candidate status field.

## 2026-08-17 — 1.1.0-rc.2 personal scheduler implementation

### Added

- `src/scheduler.py`:
  - strict versioned state schema;
  - workspace-local canonical schedule;
  - random instance identifier and HMAC ownership markers;
  - atomic write and reparse/symlink checks;
  - UTC timestamp validation;
  - tool-ready runtime definitions;
  - complete-list reconciliation plan;
  - create-first replacement, saved plan, post-create re-list verification, and 50-task
    peak guard;
  - exact post-action verification and receipts;
  - HMAC-verified uninstall planning;
  - daily maintenance mode with five-day refresh threshold;
  - visible hook notices and fail-closed hook workspace resolution.
- `src/templates/SCHEDULE.template.json` for setup/replace candidates.
- `tests/test_scheduler.py` covering state exactness, validation, replacement receipts,
  idempotency, duplicate/drift/orphan repair, foreign/spoof isolation, create-first
  ordering, capacity block, maintenance threshold, simulated session loss/expiry,
  hook errors, and CLI environment resolution.

### Changed

- Installed surface is self-contained: copy `SKILL.md` plus the complete `src/` tree.
- SessionStart/PostCompact hooks import the scheduler and point at persisted state.
- Skill modes are `setup`, `reconcile`, `maintain`, `refresh`, and `replace`.
- `CronDelete` is now a hard runtime dependency.
- User beats keep literal prompt text; only the daily maintenance task invokes the skill.
- Reconciliation receives the complete normalized CronList response and classifies
  ownership in code.
- Replacement creates all required new tasks before deleting old task IDs.

### Corrected during implementation review

- Replaced public ownership suffixes with instance-scoped HMAC markers.
- Replaced `*/5` day-of-month maintenance with daily maintenance plus an elapsed-time
  threshold; the old expression did not guarantee five elapsed days across months.
- Removed delete-first refresh and added peak-capacity blocking.
- Stopped hook fallback from malformed/missing payload cwd to process environment.
- Restricted candidate/live JSON paths to personal state directory.
- Added UTC timestamp/order validation, enabled-count validation, and stricter cron-step
  validation.
- Redacted ownership key from routine `show` output.
- Added `verify-predelete` after final audit found that a reported create alone was not
  enough evidence to proceed with old-task deletion.
- Added executable `uninstall-plan` instead of requiring manual marker classification.

### Corrected after first live Claude Code 2.1.233 run

- The model-visible `CronList` result uses human-readable schedule text and truncates
  prompt previews near 78 characters. Full canonical fields exist in the outer stream
  event but are not available to the model executing the skill.
- Schema 1's end-of-prompt marker therefore could not be classified. Schema 2 replaces
  it with a 61-character signed prefix: compact instance, entry token, canonical payload
  digest, and HMAC signature.
- Live normalization now requires only the complete task list's IDs, recurring flags,
  and verbatim visible prompt previews. It ignores display schedule text and never
  reconstructs hidden prompt tails.
- Maintenance is a marker-prefixed literal instruction to run `/freestyle-beats
  maintain`, so its ownership prefix remains model-visible.
- Added a display-only/truncated-preview regression test before the fresh live rerun.

### Schema-2 live acceptance completed

- Installed setup created 5/5 tasks; every 61-character marker remained visible in the
  model-facing CronList preview; exact verify and immediate idempotent reconcile passed.
- A fresh conversation received SessionStart context, began with zero session jobs,
  restored 5/5 from persisted state, and remained idempotent.
- A real exact duplicate produced one planned CronDelete. A complete invalid-signature
  lookalike stayed foreign through reconcile and HMAC-scoped live-task uninstall.
- In an idle interactive session, a minute-cadence maintenance prompt invoked the skill,
  selected refresh, created all replacements before deleting old IDs including itself,
  verified 3/3, and recorded the receipt. Its next fire selected no-op reconcile.
- Candidate/live JSON parsing now accepts PowerShell-generated UTF-8 BOM files in addition
  to ordinary UTF-8 after the maintenance fixture exposed that Windows input edge.
- Real `/compact` delivered the PostCompact context workaround; follow-up reconciliation
  retained all five IDs with zero mutations.
- A literal every-minute user beat fired in an idle workspace whose path contained spaces;
  a controlled partial loss restored only the missing task.
- Controlled real CronCreate/CronDelete failures preserved exact state. A 50-task run
  returned the runtime cap error, blocked a fresh peak-55 plan with no actions, and left
  all 45 foreign jobs untouched.
- In-place upgrade preserved canonical state bytes; full uninstall removed only package
  jobs, exact hook entries, installed files, and state while preserving unrelated settings
  and a foreign task.

## 2026-08-17 — Technical documentation correction and release block

- Audited version 1.0.1 against its files and runtime contract.
- Confirmed it shipped no state serializer, loader, or exact restore path.
- Identified generative slot selection as a separate idempotency defect.
- Rewrote package documentation to installation/behavior/dependency/failure/verification
  content only.
- Marked 1.0.1 blocked rather than describing reminders as durability.
- Preserved the 2026-08-13 test receipt as historical evidence for the superseded
  stateless candidate only.

## 2026-08-13 — 1.0.1 standalone extraction

- Added canonical package documentation files, goal templates, hook wrappers, registry
  metadata, smoke tests, and a release receipt.
- Removed fixed schedule content owned by external/private infrastructure.
- Changed PostCompact wording to require CronList verification after live evidence showed
  both cron survival and cron loss.
- Retained literal user beat prompts after measured context cost from scheduled skill
  invocations.

Version 1.0.1 passed its then-current install/session/uninstall test sequence but did not
test or implement cross-session durability. That receipt does not certify 1.1.0.
