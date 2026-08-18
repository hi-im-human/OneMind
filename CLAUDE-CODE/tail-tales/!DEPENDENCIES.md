# Tail Tales — Dependencies

## Required

| Dependency | Purpose | Behavior when unavailable |
|---|---|---|
| Claude Code PostCompact hooks | command delivery and lifecycle payload | package is inapplicable |
| Python 3.8+ on runtime PATH | executes the hook | no output file from the command |
| lifecycle `transcript_path` and `cwd` | source and diagnostic routing | no tail write |
| writable output directory | writes the tail | diagnostic when cwd is known |

## Local integration

The package does not register a reader for the output tail. Any process that opens or
consumes the file is local installation configuration and must be updated during
uninstall.

## Runtime reads and writes

**Reads:** package Python source, runtime stdin payload, and the runtime-supplied
transcript file.

**Writes:** one configured tail file on successful extraction and
`last_session_tail.err.log` on eligible failures.

## Observed runtime limitation

The synthetic test suite does not invoke a live PostCompact callback. Verify a target
runtime installation with an actual compaction receipt.
