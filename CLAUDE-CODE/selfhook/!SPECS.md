# Selfhook — Specs

## Design

Two scripts, one config, no state:

1. **`src/selfhook.py`** — the multiplexer. Reads `config/continuity.json`, renders the
   sections subscribed to the firing event (config order, banner per section), and
   prints one JSON `additionalContext` payload. Pointers and short text only.
2. **`src/check_limits.py`** — commit-time cap enforcement. Runs the *same full*
   config validation as the hook (imports `validate` from `selfhook.py` — one
   contract, two consumers, no code parsing code), so any config the hook would
   refuse to render fails the commit too; then exits 1 loudly on any over-limit
   file. A typo that silently disables a cap is worse than no cap.
3. **`config/continuity.json`** — the single source of truth: sections (what the agent
   is told at session start) and caps (what the checker enforces).

## Config contract

```jsonc
{
  "workspace": "<optional; else --workspace, else cwd>",
  "sections": [
    {
      "slug": "identity",              // unique; duplicates render a visible error
      "header": "BANNER TEXT",          // required
      "events": ["SessionStart"],       // optional; absent = every event
      "text": "short instruction",      // optional
      "read_files": {                   // optional
        "dir": ".memory/identity",
        "patterns": ["persona.md", "my-*.md"]   // a glob lists ALL matches
      }
    }
  ],
  "caps": [ { "path": ".brain/GROWTH.md", "limit": 8000 } ]
}
```

**There is no command/script source type, by design.** Sections carry text and file
pointers; anything executable would reopen both the payload-size hole and an
arbitrary-execution surface in a file people edit casually.

**Strict keys (load-bearing):** every level accepts only its known keys (`_comment`
allowed everywhere), and the root must contain `sections` and `caps` explicitly
(`[]` for none). A misspelled key — `event` for `events`, `read_file` for
`read_files`, `section` for `sections`, `cap` for `caps` — is a config error, not a
silent no-op: each of those typos would otherwise produce a healthy-looking partial
configuration, which is the failure class this package exists to prevent.

**Containment (load-bearing):** `workspace` must be an **absolute** path to an
existing directory — a contract enforced identically by the hook and the checker;
every `dir`, pattern, and cap path must be workspace-relative, every resolved target
(symlinks included) must sit **beneath the workspace**, and every pointer or cap
target must be a **regular file** — a directory cannot be a pointer target. A
pointer this hook renders is an instruction the agent will obey — a path that
escapes the workspace is an instruction to read outside it. Absolute paths, `..`,
and symlink escapes are all config errors. Field types are checked before any set
or path operation, so a wrong type is a visible config error, never a traceback.

## Output contract

One JSON object on stdout:
```json
{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "<payload>"}}
```
Both event registrations emit `"SessionStart"` — the runtime's schema (as of last
verification) silently drops payloads named `"PostCompact"`. `--event` still selects
which sections render.

## Failure policy (load-bearing)

**Any config error produces an ERROR-ONLY payload** headed `SELFHOOK CONFIG ERROR —
HOOK DID NOT RENDER`. No valid subset is rendered alongside errors: executing a
partial configuration while looking healthy is the failure class this package exists
to prevent.

| condition | behavior |
|---|---|
| config missing / unreadable / not valid JSON / non-object root | bounded error-only payload, no traceback |
| unknown key at any level · missing `sections`/`caps` | error-only payload (hook) **and** exit 1 (checker) — a typo must not become a silent no-op |
| duplicate section slug · malformed section · bad field types · unknown event | error-only payload listing each |
| configured file not found · glob matching nothing | error-only payload — a missing pointer is a lie waiting for a reader |
| `workspace` still `<WORKSPACE>`, not an existing directory, or relative | error-only payload (hook) **and** exit 1 (checker) — same contract in both |
| `dir`/pattern/cap path absolute, `..`, or symlink-escaping the workspace | error-only payload — a rendered pointer outside the workspace is rejected, never emitted |
| pointer or cap target exists but is not a regular file (e.g. a directory) | error-only payload / checker exit 1 — a directory cannot be read as a pointer or capped |
| malformed caps entry, absolute cap path, cap file missing or unreadable | error-only payload (hook) **and** exit 1 (checker) — one shared contract; a typo must not disable a cap silently, and a read error fails closed |
| glob matches several files | **all listed** — never a silent first-match |
| payload exceeds **1,800 chars** | cut with the marker **reserved inside the budget** — the budget sits below the worst measured transport floor (~2,000 received), because a marker past the floor can itself be truncated away |
| no sections subscribed to this event | silent exit 0 — nothing to say is not an error |

## Non-goals

- **Injecting file contents.** The measured transport truncation (README) makes this a
  lie waiting to happen. Pointer only.
- **Enforcing that the agent reads.** The banner maximizes the odds; discipline is the
  agent's.
- **Scheduling, memory search, or tail-writing.** Other tools own those; they integrate
  as sections.
