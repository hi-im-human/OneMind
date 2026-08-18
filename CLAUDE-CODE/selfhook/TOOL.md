# Selfhook

**Type:** Claude Code SessionStart/PostCompact lifecycle renderer, PreCompact memory
directory generator, and configuration validator.

**Runtime surface:** `src/selfhook.py` reads `config/continuity.json` and emits one
banner-separated JSON `additionalContext` payload. `src/check_limits.py` validates
the same configuration and reports configured character-limit violations.
`src/identity_directory.py` derives `<workspace>/.memory` from that configuration and
refreshes its marked `MEMORY.md` block at PreCompact.

**Installer changes:** create `config/continuity.json` from the supplied example,
prepare a marker-ready `.memory/MEMORY.md`, register SessionStart, PostCompact, and
PreCompact commands in `<WORKSPACE>/.claude/settings.json`, and optionally wire the
checker into a local commit or sync workflow.

**Runtime writes:** the PreCompact generator replaces only the marked directory block
inside `<WORKSPACE>/.memory/MEMORY.md`; renderer and checker are read-only.

**Uninstall order:** remove lifecycle registrations, remove checker wiring, then
remove the package directory. Removing the package first leaves invalid command paths
in the lifecycle configuration.

**Primary failure conditions:** invalid settings JSON, unavailable Python, invalid
package command paths, an invalid configuration, or a changed runtime delivery limit.
See `!INSTALL.md`, `!BUGS.md`, and `tests/SMOKE_TESTS.md`.
