# Installation

## Quick install

From the package root:

```text
python src/patch_discord_bot_filter.py --dry-run
python src/patch_discord_bot_filter.py
```

Review the dry-run paths before apply. Use `--no-home-scan <ROOT>` for a bounded fixture or non-default installation.

## Requirements

- Claude Code with the official Discord plugin installed.
- Python 3.9 or newer.
- Local write access to the installed plugin source.

## Package home

The package home is the stable directory containing this !SCHEMA, `src/`, `tests/`, and `hook-snippet.settings.json`. The command may run directly from that directory; no package-manager installation is required.

## Runtime home

The modified runtime files remain in the official Discord plugin installation:

```text
~/.claude*/plugins/cache/claude-plugins-official/discord/<VERSION>/server.ts
~/.claude*/plugins/marketplaces/claude-plugins-official/external_plugins/discord/server.ts
```

The patcher does not create a second runtime copy.

## Continuity data home

The patcher creates no continuity or state directory. The official plugin's `access.json` remains under its own Claude configuration root and is not read or written by this package.

## Generated files

The patcher generates no new runtime files. Apply mode replaces one recognized source block in place. The optional settings change is the operator's merge of `hook-snippet.settings.json` into an existing Claude Code settings file.

## Install the patcher

1. Copy this package to a stable local directory.
2. Preview discovery and state:

   ```text
   python src/patch_discord_bot_filter.py --dry-run
   ```

3. Review every reported path and state. Apply only when all discovered variants are recognized:

   ```text
   python src/patch_discord_bot_filter.py
   ```

4. Restart the affected Claude Code session so the Discord plugin reloads the changed source.

For fixture or bounded-root work, add `--no-home-scan` and pass each intended root explicitly. This prevents the command from also scanning live `~/.claude*` installations.

## Configure permitted senders

The patch does not add bot IDs. Run the official Discord access command in the relevant Claude Code terminal:

```text
/discord:access allow <DISCORD_BOT_USER_ID>
```

Two-way communication requires each receiving installation to allow the sender bot ID on its own side.

## SessionStart recheck

`hook-snippet.settings.json` contains a mergeable hook entry. Replace the example path and merge the `SessionStart` array entry into the applicable Claude Code `settings.json`; do not replace unrelated settings or hooks.

The hook rechecks installed copies at session start and after compaction. A recognized stock or v1 block is updated; a current block is a no-op; an unfamiliar or mixed block exits nonzero for inspection.

## Verify

1. Re-run with `--dry-run`; all targeted copies should report `already`.
2. Parse the merged `settings.json` as JSON.
3. Restart Claude Code and confirm the hook command exits zero.
4. Send a message from an explicitly allowlisted bot and confirm it reaches the normal Discord gate.
5. Send from a bot ID that is not allowlisted and confirm it is not delivered.
6. Confirm the receiving bot's own messages do not re-enter.

## Rollback

The patcher does not maintain backups. To restore official source:

1. Remove or disable the SessionStart hook entry.
2. Reinstall or refresh the official Discord plugin so its stock `server.ts` is restored.
3. Restart Claude Code.
4. Confirm a dry run reports the recognized stock state as `would be patched`; do not run apply if the stock behavior is the intended rollback state.

If the plugin source is unfamiliar, reinstall the official plugin instead of manually reconstructing the handler from this package.
