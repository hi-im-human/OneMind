---
description: Claude Code lifecycle renderer, PreCompact shallow memory-directory generator, and configuration validator.
---

# Selfhook — Claude Code lifecycle hooks and memory directory generator

## Function

Selfhook reads one JSON configuration and provides two runtime components:

- `src/selfhook.py` renders bounded SessionStart/PostCompact pointer banners. It does
  not inject pointed-at file contents.
- `src/identity_directory.py` refreshes the marked directory block in
  `<workspace>/.memory/MEMORY.md` at PreCompact. It lists root files and top-level
  folders with their direct files/folders only; it does not recurse farther.

`src/check_limits.py` reads the same configuration and validates configured character
limits in a commit or sync workflow when the installer wires it there.

## Package contents

```text
src/selfhook.py                  lifecycle renderer
src/check_limits.py              config and character-limit validator
src/identity_directory.py        PreCompact MEMORY.md directory generator
config/continuity.example.json   configuration template
templates/MEMORY.md              marker-ready MEMORY.md for a new workspace
tests/identity_directory_tests.py generator regression suite
```

## Requirements

- Claude Code with lifecycle-hook support.
- Python 3.8 or later available to the runtime.
- A configured workspace with `.memory/`.
- A marker-ready `.memory/MEMORY.md`: use `templates/MEMORY.md` in a new workspace or
  add the marker pair after frontmatter in an existing file without replacing its
  other content.

## Install and verify

Follow `!INSTALL.md` for configuration, lifecycle registration, marker preparation,
and runtime verification. Run `tests/SMOKE_TESTS.md` after installation.

## Operational boundaries

- The renderer emits pointers and does not read or inject pointed-at file contents.
- The generator reads frontmatter only from indexed Markdown files and writes only the
  bytes between its marker pair in `MEMORY.md`.
- The generator derives `<workspace>/.memory` from Selfhook's validated configuration;
  it does not define a second file-list or memory-directory setting.
- Character limits are enforced only when `check_limits.py` is wired into a local
  workflow.
- Every configuration error produces an error-only renderer payload; the renderer does
  not render a valid subset of an invalid configuration.

## Status

Selfhook 1.1.0 is a candidate. The added generator requires its regression, install,
and runtime receipts before release. See `!RELEASE-CHECKLIST.md` and `!BUGS.md`.
