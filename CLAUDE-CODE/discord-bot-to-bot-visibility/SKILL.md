---
name: claude-code-discord-bot-filter-patcher
description: Preview, apply, verify, or troubleshoot the local Claude Code Discord bot-filter compatibility patch.
version: v26.08.21_d1
substrate: claude-code
---

# Claude Code Discord Bot-Filter Patcher

## Use when

- An explicitly allowlisted Discord bot sender is dropped before the Claude Code Discord access gate.
- An official Discord plugin refresh may have restored the stock blanket bot filter.
- The package's current source state needs a dry-run verification.

## Procedure

1. Run `python src/patch_discord_bot_filter.py --dry-run`.
2. Read every discovered path and state.
3. If every state is recognized, run without `--dry-run`.
4. Re-run dry-run and confirm `already` for every target.
5. Restart Claude Code before testing Discord delivery.

Use `--no-home-scan` with explicit fixture roots for tests. It prevents fixture commands from also scanning live `~/.claude*` directories.

## Stop conditions

- Any `refused (...)` result.
- Any read/write error.
- A nonzero exit code.
- An unexpected plugin path or source variant.

On a stop condition, do not edit the plugin by guesswork. Record the path and status, compare it with the current official source, and update the package through review.

## Access configuration

The patcher does not choose trusted bot IDs. The operator uses the official command separately:

```text
/discord:access allow <DISCORD_BOT_USER_ID>
```

## Limits

- Windows runtime tested.
- POSIX runtime unverified.
- No network or credential access.
- No automatic backup.
