# Tail Tales — Technical specification

## Invocation

```text
python src/post_compact_shared.py [--output-dir PATH] [--output-name NAME] [--agent LABEL]
```

The command reads one Claude Code PostCompact JSON payload from stdin. It uses the
payload `transcript_path` and `cwd`; it does not use a hardcoded workspace path.

## Extraction contract

- The most recent compaction boundary is the lower bound for extraction.
- The output contains at most 40 conversational turns after that boundary.
- Text content is included; reasoning, tool calls, scheduled prompts, and runtime
  markup are excluded.
- Channel envelopes are unwrapped before message classification.
- Consecutive identical same-speaker messages are collapsed with a repeat count.
- Timestamps use the runtime machine's local time.

## Output contract

- Default output name: `last_session_tail.md` in the runtime cwd unless overridden.
- Typical installed output: `<WORKSPACE>/.brain/SESSION_TALE.md`.
- `HARD_CAP` is 30,000 characters.
- A cap preserves the document header and newest body content and emits a trim marker.
- Successful processing writes one Markdown file and exits 0.

## Failure contract

- Missing `cwd`: write a diagnostic to stderr and exit 0.
- Missing transcript path, missing transcript file, parse failure, write failure, or no
  extractable turns with a known cwd: append a diagnostic to
  `<cwd>/last_session_tail.err.log` and exit 0.
- No extractable turns never replaces an existing output file.
- Unknown command-line flags are accepted by the current parser and ignored. Do not
  use undeclared flags as configuration.

## Non-goals

- Context injection.
- Transcript archiving beyond the one configured tail file.
- Network access, credentials, schedule management, or file-reader registration.
