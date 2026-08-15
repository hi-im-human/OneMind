# Tail Tales — Specs

## Design

One script, one job: on `PostCompact`, read the session transcript, extract the conversational
turns nearest the compaction boundary, and write them to a markdown file.

The problem it addresses is that a compaction summary is a *paraphrase*. Paraphrase is lossy in a
specific direction — it keeps the gist of what was decided and drops the exact wording of what was
said. For an agent resuming after a seam, the user's literal phrasing is the part that cannot be
reconstructed; the agent's own reasoning largely can be. So the tale preserves words and discards
reasoning, which is the opposite of what a summariser optimises for.

**It writes a file. It does not put anything in an agent's context.** See `!DEPENDENCIES.md`.

## Input contract

The runtime supplies a JSON payload on **stdin**. Two fields are read:

| field | required | used for |
|---|---|---|
| `transcript_path` | yes | the source transcript (JSONL) |
| `cwd` | yes | the agent's workspace — error-log destination, and the default agent label |

Nothing else is read from the payload. No environment variables, no config file, no hardcoded
paths. **Adding an agent requires no source edit** — identity arrives at fire time.

## Transcript parsing

Read line-delimited JSON. Per line, by `type`:

- **`user`** — captured as a spoken turn, in this order. **The order is load-bearing.**

  1. **Channel envelopes are unwrapped first.** A `<channel …>…</channel>` wrapper means a relayed
     message; the words inside are the message and the `user` attribute names the speaker. This is
     **positive evidence of a person and outranks every test below it.** Runtime commentary
     outside the envelope is discarded.
  2. **Machine-authored rows are skipped** — `isMeta: true` or `promptSource: "system"` — but
     **only when step 1 found no envelope.** These fields mark scheduled prompts *and* relayed
     human messages identically, so testing them first deletes exactly what step 1 recovers. This
     is a structural test: it needs no list of prompt names and cannot rot as prompts change.
  3. **Genuine markup is skipped** — a tag-shaped opener, meaning `<` followed by a **letter**.
     Ordinary speech beginning with `<` is kept: `<3 this matters` survives because `3` is not a
     letter.
  4. **Only the exact resume banner is skipped**, not every line beginning "This session".
  5. Entries whose content is entirely `tool_result` blocks, and bare skill invocations, are
     skipped.

  ⚠️ Steps 1–4 exist because a single blanket `startswith("<")` test destroyed every relayed
  message this package ever saw. See `!BUGS.md`.
- **`assistant`** — only `text` blocks are captured. **`thinking` and `tool_use` are deliberately
  discarded** (2026-07-29): reasoning arrived as truncated fragments and is the most
  reconstructable content in the file, while tool calls were pure volume.
- **`system` with `subtype: compact_boundary`** — recorded as a boundary marker.

**Boundary rule:** everything before the *last* boundary is dropped. The tale covers the current
window, not the previous one.

**Selection:** walking backwards, keep turns until `TAIL_TURNS` (40) conversational turns are
collected. The count is of real turns — an earlier version counted thinking blocks too and
reported "53 turns" for 40.

**Collapse:** consecutive identical messages from one speaker become one line with a `(×N)` count,
so an auth error firing N times consumes one slot instead of N. Non-consecutive repeats are
preserved — that repetition is real signal.

## Output contract

A markdown file at `--output-dir` / `--output-name`. **The output directory is created if it does
not exist.** A header carrying the agent label, write timestamp, source transcript filename, and
conversational turn count; then `---`; then the turns.

**Speakers.** A relayed turn is labelled with the `user` value from its envelope; a direct turn
falls back to a generic owner label. **No handle-to-name mapping ships with this package** —
whoever the file says spoke is who the next agent will believe spoke, so the label comes from the
transcript or not at all.

**Timestamps** render in the runtime machine's own local time. No timezone database is required
and no zone is hardcoded.

**The file is overwritten every compaction.** It is a snapshot of the seam, not an accumulating
archive. Anything that must persist has to be copied elsewhere.

**The tale is capped at 30,000 characters, enforced on the write path.** There is one file and no
second copy, so this is the only place a limit can live.

**Truncation is from the top.** The oldest turns are dropped first; the material nearest the
compaction seam is what a returning agent needs, so it is the last to go. The header always
survives, and **the trim announces itself in the file** — with one copy and no fallback, a silent
trim would be indistinguishable from a quiet session.

If a single turn exceeds the whole budget, its **tail** is kept (consistent with top-truncation)
behind an explicit `[… opening of this turn cut …]` marker, so a fragment is never presented as a
complete message.

*(This was ruled on 2026-07-29 and went unenforced until 2026-08-15 — the record explaining its
absence was itself wrong. See `!DECISIONS.md`.)*

## Failure policy (load-bearing)

**Every failure path exits 0 and writes nothing.** A continuity hook that crashes the runtime it
is meant to protect has failed worse than one that produces nothing.

| condition | behaviour |
|---|---|
| stdin unparseable | message to stderr; return. No workspace can be trusted yet. |
| `cwd` missing | message to stderr; return. **No error log** — there is nowhere trustworthy to write one. |
| `transcript_path` missing | logged to `<cwd>/last_session_tail.err.log`; return |
| transcript file absent | logged; return |
| **no turns extracted** | logged; **return before the write** — an existing good tale is never replaced by an empty one |
| a row carries an unparseable timestamp | that row's stamp degrades to `?`; the tale is still written. **One bad row must not cost the whole tale** — this path previously raised, exiting 1 with a traceback and no output, which falsified the guarantee above |
| write fails | logged; return |

⚠️ **The error log goes to `cwd`, not to `--output-dir`.** Only the tale is relocated. If the tale
is pointed at a subdirectory, the two files land in different places.

⚠️ **Errors are never surfaced to the agent.** They land in a file the agent has no standing reason
to open. Silence from this package means *"nothing was reported,"* not *"nothing went wrong."*

## Argument handling — a sharp edge

The parser uses `parse_known_args()`, so **unrecognised flags are silently accepted and
discarded.** There is no error, no warning, and no exit code. A stale registration carrying a
removed flag looks exactly like a working one, and the flag does not suppress any behaviour it may
once have controlled. Verified: `tests/SMOKE_TESTS.md` Test 5.

## Non-goals

- **Injection.** Removed 2026-07-31. This package does not deliver anything to a context window.
- **Archiving.** One file, overwritten. No history, no rotation, no database.
- **Summarising.** Turns are reproduced, not condensed. The point is the exact wording.
- **Multi-agent coordination.** N=1. No roster, no shared state, no partner required.
- **Reporting its own failures to the agent.** By design it cannot; arrange that separately.
