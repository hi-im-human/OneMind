# Selfhook — Technical specification

## Components

1. `src/selfhook.py` loads `config/continuity.json`, validates it, selects sections subscribed to the supplied event, and prints one JSON hook payload.
2. `src/check_limits.py` imports the same validation contract and exits nonzero for invalid configuration or over-limit files.
3. `config/continuity.json` contains sections and character caps.

## Configuration contract

```jsonc
{
  "workspace": "C:/absolute/workspace/path",
  "sections": [{
    "slug": "startup-files",
    "header": "CONFIGURED STARTUP FILES",
    "events": ["SessionStart"],
    "text": "Optional short text.",
    "read_files": { "dir": ".memory", "patterns": ["startup.md", "work-notes.md"] }
  }],
  "caps": [{ "path": ".memory/startup.md", "limit": 12000 }]
}
```

- `workspace` is an existing absolute path.
- Section slugs and headers are nonblank; slugs are unique.
- `events` is optional. Omitted means the section renders for every event.
- `read_files.dir`, patterns, and cap paths are workspace-relative and resolve within the workspace to regular files.
- Glob patterns list every sorted match. A no-match result is a configuration error.
- Only documented keys are accepted, except `_comment`.
- `sections` and `caps` are required lists, including when empty.
- Sections support static text and file pointers only. They do not execute commands.

## Output contract

The hook prints one JSON object:

```json
{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"<payload>"}}
```

`--event` selects sections. Both registered lifecycle commands emit `hookEventName: "SessionStart"` because a verified Claude Code runtime behavior drops payloads labelled `PostCompact`.

The payload is capped at 1,800 characters. When shortened, the cut marker is kept inside the budget.

## Failure behavior

Any configuration error emits a bounded `SELFHOOK CONFIG ERROR — HOOK DID NOT RENDER` payload and no valid sections. The checker returns exit code 1 for the corresponding invalid configuration.

| Condition | Hook behavior | Checker behavior |
|---|---|---|
| unreadable or invalid JSON | error-only payload | exit 1 |
| unknown or missing required keys | error-only payload | exit 1 |
| invalid section, duplicate slug, or invalid field type | error-only payload | exit 1 |
| absent, escaping, or non-file pointer/cap target | error-only payload | exit 1 |
| over-limit cap target | normal hook validation | exit 1 |
| no sections for an event | silent exit 0 | n/a |

## Non-goals

- Injecting pointed-at file contents.
- Observing whether listed files are subsequently opened.
- Scheduling, search indexing, or tail generation.
