# Selfhook — Claude Code lifecycle-hook multiplexer

## Function

Selfhook registers one command for Claude Code `SessionStart` and `PostCompact`
events. It reads a JSON configuration and emits one bounded `additionalContext`
payload containing ordered, banner-separated sections with short text and file
pointers. It never injects pointed-at file contents.

`src/check_limits.py` reads the same configuration and can be wired into a commit or
sync step to enforce configured character limits.

## Package contents

```text
src/selfhook.py                  lifecycle hook and section renderer
src/check_limits.py              config and character-limit validator
config/continuity.example.json   configuration template
```

## Requirements

- Claude Code with lifecycle-hook support.
- Python 3.8 or later available to the runtime.
- A configured workspace and a set of existing workspace-relative files.

## Install and verify

Follow `!INSTALL.md` for configuration, hook registration, checker wiring, and
runtime verification. Run `tests/SMOKE_TESTS.md` after installation.

## Operational boundaries

- The hook emits pointers and does not read or inject the pointed-at file contents.
- The hook cannot determine whether a runtime subsequently opens a listed file.
- Character limits are enforced only when `check_limits.py` is wired into a local
  workflow.
- Every configuration error produces an error-only payload; Selfhook does not render
  a valid subset of an invalid configuration.
- The payload budget is 1,800 characters. It is intentionally below an observed
  runtime delivery limit and must be re-tested if the runtime changes.

## Status

The package has automated and headless-install receipts in
`tests/release-receipt.json`. See `!RELEASE-CHECKLIST.md` for the technical release
criteria and `!BUGS.md` for runtime constraints.
