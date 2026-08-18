# Install — Selfhook

## Placeholders

- `<PACKAGE_ROOT>`: absolute location of this package.
- `<WORKSPACE>`: absolute Claude Code workspace path containing `.claude/`.

## Install

1. Copy `config/continuity.example.json` to `config/continuity.json`.
2. Set `workspace` to an absolute existing path. Update each section and cap so every configured path exists beneath that workspace.
3. Register the command under both `SessionStart` and `PostCompact` in `<WORKSPACE>/.claude/settings.json`.
4. Optionally wire `src/check_limits.py` into a commit or sync workflow.

```json
"hooks": {
  "SessionStart": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \"<PACKAGE_ROOT>/src/selfhook.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --event SessionStart" }] }],
  "PostCompact": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \"<PACKAGE_ROOT>/src/selfhook.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --event PostCompact" }] }]
}
```

Use doubled backslashes in Windows JSON paths.

## Generated or changed paths

| Path | Change |
|---|---|
| `<PACKAGE_ROOT>/config/continuity.json` | created from the example |
| `<WORKSPACE>/.claude/settings.json` | two lifecycle registrations |
| local commit/sync configuration | optional checker invocation |

The package does not modify configured files at runtime.

## Verify

1. Run syntax and configuration validation:

   ```text
   python "<PACKAGE_ROOT>/src/selfhook.py" --config "<PACKAGE_ROOT>/config/continuity.json" --event SessionStart
   python "<PACKAGE_ROOT>/src/check_limits.py" --config "<PACKAGE_ROOT>/config/continuity.json"
   ```

2. Start Claude Code from `<WORKSPACE>` and run smoke test 6 in `tests/SMOKE_TESTS.md`.
   The receipt must show both `init.cwd` equal to `<WORKSPACE>` and a Selfhook
   `hook_response` payload.

## Uninstall

1. Remove the two registrations from `<WORKSPACE>/.claude/settings.json`.
2. Remove any local checker invocation.
3. Remove `<PACKAGE_ROOT>`.

Removing the package before its registrations leaves invalid lifecycle command paths.
