# Install — Tail Tales

## Placeholders

- `<PACKAGE_ROOT>`: absolute location of this package.
- `<WORKSPACE>`: absolute Claude Code workspace path containing `.claude/`.

## Install

1. Place the package in a stable location.
2. Add one `PostCompact` command to `<WORKSPACE>/.claude/settings.json`.
3. Configure any local process that should open or consume the written tail file.

```json
{
  "hooks": {
    "PostCompact": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "python \"<PACKAGE_ROOT>/src/post_compact_shared.py\" --output-dir \"<WORKSPACE>/.brain\" --output-name \"SESSION_TALE.md\""
      }]
    }]
  }
}
```

## Files changed by installation and runtime

| Path | Change |
|---|---|
| `<WORKSPACE>/.claude/settings.json` | one lifecycle registration |
| `<WORKSPACE>/.brain/SESSION_TALE.md` | overwritten on successful compaction processing |
| `<WORKSPACE>/last_session_tail.err.log` | written only when a failure has a known workspace |

`--output-dir` and `--output-name` change the tail output location and filename.
`--agent NAME` overrides the display label derived from the workspace basename.

## Verify

1. Run `python tests/smoke_test.py` from the package root.
2. Trigger a real PostCompact event in the target workspace.
3. Confirm the output file is recent and that its recorded turns match the post-boundary
   source transcript.
4. If no file is written, inspect `<WORKSPACE>/last_session_tail.err.log`.

## Uninstall

1. Remove or update any local process configured to consume the tail file.
2. Remove the `PostCompact` registration from `<WORKSPACE>/.claude/settings.json`.
3. Remove `<PACKAGE_ROOT>`.
4. Optionally remove the tail and error-log files.

Validate that `settings.json` remains valid JSON after removing the registration.
