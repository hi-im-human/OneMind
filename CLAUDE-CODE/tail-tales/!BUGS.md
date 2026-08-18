# Tail Tales — Known issues

## Open

- **Unknown CLI flags are ignored by the current parser.** Audit registrations against
  the supported option list in `!SPECS.md`.
- **Failures exit 0.** Diagnostics are written to the cwd error log when available;
  no hook payload is emitted.
- **Live PostCompact delivery is runtime-dependent.** The repository test suite uses
  synthetic stdin and does not replace a target-runtime receipt.
- **The tail is overwritten on each successful run.** It is not an archive.

## Resolved behavior covered by tests

- Empty extraction does not replace an existing tail.
- Post-boundary selection excludes earlier transcript windows.
- Channel envelopes are unwrapped before classification.
- Output capping preserves the newest content and emits a trim marker.
- Missing output directories are created by the hook.
