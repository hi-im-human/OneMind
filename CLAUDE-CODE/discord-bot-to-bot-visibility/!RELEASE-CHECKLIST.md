# Release checklist — Claude Code Discord Bot-to-Bot Visibility Package

Candidate root: the directory containing this file.

Complete each item from reproducible command output or an artifact produced during a clean fresh-agent run.

## Package surface

- [x] Candidate root and complete shipped-file list are recorded.
- [x] `config/tool.json` and `hook-snippet.settings.json` parse as JSON.
- [x] `SKILL.md` frontmatter contains a name and description.
- [x] Python source passes syntax and Python 3.9 grammar checks.
- [x] No forbidden cache, backup, credential, private-path, private-ID, or secret artifact is present.
- [x] Apache-2.0 declaration, `LICENSE`, `NOTICE`, and dependency review agree.

## Fresh-agent onboarding

- [x] A no-project-context agent used only `!README.md` and `!INSTALL.md` to create a clean package home.
- [x] Install paths, runtime paths, continuity-data behavior, generated files, and local costs were understood from package docs alone.
- [x] The clean run used `--no-home-scan` with an isolated fixture root and did not read or write live `~/.claude*` plugin files.
- [x] The settings hook example was merged into an isolated settings fixture and the resulting JSON parsed.

## Runtime and failure controls

- [x] Stock dry-run, stock apply, and second-run idempotence produced the documented states and preserved file tails.
- [x] All three recognized v1 variants upgraded to v2 and then reported `already`.
- [x] Unfamiliar, mixed, duplicate, and known-plus-unknown-handler fixtures were refused nonzero and remained byte-identical.
- [x] A misspelled unknown option exited 3 before discovery or write.
- [x] The emitted v2 TypeScript block contains self-drop/current-channel/parent-channel constraints and transpiles under Bun or an equivalent TypeScript parser.
- [x] A planted known-bad mutation made the independent test instrument fail.

## Uninstall and final gate

- [x] The clean fixture installation and settings fixture were removed without changing pre-existing files outside the clean test root.
- [x] `tests/release-receipt.json` records commands, paths, durations, claims, limitations, license review, and uninstall evidence.
- [x] The OneMind privacy scanner caught planted bait and then reported zero findings on the clean candidate.
- [x] `OneMind/_tools/release_gate.py` passed on the exact post-onboarding candidate.

## Release boundary

This checklist records one fresh-agent environment and one exact candidate. Windows is the tested runtime for this release; POSIX runtime remains unverified.
