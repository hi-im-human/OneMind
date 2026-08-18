# Release checklist — Tail Tales

Candidate root: `<PACKAGE_ROOT>`

Do not mark an item complete without a reproducible command result or artifact.

## Package surface

- [ ] Candidate root and tracked file list are recorded.
- [ ] `config/tool.json` parses and matches the Python entrypoint.
- [ ] Python source compiles without syntax errors.
- [ ] Package documentation contains only technical behavior, installation,
  configuration, dependencies, verification, and failure boundaries.

## Synthetic regression suite

- [ ] `python tests/smoke_test.py` exits 0.
- [ ] Empty extraction preserves a seeded existing output file.
- [ ] Post-boundary selection excludes earlier turns.
- [ ] Channel-envelope parsing preserves expected text and excludes runtime noise.
- [ ] Oversized output preserves the header and newest content with a trim marker.
- [ ] Missing output directories are created.
- [ ] Malformed timestamps and missing lifecycle fields follow the documented failure
  contract.

## Target runtime verification

- [ ] Target `settings.json` parses after registration.
- [ ] A real PostCompact event invokes the expected package command.
- [ ] Output is written at the configured path and matches the post-boundary source
  transcript.
- [ ] Failure diagnostics appear at the documented cwd error-log path when applicable.

## Uninstall

- [ ] Any local tail reader or consumer is removed or redirected.
- [ ] The PostCompact registration is removed and settings JSON remains valid.
- [ ] Package removal leaves no invalid command path.

## Release boundary

Synthetic coverage does not prove live PostCompact delivery. A release claim requires
a recorded target-runtime receipt.
