# Tool Card: Claude Code Discord Bot-Filter Patcher

## What it does

Scans local Claude Code Discord plugin copies and applies a reviewed allowlist-aware replacement for the stock blanket bot-message filter.

## Command

```text
python src/patch_discord_bot_filter.py [--dry-run] [--no-home-scan] [EXTRA_ROOT ...]
```

## Inputs

| Input | Required | Meaning |
|---|---:|---|
| `--dry-run` | no | Report recognized state without writing. |
| `--no-home-scan` | no | Exclude default `~/.claude*` roots; use explicit roots only. |
| `EXTRA_ROOT` | no | Add an existing Claude configuration root to the scan. |

## Returns

One status line per discovered `server.ts`, a count summary, and a process exit code. Refused, invalid-option, or error states are nonzero.

## Safety

- Reads: recognized installed Discord plugin source.
- Writes: one exact block in recognized `server.ts` files when not in dry-run mode.
- Network: none.
- Credentials: none.
- Unknown source variants: refused without write.

Use `SKILL.md` for the operating procedure and `!INSTALL.md` for setup and rollback.
