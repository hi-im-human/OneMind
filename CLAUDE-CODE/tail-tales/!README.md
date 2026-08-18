# Tail Tales — Claude Code PostCompact transcript-tail hook

## Function

Tail Tales runs on a Claude Code `PostCompact` event. It reads the runtime-supplied
transcript path, selects conversational text after the most recent compaction
boundary, and writes a bounded Markdown tail file.

The hook writes a file only. It does not inject the file into a later context or
register a SessionStart command.

## Runtime behavior

- Reads `transcript_path` and `cwd` from the lifecycle payload.
- Writes the most recent 40 conversational turns after the last compaction boundary.
- Excludes reasoning blocks, tool calls, scheduled prompts, and runtime markup.
- Unwraps relayed channel messages before classifying their payload.
- Collapses consecutive identical messages from the same speaker.
- Uses a 30,000-character output cap. When capped, it preserves the header and newest
  content and marks the result as trimmed.
- On invalid or empty input, exits successfully without replacing an existing tail and
  writes diagnostic output to `last_session_tail.err.log` when a workspace is known.

## Requirements

- Claude Code with `PostCompact` hooks.
- Python 3.8 or later on the runtime PATH.
- A writable output directory.

No network service, credentials, database, or companion package is required.

## Package contents

```text
src/post_compact_shared.py     PostCompact hook
config/tool.json               package manifest
!INSTALL.md                    install, verification, and uninstall
!SPECS.md                      input/output and failure contract
tests/                         synthetic-payload regression suite
```

## Verification boundary

Run `python tests/smoke_test.py` from the package root for synthetic-payload coverage.
A synthetic test does not verify delivery from a live Claude Code `PostCompact` event;
record a real runtime receipt separately.
