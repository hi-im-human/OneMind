# Selfhook — Known Issues

## Open

**Hook spawn failure is invisible to the agent.**
Status: inherent to the runtime. If Python is missing or the hook path is wrong, no
banner arrives and nothing says so. Mitigation: the Verify section of `!INSTALL.md`,
re-run after any environment change. A known *false* spawn failure: the session
was launched from a directory other than the workspace, so a different
`settings.json` was read (observed 2026-08-13 in an otherwise-valid blind install —
the session record's `cwd` was the diagnosis). Verify's cwd receipt exists for this.

**One bad comma in `settings.json` kills every hook, silently.**
Status: runtime behavior, documented. Verify step catches it.

**The budget rests on an observed floor, not a contract.**
Status: by design. 1,800 chars sits below the worst measured delivery (~2,000), but
the runtime documents no guarantee. If banners ever arrive visibly cut without the
explicit marker, the floor has moved down — re-measure from a real session receipt
and lower `PAYLOAD_BUDGET`.

**The hook cannot verify the agent actually reads the files.**
Status: inherent; see `!SPECS.md` non-goals. The banner design is the mitigation.

## Resolved (in ancestry / during packaging)

**Content injection silently truncated** — resolved 2026-07-31 by the pointer model.
**Same-event output blending** — resolved 2026-08-01 by banner, generalized here to
the section multiplexer.
**`"PostCompact"` payloads dropped** — resolved 2026-05-31 by emitting `"SessionStart"`.
**Partial render alongside config errors; marker outside the budget; silent
missing-file skips; 4,000-char budget above the measured floor** — all caught by
review during packaging (2026-08-13) and resolved before first release: error-only
payloads, marker reserved in-budget, visible missing-pointer errors, budget 1,800.
**Type errors escaping as tracebacks (`events: [{}]`, `dir: 42`); `dir: ".."`
rendering pointers outside the workspace; checker returning 0 on a typo'd cap
path** — reviewer's reproduced probes, second pass same day; resolved with
type-checks before operations, absolute-workspace + containment validation
(absolute/`..`/symlink escapes rejected), and shared caps validation that fails
the checker nonzero on any malformed or missing configured target.
**Directory-as-target passing validation (cap → checker traceback; pointer →
directory rendered as a file pointer); checker accepting a relative workspace the
hook rejects** — reviewer's third batch, same day; resolved by requiring every
pointer/cap target to be a regular file, a shared `validate_workspace` contract
used by both scripts, and a controlled exit 1 on capped-file read errors.
**Checker enforcing only part of the contract (section-level typos passed commit
while the hook refused to render); blank/whitespace slug+header rendering an
unnamed banner** — reviewer's final consistency batch, same day; resolved by the
checker running the identical full `validate()` and by requiring non-empty,
untrimmed-whitespace-free slug/header. Stale internal counts and an outdated
import description were aligned in the same pass.
**Misspelled keys as silent no-ops** (`event`→renders on every event,
`read_file`→text without pointers, `section`→exit 0 with no output, `cap`→all caps
disabled) — reviewer's schema pass, same day; resolved with strict allowed-key
validation at every level plus required explicit `sections`/`caps` lists, enforced
by both scripts. Same pass: unearned "cannot be truncated" wording resized,
uninstall order corrected to settings-first, SKILL.md cut-fragment warning added.
