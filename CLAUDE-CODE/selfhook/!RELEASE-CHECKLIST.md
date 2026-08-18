# Release checklist — Selfhook

Candidate root: `<PACKAGE_ROOT>`

Do not mark an item complete without a reproducible command result or artifact.

## Package surface

- [ ] Candidate root and tracked file list are recorded.
- [ ] `config/tool.json` parses and matches package entrypoints.
- [ ] Python source compiles without syntax errors.
- [ ] `tests/identity_directory_tests.py` passes from the packaged location.
- [ ] Example configuration parses and fails only for its intentional `<WORKSPACE>` placeholder.
- [ ] Package documentation describes only current configuration, runtime behavior, dependencies, installation, verification, and failure boundaries.

## Configuration contract

- [ ] Valid configuration renders one JSON hook payload.
- [ ] Invalid JSON, unknown keys, missing required keys, duplicate slugs, invalid field types, and invalid events produce error-only output.
- [ ] Absolute, parent-traversal, symlink-escaping, absent, and directory targets are rejected.
- [ ] The checker rejects every configuration shape rejected by the hook.
- [ ] The checker exits nonzero for an over-limit configured file.
- [ ] A payload exceeding the budget includes an in-budget cut marker.

## Lifecycle registration

- [ ] The settings fragment parses as JSON.
- [ ] SessionStart, PostCompact, and PreCompact registrations use absolute package paths and intended arguments.
- [ ] The PreCompact command uses `identity_directory.py --config … --write --quiet`.
- [ ] A marker-ready `MEMORY.md` generation preserves its prefix/suffix bytes, omits depth-2 bait, and lists direct child folders by name.
- [ ] A headless runtime receipt records the expected workspace cwd and a hook response.

## Uninstall

- [ ] Removing registrations before the package directory produces a valid settings file.
- [ ] A post-uninstall runtime receipt contains no Selfhook hook response.
- [ ] Configured file hashes are unchanged by install and uninstall tests.

## Release boundary

This checklist verifies the package's technical contract. A completed checklist does
not certify untested runtime versions or local configurations not represented by the
recorded receipts.
