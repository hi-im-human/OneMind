# Tail Tales — a PostCompact hook that keeps what a summary throws away

When a Claude Code session compacts, what comes back is a summary. Summaries keep decisions and
drop wording. Tail Tales reads the transcript at the compaction boundary and writes the last ~40
conversational turns to a markdown file, **verbatim**, so the next context window can be handed
what was actually said rather than a paraphrase of it.

## ⚠️ It writes a file. It does not put anything into your agent's context.

This is the single most important thing to understand before installing it.

The hook fires, writes `SESSION_TALE.md`, and exits. **Nothing injects it.** If nothing causes the
agent to open that file, the install is silently useless — the hook succeeds, the file is correct,
and the agent receives nothing. Arranging the read is your job. See `!DEPENDENCIES.md`.

*(Injection existed once and was removed 2026-07-31: the hook transport truncates payloads far
below the size of a real tale, so injecting one was never reliable.)*

## One registration

| Event | Flag | Behaviour |
|---|---|---|
| `PostCompact` | *(none)* | read the transcript, write the tale |

That is the whole runtime. There is no `SessionStart` registration and no `--inject-only` flag;
both were removed 2026-07-31. ⚠️ Unrecognised flags are **silently accepted and ignored**, so a
stale registration looks healthy and does nothing — audit against the parser, not against docs.

## What it captures

- The last 40 **conversational** turns before the compaction boundary — the person's messages and
  the agent's replies.
- **Relayed messages are unwrapped and attributed to whoever actually sent them.** A message that
  arrives through a chat bridge is a person speaking; the envelope's `user` attribute names them,
  so a third party is never printed under the owner's name.
- Consecutive identical messages collapsed to one line with a `(×N)` count.
- Timestamps in the runtime machine's own local time.

The compaction boundary is used as the **cut point** — everything before the most recent one is
excluded. The boundary marker itself is not written into the tale.

**Deliberately excluded:** reasoning blocks, tool calls, scheduled/cron prompts, and runtime
markup. Reasoning is the most *reconstructable* material in the file — the same agent in the same
situation thinks approximately the same thoughts. The person's exact words cannot be regenerated
at all. When budget is scarce, keep the irreplaceable half.

> ### ⚠️ For a long time this package did the exact opposite of that last paragraph
>
> A filter meant to skip runtime markup tested `text.startswith("<")`. Every message relayed
> through a channel arrives wrapped in a `<channel …>` envelope — so the filter discarded **all**
> of them. Measured on one live transcript: **12,181 dropped.** Across four agents, every
> "owner" line that survived into a tale was a scheduled prompt. Not one was a person.
>
> The file whose header promises someone's exact words contained none of them, and had not for
> its entire existence. It kept the half that could have been rebuilt and destroyed the half that
> could not.
>
> Fixed 2026-08-15. **The rule that came out of it: a channel envelope is positive evidence of a
> person, and it outranks every machine heuristic. Unwrap first, then classify.** The first
> attempt at this fix got the order backwards and reproduced the bug, because the runtime marks
> relayed human messages with the same fields it puts on scheduled prompts.

## Size

**30,000 characters, enforced on the write path.** Over that, the **oldest** turns are dropped —
the material nearest the seam is what a returning agent needs, so it is the last thing to go. The
header always survives, and a trimmed tale says so in its own text.

There is one file and no second copy, so a silent trim would be indistinguishable from a quiet
session. Trims are announced.

## Why it exists

Compaction is the one real seam in an agent's continuity. What crosses it is a summary, and a
summary is a reconstruction. `SESSION_TALE.md` gives the next instance the actual fabric — the
sentences, in order, in the words they were said in.

## Design principles

- **Runtime-payload-as-source-of-truth.** `transcript_path` and `cwd` come from the hook's stdin
  payload at fire time. No hardcoded project paths. Move a workspace and it keeps working; add an
  agent and no source changes. *(This replaced per-agent scripts with hardcoded paths, which
  silently captured week-old transcripts after a workspace move — present, well-formed, wrong.)*
- **Agent label from `cwd`.** The basename with leading non-letter characters stripped, so
  `⚙️Ada` renders as `Ada`. Override with `--agent`.
- **No local configuration.** No timezone database, no network, no credentials, no other packages.
- **Failures never break the runtime.** Every failure path exits 0 and writes nothing rather than
  risking the session it is meant to protect. **The cost is that failures are invisible to the
  agent** — they go to a log file it has no standing reason to open. Silence from this package
  means *nothing was reported*, not *nothing went wrong*.
- **Non-destructive on bad input.** If no turns extract, the module returns *before* writing, so a
  broken transcript can never replace a good tale with an empty one.

## Files

```
src/post_compact_shared.py   ← the hook; registrations point here
config/tool.json             ← manifest
SKILL.md · TOOL.md           ← how an agent should read a tale
!INSTALL.md                  ← installation and verification
!DEPENDENCIES.md             ← ⚠️ the read you must arrange yourself
!SPECS.md · !DECISIONS.md    ← contracts, and why they are what they are
!BUGS.md · !CHANGELOG.md     ← known issues and history
tests/                       ← smoke suite; run it, don't trust this file
```

## Verifying an install

**Read the tale. Do not stat it.** A tale can exist, be recent, be well-formed, and be drawn from
the wrong transcript — that is the bug this package was built after, and a file-exists check would
not have caught it. Confirm the content matches what you were actually doing.
