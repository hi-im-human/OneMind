# Specifications

## Purpose

Patch recognized local copies of the official Claude Code Discord plugin so explicitly allowlisted bot senders may reach the plugin's existing access gate.

## Inputs

```text
python src/patch_discord_bot_filter.py [--dry-run] [--no-home-scan] [EXTRA_ROOT ...]
```

- `--dry-run` reports recognized state without writing.
- `--no-home-scan` excludes default `~/.claude*` roots and limits discovery to explicit roots.
- `EXTRA_ROOT` adds an existing directory to the default `~/.claude*` scan roots.
- Unknown `--...` options exit nonzero before discovery or write.

## Discovery contract

For each scan root, the patcher checks:

```text
plugins/cache/claude-plugins-official/discord/*/server.ts
plugins/marketplaces/claude-plugins-official/external_plugins/discord/server.ts
```

Discovery is recursive only where the glob contains `*`. Duplicate roots are removed by resolved path while preserving first-seen order.

## Source-state contract

The patcher recognizes three exact executable shapes:

1. **Stock** — the known unconditional `msg.author.bot` return followed by `handleInbound`.
2. **Hearthwell v1** — the earlier allowlist-aware block.
3. **Current** — unconditional self-message drop plus explicit top-level/current-channel allowlist check before `handleInbound`.

Exactly one known source block and exactly one `messageCreate` handler registration may be present in the file. A known block beside a second known or unknown handler is refused. Mixed, duplicate, or unfamiliar shapes are refused without a write.

## Authorization behavior

The current patch preserves these stages:

1. A message authored by the receiving Discord bot itself is dropped.
2. A message authored by another bot is dropped unless that bot's Discord user ID is explicitly present in the applicable `access.json` allowlist recognized by the patch block.
3. A bot that passes the early filter still enters `handleInbound` and the plugin's normal `gate()` logic. Channel policy, mention policy, and other access checks remain active.

For guild threads, the early filter checks the thread channel ID and its parent channel ID. Plain guild text channels check their own channel ID only; category IDs are not authorization scopes. The plugin's normal gate remains authoritative after this early filter.

## Writes

- Replaces one recognized block in each matching `server.ts` file.
- Does not modify `access.json`, `.env`, bot tokens, Claude settings, or Discord state.
- Uses UTF-8 text I/O.

## Exit behavior

- Zero: every discovered file was recognized and no read/write error occurred.
- Nonzero: an option was invalid, at least one discovered file was refused, or a read/write error occurred.
- No files found: reports the number of roots scanned and performs no write.

## Safety and failure boundaries

- Exact-shape recognition prevents edits to unknown upstream variants.
- Dry-run and apply use the same recognition path.
- The receiving bot's own messages remain blocked independent of allowlist configuration.
- A nonzero hook result signals that an installed plugin copy requires inspection.
- No automatic retry or source reconstruction occurs after refusal.

## Non-goals

- Installing or configuring the official Discord plugin.
- Creating Discord bot accounts or credentials.
- Editing `access.json` or choosing which bot IDs to trust.
- Replacing the official plugin gate.
- Patching non-Discord plugins.
- Claiming POSIX runtime verification in this release.
