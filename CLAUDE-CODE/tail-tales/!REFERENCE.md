# Tail Tales — Reference

## Terms

- **Compaction boundary:** the most recent transcript marker separating the current
  context window from earlier content.
- **Tail:** the Markdown file containing selected conversational turns after that
  boundary.
- **Runtime payload:** the JSON data supplied to the PostCompact command, including
  `transcript_path` and `cwd`.

## Extension boundary

Tail Tales has no package dependency on other repository packages. A local
installation may arrange an independent reader or consumer for its output file.

## Technical support scope

Report reproducible installation, runtime payload, transcript parsing, output, or
verification findings through this repository's issue tracker.
