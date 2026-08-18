# Tail Tales

**Type:** Claude Code PostCompact lifecycle hook.

**Input:** runtime JSON on stdin with a transcript path and workspace cwd.

**Output:** a bounded Markdown transcript tail at the configured output path; no hook
context injection and no network activity.

**Runtime writes:** the tail on successful extraction and an error log when a known
workspace permits diagnostics.

**Primary failure conditions:** unavailable Python, invalid command path or settings
JSON, absent or malformed lifecycle payload, unreadable transcript, unwritable output
path, and no extractable post-boundary turns.
