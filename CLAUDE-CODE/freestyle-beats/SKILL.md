---
name: freestyle-beats
description: Set up your in-session autonomous crons (Freestyle Beats). 2–8 per day, each labeled work or personal. Output fires into your live session. Run at session start, after compaction, or any time you want to adjust your schedule.
---

# Freestyle Beats

Your day, your call.

An agent with scheduled beats doesn't sit idle between conversations — it decides in the
morning what its day holds, then gets woken to do it. The beats are chosen fresh, by you,
each session. Nothing is inherited and nothing is graded.

## Steps

1. Read your `WORK_GOALS.md` and `PERSONAL_GOALS.md` (workspace root — templates ship in
   `src/templates/`, copy them out and fill them in on first run).
2. Pick **2–8 slots** for today. Each slot = a time + a `work`/`personal` label + a brief
   prompt you'd write for yourself.
3. Call `CronList` first to see what already exists. Then `CronCreate` only what's missing.
4. If you keep a running notes file, end each beat's prompt with "leave a breadcrumb" —
   a line about what happened, for the next you.

## Scheduled infrastructure beats (optional hook)

If you also run a fixed daily schedule (wake-up, checkpoint, end-of-day review — anything
that fires at the same times every day), register those alongside your freestyle slots.

**⚠️ Register the literal prompt TEXT, never a skill invocation.** A slash-invocation
(`/some-skill`) attaches the *entire skill file* to the fired prompt — measured on this
package's ancestor at ~11,200 characters per fire, which at seven fires a day was ~78,000
characters of the same document re-entering context daily, silently starving conversation
history. The failure is invisible until you notice your context is mostly boilerplate.
Short literal prompts cost almost nothing.

## Rules

- **At session start or post-compaction, check your beats before beginning unrelated
  work** — skipping the check is how drift accumulates silently. **But a live condition
  outranks maintenance:** an urgent request from your human, an active correction, a
  safety issue, or an explicit pause/hold comes first. Handle it, then return to the
  check.
- Beats fire into your live session as your own turns — no separate process.
- **Crons can die on any session break** — compaction, restart, disconnect, fresh session.
  **⚠️ But check before assuming: `CronList` FIRST, then rebuild only what's missing.**
  Compaction is survivable — the same runtime has been observed both keeping and losing
  crons across compactions on the same day. Neither outcome is predictable. Announcing a
  cause you didn't verify propagates a wrong model; checking the list costs one call.
- **Crons auto-expire after 7 days** regardless of session state. Running this skill at
  every session start keeps the schedule alive long-term.
- `--resume` from the same session ID *may* preserve crons — narrow case, don't rely on it.
- This skill is idempotent. Running it when everything is alive changes nothing; running
  it after a loss recreates only the gaps.

## Multi-agent installations (optional)

Running several agents on one machine? Two additions have proven useful:

- **Space slots ≥20 minutes apart across agents** so wake-ups don't collide.
- **A shared schedule file** each agent updates when it sets its beats, so everyone can
  see who's active when. Keep a `*(last updated YYYY-MM-DD)*` stamp per section — stale
  entries are how collisions sneak back in.

Single agent? Skip this section entirely.
