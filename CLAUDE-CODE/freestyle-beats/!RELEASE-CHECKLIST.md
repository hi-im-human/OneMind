# Freestyle Beats — Release Checklist

## Current verdict

**PASS — 1.1.0 RELEASE-VERIFIED.** Required local/live acceptance, independent frozen-
diff review, sanitization, and link/version gates pass.

## Package structure

- [x] Required `!SCHEMA` files present.
- [x] Infrastructure catch-bin/reference/decision/dependency files present.
- [x] `SKILL.md`, `TOOL.md`, `config/tool.json`, `src/`, and tests present.
- [x] Self-contained installed skill includes scheduler, hooks, and template.
- [x] No dependency on an external/shared schedule.

## Canonical state and scheduler

- [x] Versioned schema persists exact IDs/labels/crons/prompts/enabled state.
- [x] Local-time runtime contract explicit.
- [x] Random instance + ownership key generated on first state creation.
- [x] Schema-2 compact prefix carries current-instance HMAC + canonical payload digest.
- [x] Routine `show` redacts ownership key.
- [x] Unknown keys, invalid cron/labels/IDs/prompts, duplicate semantic entries, fewer
  than two enabled beats, malformed UTC timestamps, and out-of-order receipts rejected.
- [x] State write uses same-directory temp + flush/fsync + component recheck + replace.
- [x] Candidate/live file inputs constrained to personal state directory (candidate
  stdin allowed).
- [x] Goal files used only for setup/explicit replace.
- [x] Replacement resets prior schedule verification receipts.

## Reconciliation and refresh

- [x] Complete normalized CronList input required.
- [x] Public marker lookalikes and other instances treated as foreign.
- [x] Missing task creates from canonical state.
- [x] Exact task keeps stable ID on ordinary reconcile.
- [x] Exact duplicate cleanup deterministic.
- [x] Drifted and orphaned instance-owned tasks repaired.
- [x] Foreign tasks never deleted or rewritten.
- [x] Refresh creates replacements before deleting old IDs.
- [x] Reported create is re-listed and verified against the saved plan before deletes.
- [x] Failed create or failed pre-delete observation blocks deliberate deletes.
- [x] Peak above 50 tasks blocks with no plan actions.
- [x] Post-action exact verify required before receipt.
- [x] Daily maintenance selects refresh at five-day receipt age.
- [x] Uninstall-plan emits only current-instance HMAC-verified delete IDs.

## Hooks and path selection

- [x] Hook payload `cwd` is required and canonical.
- [x] Missing/malformed cwd does not fall back to another environment workspace.
- [x] Invalid/missing state produces visible context and no mutation instruction.
- [x] Hook output JSON contract passes direct execution.
- [x] PostCompact wording claims neither survival nor loss.
- [x] Current live SessionStart delivery verified after install.
- [x] Current live PostCompact delivery/workaround verified after real compaction.
- [x] Absolute interpreter/hook paths tested on a path containing spaces.

## Automated/local verification

- [x] Scheduler/hook/test Python compiles.
- [x] Unit suite covers strict state, exact round-trip, ownership isolation,
  reconciliation, create-first refresh, cap block, maintenance threshold, session-loss
  simulation, hooks, and CLI path behavior.
- [x] Manifest and schedule template parse as JSON.
- [x] Final local test count/output copied into `tests/release-receipt.json` after all
  implementation changes freeze.
- [x] `git diff --check` clean after final documentation pass (line-ending warnings only).
- [x] Full package sanitization/secret/path/name scan rerun after schema-2 freeze; no
  credential, local path/account/session identifier, or nontechnical prose leak found.
- [x] No `__pycache__` directories or `.pyc` artifacts remain after local validation.
- [x] Independent final reviews pass: code/security found no substantive defect; docs
  recheck found no blocker beyond the completed release-status transition.

## Live Claude Code gates — all required

- [x] Claude Code 2.1.233 CronList exposes the complete compact marker prefix for every package task;
  truncated tails and human-readable schedules are accepted without reconstruction.
- [x] Setup creates exact state + 2–8 beats + maintenance; final 5/5 verify passed.
- [x] Immediate second reconcile creates/deletes nothing and retains IDs.
- [x] After deleting only `partial-loss`, reconcile created exactly that missing task,
  kept the other two IDs, deleted nothing, and verified 3/3.
- [x] Exact duplicate removed through real CronDelete; invalid-signature lookalike
  remained foreign and untouched.
- [x] Fresh conversation began with zero jobs, received SessionStart context, restored
  5/5 exact from disk, and remained idempotent on the second pass.
- [x] Real `/compact` delivered PostCompact additional context through the current
  SessionStart-named output workaround; follow-up reconcile kept all 5 IDs unchanged.
- [x] Stale refresh create at real 50-task cap returned `Too many scheduled jobs`; old
  5/5 remained, no partial create remained, and zero deletes ran.
- [x] Controlled delete race produced real `No scheduled job with id ...`; final 5/5
  verify passed and the next reconcile returned zero actions.
- [x] Fresh refresh plan over 50 live tasks blocked at projected peak 55 with
  `actions/create_actions/delete_actions: []` and preserved all 45 foreign tasks.
- [x] Minute-cadence scheduled maintenance prompt invoked `/freestyle-beats maintain`;
  its next scheduled fire did so again without a user turn.
- [x] Missing/expired receipt selected create-first refresh, verified 2 copies per entry
  before deleting old IDs, self-replaced maintenance, and recorded refresh success.
- [x] Runtime loss seam passes: fresh conversation lost every session task, then restored
  exact state and remained idempotent—the same missing-live-state path used after expiry.
- [x] Literal every-minute user beat fired repeatedly while idle and appended one exact
  line per fire; package/hook/runtime paths containing spaces worked.
- [x] Live uninstall-plan deleted 5/5 HMAC-verified tasks and preserved the spoof; second
  plan returned owned count 0 / foreign count 1.
- [x] In-place package upgrade preserved state byte-identically; full uninstall removed
  only owned live tasks, exact hook entries, installed skill, and state while preserving
  unrelated settings and a foreign task.

## Documentation consistency

- [x] README/SPECS/SKILL/TOOL/INSTALL/DEPENDENCIES describe the same state path and
  modes.
- [x] Runtime IDs described as ephemeral.
- [x] No unattended/closed-session claim.
- [x] Jitter, seven-day expiry, open/idle requirement, no catch-up, and 50-task cap
  documented.
- [x] Family scheduler explicitly excluded.
- [x] Technical-only prose: installation, behavior, dependencies, failures,
  verification, and concrete effects.
- [x] Final link/path/version scan after freeze: no markdown/wiki links; placeholders,
  schema 2, and 1.1.0 release status are consistent.

## Release rule

Release verification requires every gate above to pass with a dated receipt tied to the
frozen implementation candidate. Version 1.1.0 satisfies that rule.
