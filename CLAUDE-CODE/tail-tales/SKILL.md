---
name: tail-tales
description: Read and use your session tale — the verbatim conversational turns written to disk at the last compaction boundary. Use after a compaction or session restart to recover the exact wording nearest the seam, which the compaction summary paraphrases away.
---

# Skill: Tail Tales

## Purpose

Recover what was actually said before the seam.

A compaction summary tells you what was decided. The tale tells you **how it was said** — the
user's literal words, your literal words, in order. Those are different things, and the second one
cannot be reconstructed from the first.

## Use when

- You have just compacted, and need the wording rather than the gist.
- You are resuming a session and the summary references something you cannot place.
- Someone refers to an earlier instruction or phrasing and you want the original, not a paraphrase.
- You are about to act on a remembered instruction that would be costly to get subtly wrong.

## Do not use when

- The current context already contains what you need.
- The work predates the last compaction — **the tale covers one window only** and is overwritten
  each time. Older material is gone from this file; go to whatever archive exists.
- You want a summary. The tale is not condensed and is not trying to be.

## How to use it

**Open the file and read it.** There is no tool call and no command. The path is set at install
time — commonly `<WORKSPACE>/.brain/SESSION_TALE.md`.

⚠️ **Nothing injects this file.** If your operating document tells you to read your tale after a
compaction, that instruction is the delivery mechanism — treat it as load-bearing, and do not
retire it on the belief that something else covers it. Nothing else does.

## Reading it well

1. **Check the header first.** It carries the write timestamp, the source transcript, and the turn
   count. **A tale can be present, well-formed, and drawn from the wrong session** — that is the
   specific bug this package was built after. If the timestamp is older than your last compaction,
   or the content does not match what you were doing, say so rather than working from it.
2. **Take the user's words as quoted, not as remembered.** They are reproduced verbatim. If your
   memory of an instruction differs from the tale, the tale is the record.
3. **Expect your reasoning to be absent.** Thinking blocks and tool calls are deliberately
   excluded. Their absence is not a gap in the record.
4. **`(×N)` means a message repeated consecutively** and was collapsed. The repetition was real.
5. **Do not treat the tale as complete history.** It is the last ~40 conversational turns of one
   window. Absence from the tale is not evidence something did not happen.

## Safety behavior

- Read-only. Never edit the tale — it is regenerated every compaction and edits are discarded.
- Do not quote it outward without checking whether the conversation it captures was private.
- If the tale is missing or empty, report that plainly. Do not reconstruct what you think it said.

## If it is missing or looks wrong

The file is written by a `PostCompact` hook. If it is absent, stale, or drawn from the wrong
transcript, check `last_session_tail.err.log` — ⚠️ in the **workspace root**, not beside the tale.

Silence from the hook means nothing was reported, not that nothing went wrong. Report the state and
let a human or a maintainer look; do not debug a continuity hook live in the session it protects.
