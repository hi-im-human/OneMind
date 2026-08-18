# Install — Selfhook 1.1.0

## Placeholders

- `<PACKAGE_ROOT>`: absolute package location.
- `<WORKSPACE>`: absolute Claude Code workspace containing `.claude/` and `.memory/`.

## Prepare the configuration and directory target

1. Copy `config/continuity.example.json` to `config/continuity.json` and set its
   `workspace` to `<WORKSPACE>`. Ensure every configured section/cap path exists.
2. Prepare `<WORKSPACE>/.memory/MEMORY.md`.
   - For a new workspace, copy `templates/MEMORY.md`.
   - For an existing file, retain its frontmatter and other content, then add the two
     generated-directory markers on their own lines after closing frontmatter.

The generator replaces only the bytes between those markers. It refuses an unmarked
or malformed target and does not add markers itself.

## Register lifecycle commands

Register the existing renderer commands plus the default PreCompact directory refresh
in `<WORKSPACE>/.claude/settings.json`:

```json
"hooks": {
  "SessionStart": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \"<PACKAGE_ROOT>/src/selfhook.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --event SessionStart" }] }],
  "PostCompact": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \"<PACKAGE_ROOT>/src/selfhook.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --event PostCompact" }] }],
  "PreCompact": [{ "matcher": "", "hooks": [{ "type": "command", "command": "python \"<PACKAGE_ROOT>/src/identity_directory.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --write --quiet" }] }]
}
```

Use doubled backslashes in Windows JSON paths. Optionally wire `check_limits.py` into
a local commit or sync workflow.

## Verify

1. Run the renderer and checker commands from `tests/SMOKE_TESTS.md`.
2. Run the generator directly once:

   ```text
   python "<PACKAGE_ROOT>/src/identity_directory.py" --config "<PACKAGE_ROOT>/config/continuity.json" --write --quiet
   ```

   Expect `WRITTEN` or `UP TO DATE`; inspect the marker block and confirm no depth-2
   child contents appear.
3. Parse `settings.json` and verify all three lifecycle registrations.
4. Run the runtime and directory-specific smoke tests in `tests/SMOKE_TESTS.md`.

## Uninstall

1. Remove the SessionStart, PostCompact, and PreCompact registrations.
2. Remove optional checker wiring.
3. Remove `<PACKAGE_ROOT>`.

Removing the package before registrations leaves invalid command paths. Uninstall does
not remove a generated directory block from `MEMORY.md`; remove the markers manually
only if that is desired.
