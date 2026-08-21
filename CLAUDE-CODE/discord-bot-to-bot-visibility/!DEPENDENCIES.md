# Dependencies

## Paths read

Default scan roots:

```text
~/.claude*
```

Per-root plugin paths:

```text
plugins/cache/claude-plugins-official/discord/*/server.ts
plugins/marketplaces/claude-plugins-official/external_plugins/discord/server.ts
```

Additional existing directories may be passed as positional arguments.

## Paths written

- Recognized Discord plugin `server.ts` files discovered through the paths above.
- No other path is written by the Python applicator.

## Tools and runtimes called

- Python 3.9 or newer.
- Python standard library: `pathlib`, `re`, `sys`.
- Claude Code executes the optional SessionStart command when the hook is installed.

## Configuration sources

- User home from `Path.home()`.
- Positional scan roots from the command line.
- `--dry-run` from the command line.
- `--no-home-scan` from the command line.
- Official plugin access policy remains in its own `access.json`; the patcher does not read or modify that file directly.

## Consumers

- Installed official Claude Code Discord plugin processes consume the modified `server.ts` files after restart.
- Operators and SessionStart hooks consume the patcher's text output and exit code.

## Triggers

- Manual command invocation.
- Optional Claude Code `SessionStart` hook from `hook-snippet.settings.json`.

## Network and credentials

- The patcher makes no network call.
- The patcher reads no Discord token, API key, OAuth credential, or `.env` file.

## Platform verification

- Windows: tested.
- POSIX: path design present; runtime unverified in this release.
