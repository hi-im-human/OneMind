# Freestyle Beats — Known Issues

## Open — release blocking

## Open — documented runtime/implementation boundaries

### Hooks fail invisibly if interpreter/path/settings are wrong

Claude Code may not expose a failed command hook to the agent. Installation uses an
absolute interpreter and hook path; a real fresh-session receipt is still the proof.

### Create-first refresh needs spare task capacity

Safe replacement temporarily adds one task per managed entry before deleting old IDs.
If that peak would exceed Claude Code's 50-task limit, the planner blocks with no actions.
It does not silently switch to delete-first replacement.

### Failed delete after successful create can leave duplicates

Create-first plus a post-create re-list reduces deletion risk. If a later `CronDelete`
fails, both old and new jobs may remain. Verification reports the duplicate and the next
reconciliation removes the extra once deletion works.

### Create/re-list/delete is not one atomic runtime transaction

`verify-predelete` proves the replacement existed at the post-create CronList. A task
could still disappear before a later delete call because the runtime tools do not expose
a transaction. Final verification detects the resulting gap, but it cannot retroactively
preserve an old task already deleted. Controlled live create/delete failures pass; this
non-atomic boundary remains inherent to the runtime tools.

### No unattended execution while Claude Code is closed

Persisted state survives, but runtime jobs only fire while Claude Code is open and idle.
The package restores on return; it is not an OS scheduler, Desktop task, or cloud Routine.

### Atomic replacement has a small local path-race boundary

The scheduler rejects symlink/reparse components, writes a sibling temp file, fsyncs,
rechecks components, and calls `os.replace`. Python's cross-platform path APIs cannot
make the entire path walk and replacement one no-follow operation on Windows. A local
actor concurrently swapping path components could race the recheck; this package is not
a hostile multi-user filesystem boundary.

### Runtime jitter affects wall-clock fire time

Claude Code adds deterministic jitter to recurring tasks. Persisted cron expressions are
exact inputs, not promises of exact wall-clock execution. The five-day refresh threshold
leaves margin for daily maintenance jitter.

## Resolved in 1.1.0

- **No persisted schedule/restore path** — canonical state, atomic write, hooks, plan,
  and verify implemented.
- **Generative repeated runs were not idempotent** — setup selects once; later runs load
  canonical state and deterministic signed markers.
- **Public marker could delete lookalikes/other installations** — random instance ID +
  HMAC marker; complete live list classified in code.
- **CronList hides canonical cron and truncates prompt tails** — schema 2 uses a compact
  signed prefix whose digest identifies the exact canonical payload; human-readable
  schedule text and hidden tails are not reconstructed.
- **Schema-2 prefix needed live proof** — Claude Code 2.1.233 displayed all five complete
  61-character markers before truncation; setup and immediate idempotent reconcile
  verified 5/5 exact.
- **Fresh-conversation restore needed live proof** — a new conversation began with zero
  runtime jobs, received the SessionStart context, restored 5/5 from persisted state,
  and produced no actions on its second reconcile.
- **Scheduled maintenance and self-refresh needed live proof** — a minute-cadence
  maintenance task fired in an idle Claude Code 2.1.233 session, invoked the skill with
  `maintain`, created three replacements before deletion, passed the two-copy pre-delete
  gate, deleted the old IDs including itself, verified 3/3 exact, and recorded refresh.
  Its next scheduled fire selected reconcile and made zero mutations.
- **PowerShell UTF-8 BOM candidate failed JSON parsing** — the loader now accepts ordinary
  UTF-8 and UTF-8 BOM JSON via `utf-8-sig`; regression coverage added.
- **Current PostCompact workaround needed revalidation** — real `/compact` on Claude Code
  2.1.233 displayed successful PostCompact hook output with the SessionStart-named
  additionalContext, requested persisted-state reconciliation, and the follow-up plan
  retained all 5 task IDs with zero mutations.
- **Refresh deleted all jobs before creating replacements** — create-first plan,
  post-create re-list/verification, and 50-task peak guard.
- **`*/5` day-of-month maintenance gap was misdescribed** — daily maintenance plus
  five-day receipt threshold.
- **Hook could load environment workspace after malformed payload** — hook requires its
  own absolute payload `cwd`; no environment fallback.
- **Candidate/live input paths could read arbitrary files** — CLI paths restricted to
  the workspace's `.claude/freestyle-beats/` directory; stdin remains available for
  candidate creation.
- **Timestamp strings were unchecked** — timezone-aware UTC and ordering validated.
- **PostCompact loss stated as deterministic** — hook requests CronList verification and
  claims neither retention nor loss.
- **Skill invocations used as user beat prompts** — user prompts must be literal; only
  package maintenance invokes the skill.
