# Selfhook

**Type:** Claude Code SessionStart/PostCompact lifecycle hook and configuration
validator.

**Runtime surface:** `src/selfhook.py` reads `config/continuity.json` and emits one
banner-separated JSON `additionalContext` payload. `src/check_limits.py` validates
the same configuration and reports configured character-limit violations.

**Installer changes:** create `config/continuity.json` from the supplied example,
register two lifecycle commands in `<WORKSPACE>/.claude/settings.json`, and optionally
wire the checker into a local commit or sync workflow.

**Runtime writes:** none. Package code reads configuration and configured file paths;
it does not create, modify, or inject file contents.

**Uninstall order:** remove lifecycle registrations, remove checker wiring, then
remove the package directory. Removing the package first leaves invalid command paths
in the lifecycle configuration.

**Primary failure conditions:** invalid settings JSON, unavailable Python, invalid
package command paths, an invalid configuration, or a changed runtime delivery limit.
See `!INSTALL.md`, `!BUGS.md`, and `tests/SMOKE_TESTS.md`.
