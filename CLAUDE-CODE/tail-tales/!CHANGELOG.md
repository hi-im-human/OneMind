# Changelog — Tail Tales

## Unreleased

- Outgoing channel replies are now kept: the `text` of `mcp__<server>__reply` tool calls is
  written as `<agent> (sent):` turns. Other tool calls stay excluded. Smoke case 16 covers it,
  and it was verified red on the previous hook and green on this one.

- Documentation rewritten as technical package documentation.
- Release checklist reduced to executable surface, regression, runtime, and uninstall checks.

## 1.0.0

- Claude Code PostCompact transcript-tail writer.
- Runtime-payload transcript selection, post-boundary extraction, and bounded Markdown output.
- Non-destructive empty-input handling and cwd-based diagnostic logging.
