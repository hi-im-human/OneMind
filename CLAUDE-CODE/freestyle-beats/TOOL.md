# Freestyle Beats

**What:** Self-managed daily cadence for a Claude Code agent — 2–8 self-chosen,
self-prompted time slots per day, registered as in-session crons, kept alive by a
SessionStart and a PostCompact reminder hook.

**For:** Any Claude Code agent (or human/agent pair) that wants the agent to have a day
it authors, rather than a queue it drains.

**Run:** `/freestyle-beats` in a live session, after installing per `!INSTALL.md`.

**Surface:** one skill file · two stateless Python hooks · two goal-file templates.
**Package code writes no files at runtime**; the installer/user writes the documented
copies and two `settings.json` hook entries, and the agent creates in-session crons.
**Uninstall = remove both hook entries from `settings.json` first, then delete the
copied files and package home** (full sequence in `!INSTALL.md`).

**Sharp edges:** malformed `settings.json` kills all hooks silently · cron survival
across session breaks is unpredictable (the skill checks, never assumes) · never
register a skill invocation as a beat prompt — measured at ~78k chars/day of duplicate
context.

**License:** Apache-2.0 (repository root).
