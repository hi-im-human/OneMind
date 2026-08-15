# Tail Tales — Known Issues

## Open

### 1. Unknown flags are silently swallowed — a stale registration is invisible

`parse_known_args()` accepts and discards any unrecognised argument. No error, no warning, exit 0.

**Why it matters:** when a flag is removed from the code, every config still passing it keeps
working *in appearance*. The registration looks healthy and the flag controls nothing. This kept a
removed `--inject-only` registration alive and unnoticed for six weeks — and the flag did not make
the run read-only, so the full write path executed anyway (`tests/SMOKE_TESTS.md` Test 5).

**Workaround:** audit registrations against the parser's declared arguments (`--agent`,
`--output-dir`, `--output-name`), not against the docs. Not fixed here because tightening to
`parse_args()` would make the hook exit non-zero on a stale config — converting a silent
degradation into a hard failure at session start, which is a worse trade for a continuity hook.

### 2. Failures are invisible to the agent by construction

Errors go to a log file the agent has no standing reason to open. A failed run and a successful one
are indistinguishable from inside the agent. **Silence means "nothing was reported."**

**Workaround:** the verification step in `!INSTALL.md` is a *read*, not a `stat`. If the install
matters, check the content.

### 3. `--output-dir` moves the tale but not the error log

The error log always goes to `cwd`. Point the tale at a subdirectory and the two separate, so
anyone debugging a silent failure looks beside the tale and finds nothing. Documented rather than
changed — moving the log would break existing installs that know where to look.

### 4. ~~Live `PostCompact` induction is not covered by the test suite~~ — CLOSED 2026-08-15

Every smoke case feeds a synthetic stdin payload. That the runtime supplies these fields, in this
shape, at the moment it fires, was assumed and not proven.

**Closed on a real automatic compaction, 2026-08-15.** The reviewer bound the run to the raw
boundary record, its trigger type, the firing working directory, the session source, and the sole
registered writer at its frozen digest. Kept visible rather than deleted, because the *shape* of
this gap recurs: a suite can be green on every case it contains and still have never run the one
path that matters. Evidence: `tests/release-receipt.json` → `factual_runtime_claims`.

### 5. The tale's timestamp can precede the boundary record it was triggered by

Observed on the live induction: the output file's modification time landed roughly **34 ms
before** the runtime's own boundary record, while an independent watcher saw the file change
roughly 600 ms *after* it. The same inversion was **independently observed in a second agent
workspace on the same host**, so it is not attributable to one workspace's configuration.
**Two observations on one machine do not rule out a machine-specific quirk** — treat the scope
as open.

**No effect on emitted content** — the tale was complete and correct, and the post-boundary read
returned the exact file. It matters only when you are trying to establish causality.

**Operational rule:** never require the tale's mtime to be later than the boundary row, and never
rely on strict timestamp ordering alone. **Correlate the event window, then bind causality with
the registered route, the session source, and content hashes before and after** — which is what
the release receipt does.

## Resolved 2026-08-15 — found in independent release review

Every one of these failed **silently**. None produced an error, and the package looked healthy
throughout.

### The tale contained none of the owner's words — the worst defect this package has had

A `startswith("<")` filter meant to skip runtime markup discarded every channel-relayed message:
**12,181 in one transcript.** Across four agents, every surviving "owner" line was a scheduled
prompt. The file promising someone's exact words had never contained any.

**Fixed** by unwrapping the envelope instead of skipping it. **The ordering rule is the durable
part — a channel envelope is positive evidence of a person and outranks every machine heuristic.**
The first fix attempt inverted that order and reproduced the bug through a different mechanism,
because relayed human messages carry the same runtime markers as scheduled prompts.

### Ordinary speech was being deleted as markup

`<3 this matters` and `This session was hard` were both dropped by prefix tests while the agent's
reply survived — leaving a tale where the agent answers words that appear nowhere in it. Fixed: a
tag-shaped opener requires `<` followed by a **letter**, and only the exact resume banner is
skipped.

### Third parties' words were attributed to the owner

All relayed turns rendered under one label. Fixed: the speaker comes from the envelope's `user`
attribute, with a generic owner label as fallback. No handle-to-name map ships with this package.

### The 30,000-character cap was defined and never enforced

`HARD_CAP` existed in the source and nothing read it. Fixed on the write path, truncating from the
top; header preserved, trim announced in-file, oversized-single-turn case labelled rather than
silently fragmented. See `!DECISIONS.md` for why the record about this was wrong for two weeks.

### A fresh install wrote nothing

The module never created `--output-dir`. First compaction in a new workspace: exit 0, no tale, a
write-failure log the agent never reads. Fixed with `mkdir(parents=True, exist_ok=True)`.

**The test suite could not have caught this** — the harness pre-created the output directory, so
the instrument had the bug's blind spot built into it. Regression case now models a fresh install.

### One malformed timestamp crashed the whole run

Uncaught `ValueError` out of `main()`: traceback, exit 1, no tale, no error log — falsifying the
package's own "every failure path exits 0" claim. Fixed; a bad row degrades to `?`.

### Uninstall left the delivery mechanism behind — found by a fresh installer

The uninstall section listed three steps, none of which undid **install step 3** — the mandatory
*"arrange for the agent to read the tale"* — and then claimed *"Nothing else is touched… removing
the hook entry is a complete rollback on its own."*

A fresh agent with no prior context installed from the docs, used the package, and uninstalled it
cleanly by the guide. It left behind an operating document still instructing an agent to read
`.brain/SESSION_TALE.md` in a package that no longer existed.

**That instruction is not unrelated state. The install guide requires creating it.**

**⚠️ This same instruction has now failed in BOTH directions:** wrongly **removed** on
2026-07-29/31 (delivery assumed to cover it — it *was* the delivery), and wrongly **left** on
2026-08-15 (uninstall assumed it wasn't part of the install). Removed when needed, kept when dead,
silent both times.

**Rule taken, and it travels past this package:** *anything an install requires the user to create
belongs to the installation, and the uninstall owes it a step* — regardless of what the module's
own code writes. See `!DECISIONS.md` for the scope slip that produced it.

### An undeclared dependency, invisible on the build machine

Timestamps resolved a hardcoded IANA zone, which on Windows requires the external `tzdata`
package. It was installed here, so nothing ever failed — while the docs said no other packages were
required. Fixed by using the platform's local time, which needs no timezone database. *(The
hardcoded zone was also simply wrong for the machine: tales had been stamped an hour off.)*

## Resolved earlier (ancestry)

### Week-stale tales from hardcoded paths — 2026-06-10

Per-agent script copies each carried a hardcoded projects directory. After a workspace move they
silently captured a week-old transcript. Nothing errored; the tale was present, well-formed, and
wrong. **This is why the verify step is "read it," not "check it exists."**

### `hookSpecificOutput` rejected `PostCompact` — 2026-06-03

The schema validator accepted only `SessionStart` as a `hookEventName`, so output was silently
dropped. Relevant to the removed injection path; kept for the shape — *silently dropped* rather
than loudly rejected.

### Turn count inflated by thinking blocks — 2026-07-29

The header reported 53 turns for 40 real ones; the rest were reasoning blocks.

### Two registrations racing on one event — 2026-07-29, obsolete 2026-07-31

Both fired on the same event and one read the file before the other rewrote it. The agent woke
holding the previous compaction's tale. **A staleness failure, not a truncation one, so nothing
warned.** Now moot: one registration, no race.

### An invalid 70% compression claim — corrected 2026-07-29

Compared two different compactions covering different conversation. Re-measured on a single
transcript: 22,550 → 16,572, **26%**. Recorded because the wrong number was quotable and had been
quoted.

### Documentation outliving the code — corrected 2026-08-15

The injection removal deleted the code and left the prose. The install guide still documented a
removed flag and — worse — told installers to retire the *"read the tale after compaction"* line
from their agent's operating document because injection covered it. **It does not; that
instruction is the only delivery path.**
