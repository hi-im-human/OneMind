---
name: tail-tales
description: Operation and verification procedure for Tail Tales PostCompact transcript-tail output.
---

# Tail Tales — Operating procedure

## Output handling

Tail Tales writes the configured tail file after successful PostCompact processing. It
does not inject that file into a later context. Configure any required reader outside
this package.

## Failure handling

- Missing or invalid input does not overwrite an existing tail.
- When a workspace is known, inspect `last_session_tail.err.log` for diagnostics.
- A missing output file requires a live PostCompact receipt and a check of the runtime
  payload path, command path, Python availability, and output-directory write access.

## Verification

Run `python tests/smoke_test.py` from the package root for synthetic input coverage.
For a target installation, trigger a real compaction and compare the output to the
post-boundary source transcript.
