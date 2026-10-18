# Tail Tales — Technical decisions

- **Runtime payload paths:** use `transcript_path` and `cwd` supplied at invocation;
  do not store workspace-specific source paths in package code.
- **Post-boundary extraction:** retain only turns after the latest compaction marker.
- **Text-only capture:** exclude reasoning, tool, scheduled-prompt, and runtime
  markup entries from the Markdown tail.
- **Outgoing channel replies are speech, not volume:** the text-only rule treats tool
  calls as volume, but a `mcp__<server>__reply` call's `text` is the agent's actual words
  on a chat bridge. Without it, the tale kept only the agent's terminal note *about* a
  reply. Only reply tools are admitted, and they are labelled `(sent)` so they cannot be
  mistaken for terminal-only notes. (Margin, 2026-10-18, requested by the owner.)
- **Envelope-first parsing:** unwrap channel envelopes before applying metadata-based
  classification.
- **Non-destructive empty input:** return before output replacement when no turns
  extract.
- **Newest-first cap retention:** when output exceeds `HARD_CAP`, preserve the header
  and content closest to the current boundary.
- **No lifecycle injection:** writing a tail and injecting a large payload are separate
  operations; this package performs the write only.
