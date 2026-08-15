# Tail Tales — Changelog

## 2026-08-15 — the package was destroying the thing it existed to preserve

**Found in independent release review. Fixed in the live source and here.**

### The tale contained none of the owner's words. It never had.

A filter meant to skip runtime markup tested `text.startswith("<")`. Every message relayed through
a channel arrives wrapped in a `<channel …>` envelope, so the filter discarded **all** of them —
**12,181 in a single live transcript.** Across four agents, every "owner" line that had ever
survived into a tale was a scheduled prompt. Not one was a person speaking.

The stated design rationale made it sharper: reasoning is dropped because it is reconstructable,
while the owner's words are not. **The filter then deleted the irreplaceable half and kept the
recoverable one.**

Ordinary speech was collateral: `<3 this matters` and `This session was hard` were both discarded
by prefix tests, while the agent's reply survived — so a tale could show the agent answering words
that appear nowhere in it.

**Fix, and the rule that came out of it: a channel envelope is positive evidence of a person and
outranks every machine heuristic. Unwrap first, then classify.** The first attempt inverted that
order and reproduced the bug — the runtime marks relayed human messages with the same `isMeta` /
`promptSource` fields it puts on scheduled prompts, so a skip-if-marked test placed ahead of the
unwrap deletes exactly the same messages by a different route.

### Speakers are now attributed to whoever actually spoke

The envelope carries a `user` attribute. Relayed turns previously all rendered under the owner's
label, so a third party's words were printed as the owner's. Attribution in a continuity record is
not cosmetic — whoever the file says spoke is who the next agent will believe spoke. **No
handle-to-name mapping is shipped; the label comes from the envelope or falls back to a generic
owner label.**

### Scheduled prompts are excluded

Structurally, via `isMeta` / `promptSource` — not by matching prompt text, so it cannot rot as
prompts change. Applied **only** to rows with no person-evidence, per the ordering above.

### The 30,000-character cap is now actually enforced, on the write path

It had been defined and never read. There is one file and no injected copy, so the write path is
the only place a limit can live. **Truncation is from the top** — the oldest turns go first and
the material nearest the seam is the last to be dropped. The header always survives, the trim
announces itself in the file, and a single turn larger than the whole cap keeps its tail with an
explicit `[… opening of this turn cut …]` marker rather than passing a fragment off as complete.

### Three smaller ones, each of which failed silently

- **The output directory was never created.** A fresh install pointing `--output-dir` at a
  subdirectory that did not exist yet wrote nothing and logged a failure the agent never saw.
- **A malformed timestamp crashed the run** — uncaught `ValueError`, traceback, exit 1, no tale,
  no error log, falsifying this package's own "every failure path exits 0" claim. Now guarded;
  one bad row degrades to `?` instead of costing the whole tale.
- **The timezone was a hardcoded IANA zone**, which on Windows requires the external `tzdata`
  package to resolve — an undeclared dependency that happened to be installed on the build
  machine, so it never failed there. Timestamps now use the platform's own local time. *(This also
  revealed the hardcoded zone was simply wrong for the machine it ran on: tales had been stamped
  an hour off.)*

### Also corrected in the documentation

The error log is written to `cwd`, **not** beside the tale — `--output-dir` relocates the tale and
nothing else. Three files claimed otherwise, which would send anyone debugging a silent failure to
an empty directory.

## 2026-07-31 — injection removed; this pack writes only

**Owner ruling. Current behaviour starts here — every entry below describes a design that no
longer runs.**

Tail Tales no longer injects anything. It writes the tale to disk and exits. The `--inject-only`
flag and its `SessionStart` registration are gone; the only registration is `PostCompact`.

**Why:** the hook transport truncates payloads well below the size of a real tale, so injecting
one was never reliable. A separate hook now emits a short *pointer* telling the agent to read
its files, and the agent reads them itself — the one path the transport cannot shorten.

**What this means for the reader:** the entries below discuss injection budgets, hard caps on an
injected copy, and a `--inject-only` race guard. Those were real and are now historical. **The
package as shipped has one job: write the file.** See `!DEPENDENCIES.md` for what you must
arrange so something actually reads it.

## 2026-07-29 (later) — race guard: SessionStart stands down on compact

**Found the same day the fix below shipped, and it was reintroducing the same class of bug in a new place.**

On compaction Claude Code fires **`SessionStart` with source `compact`** — the hook runner labels it `SessionStart:compact` — *in addition to* `PostCompact`. Both of this pack's registrations therefore run on the same event, and `--inject-only` read the tail **before** the PostCompact path rewrote it.

Observed live, in the builder's own context:

| | timestamp | format |
|---|---|---|
| copy **injected into the agent** | 2026-07-28 09:47 | old — "53 turns" |
| file **on disk** | 2026-07-29 07:38 | new — "40 conversational turns", correct |

The agent woke holding the **previous** compaction's tail while the correct one landed on disk moments later. It fails by **staleness, not truncation**, so nothing warns — the header timestamp is the only tell.

**Fix:** `--inject-only` returns immediately when `payload["source"] == "compact"`. PostCompact owns that event. If `source` is absent or unexpected the old behaviour is unchanged, so it degrades safely; and if PostCompact ever failed to fire, the CLAUDE.md fallback catches the missing block (a reviewer's catch, below).

Verified across all three branches: `source=compact` → 0 bytes emitted · `source=startup` → 15,986 · `source` missing → 15,986 · `SESSION_TALE.md` untouched throughout.

**Also established while investigating — there are THREE injection layers, not two.** Claude Code natively re-injects `CLAUDE.md` in full, `MEMORY.md`, the compaction summary, a transcript pointer, git status, the deferred-tools list, and **every skill invoked earlier in the session as a complete SKILL.md body.** It does *not* inject `.memory/identity/*.md` — that remains Selfhook's. Every budget decision made this week assumed two layers; the native layer had not been measured by anyone.

the builder · found while answering a question of the owner's about something else

### Release review

**Independent reviewer: Sable.** Not a rubber stamp on a finished thing — the review is why most
of the entries above exist. The reviewer ran the release gate against the exact candidate bytes
and reproduced the digest each round; drove two stateless docs-first onboarding sessions from
fresh homes, one of which **failed the package** and produced the uninstall-lifecycle fix;
pre-registered the acceptance criteria for the live `PostCompact` induction **before** the
qualifying event, so the builder could capture evidence without grading his own work; and caught
the builder asserting, after a context seam, that review runs had not happened when the shared
worklog held them.

Author: Thread · packaging: Cael · independent release review: Sable

---

## 2026-07-29 — this pack now owns SESSION_TALE end to end

**Context:** Selfhook was separately injecting a copy of this pack's output, capped at 20,000 chars, while this pack emitted only a *"go read the file"* pointer. Two packs, one file, mismatched limits. Measured across CC agents — 43,291 · 35,975 · 37,843 · 72,596 — **every one over the cap, none ever under it.** It fired every compaction and trimmed from the *end*, dropping the material nearest the seam: ~109,705 chars lost across four agents, every time, silently.

**Changed:**
- **Injects the tail itself.** The pointer is gone; the notice states whether the copy is complete or trimmed, and only sends the agent to the file when there's genuinely more there. Selfhook's SESSION_TALE handling + `SESSION_TALE_LIMIT` removed (with a *do-not-re-add* comment).
- **`--inject-only` + SessionStart registration.** Injects the existing file without regenerating — regenerating at SessionStart runs against a near-empty transcript. Without this, compaction was covered but a plain **session restart woke with no tail**. Silent no-op if the file is absent. On trim it preserves the header through the first `---` and trims the body from the front; slicing the raw string from the end delivered an unlabelled mid-conversation fragment.
- **Reasoning + tool calls dropped.** Reasoning was capped at 300 chars, so it arrived as fragments — anxiety without resolution — and it's the most *reconstructable* content in the file, whereas the owner's exact words can't be regenerated at all. (Tool calls were never actually captured; the old code only read `thinking` and `text` blocks. Removing them changed nothing — worth recording, since I'd have gone on believing I'd fixed something.)
- **`collapse_repeats()`** — consecutive identical messages from one speaker collapse to one line with a `(×N)` count, so a relog/auth error firing N times stops eating N slots. Non-consecutive repeats preserved; that repetition is real.
- **`HARD_CAP = 30,000`, applied to the INJECTED COPY ONLY.** The file on disk always keeps everything — the trim is non-destructive. First version wrote the capped text to disk too, which would have removed the escape hatch this change was meant to protect (the owner caught it).
- **Trims oldest-first.** Newest turns survive.
- Header now counts *conversational* turns. The old "53 turns" was 40 real turns + 13 thinking blocks.

**Measured, not assumed:** proper A/B on a single transcript, 22,550 → 16,572 (**26%**). An earlier "70%" claim of mine was invalid — it compared two different compactions covering different conversation. Both trim branches exercised by forcing the cap to 6,000; missing file → exit 0, zero output; live `SESSION_TALE.md` untouched throughout; dedupe unit-tested both directions.

**Ordering rule worth keeping:** the *"go read your tail"* instruction was **load-bearing precisely because the injection was broken.** Removing it before fixing the size would have silently deleted half the tail and looked like an optimization. Fix the size, verify, *then* remove the read step.

the builder (build) · the owner (ruling, and two corrections that moved it from shipped to correct) · a reviewer (caught that I'd removed my own fallback before ever compacting under the new hook)

---

## v26.07.03_d1 (2026-07-03) — backport output override args

- Added `--output-dir` and `--output-name` args (backported from loose hook at `hooks/CLAUDE/tail-tales/post_compact_shared.py`, which evolved ahead of the pack)
- Default behavior unchanged: falls back to `cwd / "last_session_tail.md"` when neither flag is passed
- Live registrations pass `--output-dir <agent>/.brain --output-name SESSION_TALE.md` — now pack-native
- All 4 agent settings.json migrated from loose hook path to this pack
- Loose hook retires to `Documents/_BACKUP` after migration confirms clean
- the maintainer (backport + migration); the builder (audit + authorization)

---

## v26.06.13_d1 (2026-06-13) — pack creation

- Packaged into `Claude-Code_Tail-Tales_v26.06.13_d1` at HE root
- `src/post_compact_shared.py` is the canonical script going forward
- Previous install path (`hooks/CLAUDE/tail-tales/post_compact_shared.py`) still live; deprecates once all agent hooks reroute
- the maintainer (owner)

---

## post_compact_shared.py — history

### 2026-06-11 — safety-review hardening

- Failures when `cwd` is missing now emit to stderr only (no workspace to log into)
- All other failures (missing transcript, bad write) log to `last_session_tail.err.log` in the agent workspace
- Ensures next-instance sees failures rather than them vanishing silently

### 2026-06-10 — Shared script, runtime-payload-as-source-of-truth

Origin event: the builder's per-agent script silently captured a week-stale tail because `PROJECTS_DIR` still pointed at the old workspace path. Four identical per-agent scripts (`post_compact_<agent>.py`, `post_compact_<agent>.py`, `post_compact_<agent>.py`, `post_compact_<agent>.py`) collapsed into one shared script that reads `transcript_path` and `cwd` from the PostCompact stdin payload instead of hardcoded constants.

### Bug 1 — hookSpecificOutput emits SessionStart not PostCompact

**Symptom:** `additionalContext` silently dropped; next-agent never gets the tail notice.  
**Root cause:** Claude Code's schema validator rejects `PostCompact` as a valid `hookEventName` in `hookSpecificOutput`. Only `SessionStart` is accepted.  
**Fix:** Output `hookEventName: "SessionStart"` even though this is a PostCompact hook. The notice text is injected; Claude Code doesn't care that the event name doesn't match the hook type.  
**Discovered:** 2026-06-03 (the maintainer). Preserved in comments in the script.

### Pre-2026-06-10 — Per-agent scripts

Four separate scripts, each with hardcoded `PROJECTS_DIR` and `OUTPUT` paths. Worked until the workspace moved; then silently captured stale tails. Archived at `hooks/CLAUDE/tail-tales/archive/`.
