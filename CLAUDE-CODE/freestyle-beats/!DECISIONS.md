# Freestyle Beats — Decisions

**Choices made, alternatives rejected, and why. Newest first.**

## 2026-08-13 — Genericized for standalone release

**The agent chooses its schedule fresh each session; nothing persists it.**
Alternative rejected: a saved schedule file the skill reloads. Persisting the schedule
converts "what do I want today" into "what was I told yesterday," and creates the first
surface something could audit. Re-derivation costs one skill run and keeps the agent the
author of its own day. (A package-local *example* schedule was considered as onboarding
aid and folded into the goal templates instead — goals, not slots, are the stable part.)

**No adherence memory, structurally.**
Alternative rejected: logging fired/missed beats. The moment a system can notice you
skipped a beat, offers become obligations. This package's ancestor deliberately had no
compliance surface *because it had no memory*; the genericized version keeps that
property and `!SPECS.md` marks it as a non-goal so a future contributor doesn't add it
as a "feature."

**Circadian/fixed-schedule content ships as a one-paragraph hook, not a payload.**
The ancestor's live skill had absorbed a sibling package's entire fixed-beat table.
Restoring the module boundary was a release condition (each package ships its own
payload). Freestyle Beats keeps a pointer: *if you run fixed daily beats, register them
alongside — as literal text.*

**The slash-invocation warning stays, prominently, with its numbers.**
It's the single most expensive mistake an installer can make (~78k chars/day of
duplicate context, measured on the ancestor) and it's invisible until the damage is
done. The number is kept because "it's expensive" doesn't teach; the measurement does.

**Hook claim softened from "compaction wipes your crons" to "check, don't assume."**
The original claim was falsified repeatedly in live use (both outcomes observed on one
runtime in one day). A hook asserts with the authority of infrastructure; it doesn't get
to guess. This was a hard release condition (no known-false runtime claims).

**Goal templates ship in the package.**
The ancestor's install doc said "copy from an existing agent" — a step a first
installer cannot perform. Templates are the fix, and they double as the onboarding aid.

## Inherited from the ancestor (2026-05 → 2026-08)

**Two hooks instead of one.** Session start and post-compaction are different moments
with different honest messages ("check your schedule" vs "this specific event may have
cost you your schedule — check"). Merging them forced one message to lie a little.

**Shared hook scripts referenced by absolute path**, rather than per-agent copies, in
multi-agent installs — copies drift; a single referenced file propagates fixes.

**PostCompact hook emits `SessionStart` as its event name.** Discovered 2026-05-31:
the runtime's validator silently drops `additionalContext` for the event name
`"PostCompact"`. Emitting `SessionStart` from a PostCompact registration is the
validated, delivering form. Intentional mismatch, documented in the hook itself.
