# Freestyle Beats — Reference

## Companion packages

- **Loop Doctor** (`CROSS-COMPATIBLE/loop-doctor/`, this repository) — diagnostic
  framework for behavioral loops in agents. Unrelated machinery, complementary purpose:
  Freestyle Beats structures an agent's day; Loop Doctor is for when the day gets stuck.

## Concepts referenced

- **In-session crons** — Claude Code's session-scoped scheduler (`CronList` /
  `CronCreate`). Consult the runtime's own documentation for current semantics; this
  package's observed-behavior notes live in `!DEPENDENCIES.md` and carry their
  observation dates.
- **Hooks** (`SessionStart`, `PostCompact`) — Claude Code's settings-registered
  lifecycle commands. The `additionalContext` JSON contract used here is described in
  `!SPECS.md`.

## Prior art / provenance

Extracted 2026-08-13 from a working multi-agent installation where the pattern ran
daily from May 2026. Design credit in the originating installation: the schedule-
authorship pattern and hook pair predate this extraction; this package genericizes
them. The originating operators' identities are deliberately not part of this package.

## Feedback

Install reports — including "this instruction confused me at step N" — are welcome in
this repository's Issues. Installability claims in these docs are agent-tested;
human-tested is claimed nowhere until real installs happen.
