# Selfhook

**What:** SessionStart + PostCompact continuity hook for a Claude Code agent — one
event multiplexer that renders named, banner-separated sections of instructions and
file *pointers* (never file contents), from one JSON config. Companion commit-time
checker enforces size caps on the pointed-at files.

**For:** any Claude Code agent whose continuity depends on actually reading its own
files at session start — and any household where multiple tools would otherwise pile
hooks onto the same events and blend into one unbounded, delimiter-free payload.

**Run:** nothing to run — the hook fires on session start and compaction once
registered. Maintenance surface is `config/continuity.json`; `SKILL.md` holds the
agent-side operating procedure.

**Surface:** two stateless Python scripts · one JSON config · no state.
**Three writers, all human/agent, none runtime:** you write the config (from the
example), you write two hook entries in `settings.json`, you wire the checker into
your pre-commit/sync. **Package code writes no files at runtime, ever.**
**Uninstall = remove the two hook entries from `settings.json` FIRST** (the
registrations are live consumers — delete the package before them and the hooks fail
invisibly), then the checker call, then the package home.

**Sharp edges:** hook spawn failure is invisible (no banner, no error — see Verify in
`!INSTALL.md`) · malformed `settings.json` kills all hooks silently · payload budget
is 1,800 chars because the transport truncates beyond ~2,000 *while reporting
success* · any config error renders an error-only payload — the hook never executes
a partial configuration while looking healthy.

**License:** Apache-2.0 (repository root).
