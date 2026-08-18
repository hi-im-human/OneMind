# Tail Tales — Technical decisions

- **Runtime payload paths:** use `transcript_path` and `cwd` supplied at invocation;
  do not store workspace-specific source paths in package code.
- **Post-boundary extraction:** retain only turns after the latest compaction marker.
- **Text-only capture:** exclude reasoning, tool, scheduled-prompt, and runtime
  markup entries from the Markdown tail.
- **Envelope-first parsing:** unwrap channel envelopes before applying metadata-based
  classification.
- **Non-destructive empty input:** return before output replacement when no turns
  extract.
- **Newest-first cap retention:** when output exceeds `HARD_CAP`, preserve the header
  and content closest to the current boundary.
- **No lifecycle injection:** writing a tail and injecting a large payload are separate
  operations; this package performs the write only.
