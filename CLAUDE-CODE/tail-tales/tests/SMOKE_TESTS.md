# Smoke Tests: Tail Tales

Run with `python tests/smoke_test.py` from the package root. Every case builds a throwaway
sandbox — the suite never touches a real workspace, and never reads a real transcript.

Results below are pasted from an actual run: **2026-08-15, Windows 11, Python 3.13, candidate
`src/post_compact_shared.py`.** Suite exit `0`, **40 assertions across 15 cases, 0 failures**.
The same suite was additionally run against the *installed copy* in an isolated fresh home by an
independent stateless agent, with the same result.

*(The count read `36/36` until 2026-08-15. It was stale: cases added during independent release
review raised the assertion count and the header was not re-derived from the run. Corrected by
counting the actual output rather than trusting the prose — the same class of defect this suite
exists to catch, found in the suite's own documentation.)*

Tests 10–15 are regression cases for defects found in independent release review the same day.
Each one models a failure that shipped, went unnoticed, and produced no error.

**⚠️ Live-caller coverage.** No case here is driven by a real `PostCompact` event; every case
feeds a synthetic payload. That gap was closed *outside* this suite by an actual automatic
compaction on 2026-08-15, reviewed and bound to the raw boundary record — see
`tests/release-receipt.json`. **A synthetic payload cannot substitute for the live caller, and
this suite should not be read as covering it.**

## ⚠️ Test 6 runs FIRST, on purpose — it is the bait

The property this suite most needs to prove is *"a bad transcript cannot destroy a good tale."*
A suite that cannot observe that property failing does not verify it. So the first case seeds a
known-good tale, feeds an empty transcript, and asserts the tale comes back byte-identical. **If
the bait does not hold, the run aborts and no other result is reported** — a green light from an
instrument that cannot go red is not information.

## Test 6 — empty transcript must not clobber an existing tale (BAIT)

```bash
# sandbox seeded with "ORIGINAL GOOD TALE — must survive\n", transcript is empty
python src/post_compact_shared.py --output-dir <box>/.brain --output-name SESSION_TALE.md
```

Expected: existing tale untouched; refusal recorded; exit 0.

Actual:

```
exit=0  stdout=''  stderr=''
tale_written=True  tale_chars=34          <- unchanged, byte-identical to the seed
err_log: no turns extracted from transcript.jsonl (boundary at end?)
BAIT HELD
```

Status: **passed.** The module returns before the write when no turns extract.

## Test 1 — happy path

```bash
python src/post_compact_shared.py --output-dir <box>/.brain --output-name SESSION_TALE.md --agent TestAgent
```

Actual:

```
exit=0  stdout=''  stderr=''
tale_written=True  tale_chars=342
```

Status: **passed.** Tale contains the agent's text; the owner turn renders as `User:` with no
real name present.

## Test 2 — payload missing `transcript_path`

Actual:

```
exit=0  stdout=''  stderr=''
tale_written=False
err_log: stdin payload missing transcript_path
```

Status: **passed.** No tale written; failure lands in the workspace error log, not in the agent.

## Test 3 — `transcript_path` points at a nonexistent file

Actual:

```
exit=0  stdout=''  stderr=''
tale_written=False
err_log: transcript_path does not exist: <box>\transcript.jsonl.missing
```

Status: **passed.**

## Test 4 — payload missing `cwd`

Actual:

```
exit=0  stdout=''  stderr='tail-tales: stdin payload missing cwd'
tale_written=False
```

Status: **passed.** With no trustworthy workspace, the failure goes to stderr and nothing is
written — including no error log. This is the one case with no on-disk trace.

## Test 5 — unknown flag `--inject-only` (removed 2026-07-31)

```bash
python src/post_compact_shared.py --output-dir <box>/.brain --output-name SESSION_TALE.md --agent TestAgent --inject-only
```

Actual:

```
exit=0  stdout=''  stderr=''
tale_written=True  tale_chars=342
```

Status: **passed, and this is the result to read carefully.**

The argument parser calls `parse_known_args()`, so an unrecognized flag is **silently accepted and
discarded**. `--inject-only` does not error, does not warn, and does **not** suppress the write —
the body is byte-identical to the run without it.

⚠️ **Consequence for anyone with a stale `SessionStart` registration:** the flag does not make the
run read-only. The full regenerate-and-write path executes. Whether that destroys a good tale then
depends entirely on Test 6's behaviour — if the session's transcript yields no turns, the existing
tale survives; if it yields a few, the tale is replaced by a short one. **Remove the registration
rather than relying on the flag to neuter it.**

## Test 7 — compaction-boundary discipline

Transcript: turn, turn, `compact_boundary`, turn.

Actual:

```
exit=0  tale_written=True  tale_chars=277
```

Status: **passed.** Post-boundary content present; pre-boundary content absent. The tale covers
the current window, not the previous one.

## Test 8 — reasoning blocks excluded

Transcript contains an assistant `thinking` block with a sentinel string.

Actual:

```
exit=0  tale_written=True  tale_chars=342
```

Status: **passed.** Sentinel absent. Only `text` blocks are captured (deliberate, 2026-07-29).

## Test 9 — agent label derives from `cwd` basename

Run with no `--agent` override.

Actual:

```
exit=0  tale_written=True  tale_chars=346
```

Status: **passed.** Label taken from the sandbox directory name rather than the override.

## Test 10 — speech vs. runtime noise (the regression that matters most)

Feeds, in one transcript: speech beginning `<`, speech beginning "This session", a channel-relayed
message from `owner`, a channel-relayed message from `Reviewer`, a scheduled prompt, runtime
markup, and a pure `tool_result` entry.

⚠️ **The two relayed fixtures carry `isMeta: true` and `promptSource: "system"` on purpose.** The
runtime stamps relayed human messages with the same markers it puts on scheduled prompts. A fix
that skipped marked rows *before* unwrapping the envelope deleted every relayed message —
reproducing the original bug by a different route. This fixture is the bait for that.

Actual:

```
exit=0  stderr=''
tale_written=True  tale_chars=483
```

Status: **passed, 9 assertions.** `<3 this matters` preserved · `This session was hard` preserved ·
envelope unwrapped · commentary outside the envelope dropped · relayed speech survives despite the
machine markers · two relayed humans remain two distinct speakers · a direct turn keeps the generic
owner label · no house-specific handle mapping · scheduled prompt, runtime markup, and `tool_result`
all excluded.

## Test 11 — a malformed timestamp must not cost the tale

One row carries `timestamp: "not-a-time"`.

Actual:

```
exit=0  stderr=''
tale_written=True  tale_chars=363
```

Status: **passed.** Previously this raised an uncaught `ValueError` out of `main()` — traceback,
exit 1, no tale, no error log. It degrades to `?` now.

## Test 12 — a tale over the cap truncates from the TOP

61 turns, ~55,000 characters, oldest carrying `OLDEST_SENTINEL` and newest `NEWEST_SENTINEL`.

Status: **passed, 5 assertions.** Output ≤ 30,000 · header intact · `NEWEST_SENTINEL` present ·
oldest turns dropped · the trim announces itself in the file.

## Test 13 — a single turn larger than the entire cap

One turn of ~40,000 characters, `HEAD_OF_TURN` at its start and `TAIL_OF_TURN` at its end.

Status: **passed, 3 assertions.** Output ≤ 30,000 · the opening is cut and the end nearest the seam
kept · the partial turn is labelled `[… opening of this turn cut …]` rather than passed off as
complete. **This is the "no mid-record ambiguity" case** — a fragment must never look like a whole
message.

## Test 14 — fresh install, output directory does not exist

Runs with `--output-dir` pointing at a directory that has not been created.

Status: **passed.** The module creates it.

⚠️ **This case exists because the harness itself hid the bug.** The original suite always
pre-created the output directory, so the instrument had the defect's blind spot built into it and
reported green while a fresh install silently wrote nothing.

## Not covered here

- **Live `PostCompact` induction.** Every case above feeds a synthetic payload on stdin. Whether
  the runtime supplies the fields this module expects, at the moment it expects them, is not
  proven by this suite and must be confirmed on a real compaction.
- **The read.** This suite verifies the file is written correctly. It cannot verify anything
  opens it — see `!DEPENDENCIES.md`.
