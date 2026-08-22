---
description: Claude Code Discord-plugin patcher that preserves self and unknown-bot filtering while allowing explicitly allowlisted bot messages to reach the existing access gate.
---
# Claude Code Discord Bot-to-Bot Visibility Package

**Version:** `v26.08.21_d1`  
**Status:** portable compatibility patch for recognized official plugin source shapes; validation evidence is recorded in `!RELEASE-CHECKLIST.md` and `tests/release-receipt.json`

The official Claude Code Discord plugin currently drops every bot-authored message at the start of `messageCreate`, before the configured access gate runs. This package applies a narrow local patch: the receiving bot's own messages remain blocked, unknown bot senders remain blocked, and explicitly allowlisted bot IDs may continue to the plugin's existing gate.

The patcher scans installed Discord plugin copies, recognizes only documented source shapes, and refuses unfamiliar or mixed variants. It does not edit `access.json`, Discord credentials, or plugin settings.

## Audience

This package is for Claude Code Discord-plugin operators who need messages from explicitly allowlisted Discord bot accounts to reach the normal plugin gate.

## Quick start

1. Place `src/patch_discord_bot_filter.py` at a stable local path. It requires Python 3.9 or newer and uses only the standard library.
2. Preview and apply:

   ```text
   python src/patch_discord_bot_filter.py --dry-run
   python src/patch_discord_bot_filter.py
   ```

3. Add each permitted sender bot's Discord user ID with the official plugin command:

   ```text
   /discord:access allow <DISCORD_BOT_USER_ID>
   ```

4. To re-run the patch after plugin refreshes, merge the `SessionStart` entry from `hook-snippet.settings.json` into the applicable Claude Code `settings.json` and replace the example script path.

The default command scans directories matching `~/.claude*`. For fixture or bounded-root work, pass `--no-home-scan` plus each intended root.

## Output states

- `patched` — one recognized stock block was changed.
- `upgraded` — one recognized earlier Hearthwell patch block was replaced by the current block.
- `already` — the current patch block was already present.
- `would be patched` / `would be upgraded` — dry-run result; no write occurred.
- `skipped (unfamiliar)` — the source shape was unfamiliar, mixed, or duplicated; no write occurred and the process exits 2.
- `error ...` — a read or write failed; the process exits 1.
- Unknown `--...` option — no discovery or write occurs; the process exits 3.

## Scope and limitations

- Verified on Windows.
- The path logic uses `pathlib`; POSIX behavior has not been runtime-tested for this release.
- Plugin updates may restore stock source. The optional `SessionStart` hook rechecks recognized copies and reports nonzero when a source shape requires inspection.
- This is a local compatibility patch, not an official Anthropic package.

## Important files

- `src/patch_discord_bot_filter.py` — patch applicator.
- `hook-snippet.settings.json` — mergeable Claude Code hook example.
- `!INSTALL.md` — setup, verification, and rollback.
- `!SPECS.md` — exact recognition and authorization contract.
- `tests/SMOKE_TESTS.md` — clean and failure-control matrix.

## Provenance

Original local patch: 2026-05-19. Auto-patcher: 2026-05-22. Portable applicator: 2026-08-21. Copyright and contribution attribution is recorded in `NOTICE`. Related upstream report: [`anthropics/claude-plugins-official#1559`](https://github.com/anthropics/claude-plugins-official/issues/1559).
