---
description: Runtime conversation-export archive, including configured Lumberjack output locations.
---

# .chat_logs/

Conversation-export archive.

## Lumberjack output

A configured Lumberjack installation writes daily Claude Code exports under
`.chat_logs/claude_code/`. Keep this directory and its source subdirectories in place
while that scheduled extractor is registered. Deleting or renaming the directory breaks
the configured output route.

The template does not install or register Lumberjack. Install and verify the extractor
separately before assuming automated export is active.

## Other exports

Store non-Lumberjack conversation exports in source-specific subdirectories such as
`claude_app/`, `letta/`, or `other/`. Keep source formats separate so an importer can
identify the expected parser.
