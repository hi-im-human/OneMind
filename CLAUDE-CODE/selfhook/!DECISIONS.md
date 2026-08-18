# Selfhook — Technical decisions

## Configuration and execution

- **Sections are configuration, not source edits.** A section is defined by
  `slug`, `header`, optional `events`, optional `text`, and optional `read_files`.
  Configuration order is render order.
- **No executable section source.** Section payloads contain static text and file
  pointers only. Executable section sources would add an unreviewed execution path
  and make the payload size nondeterministic.
- **One lifecycle renderer.** Installers can add sections to one payload rather than
  registering multiple commands for the same event.
- **Strict configuration validation.** Unknown keys, duplicate slugs, malformed
  sections, invalid paths, and budget errors produce explicit configuration errors.
- **Fail closed for character caps.** The hook and checker use the same validation
  path. Missing, malformed, or unreadable cap targets fail validation instead of
  disabling enforcement.

## File and path contract

- The workspace path is absolute and existing.
- Listed and capped paths are workspace-relative, resolve beneath the workspace, and
  must target regular files.
- Glob patterns list every match in sorted order; Selfhook does not select an
  arbitrary first match.

## Delivery contract

- Selfhook emits one JSON output object.
- Both registered lifecycle commands emit `hookEventName: "SessionStart"`; the
  command-line `--event` argument selects sections. This is a compatibility
  workaround for a verified runtime behavior.
- The additional-context payload is capped at 1,800 characters and includes an
  in-budget cut marker when shortened.
