# Selfhook — Reference

## Companion packages (this repository)

- **Freestyle Beats** (`CLAUDE-CODE/freestyle-beats/`) — self-managed daily schedule.
  Currently ships its own two reminder hooks; its docs recommend combining same-event
  hooks. Its planned v1.1 removes those handlers and contributes a `schedule` section
  to Selfhook's config instead — Selfhook then owns the SessionStart/PostCompact
  events for the workspace.
- **Loop Doctor** (`CROSS-COMPATIBLE/loop-doctor/`) — diagnostic framework for
  behavioral loops. Unrelated machinery; a natural consumer if an installation wants
  a session-start pointer at its intake docs.

## Concepts referenced

- **Hooks / `additionalContext`** — Claude Code's settings-registered lifecycle
  commands. Contract and observed constraints in `!SPECS.md` and `!DEPENDENCIES.md`,
  with observation dates.
- **Pointer-not-payload** — the design premise; measured basis in `src/selfhook.py`'s
  docstring.

## Prior art / provenance

Extracted 2026-08-13 from a working multi-agent installation where the pointer model
and banner ran daily from 2026-07-31. The section/multiplexer generalization was
designed during packaging, against a hardening contract from the package's independent
reviewer. The originating operators' identities are deliberately not part of this
package.

## Feedback

Install reports and ambiguity notes are welcome in this repository's Issues.
Installability claims are agent-tested; human-tested is claimed nowhere until real
installs happen.
