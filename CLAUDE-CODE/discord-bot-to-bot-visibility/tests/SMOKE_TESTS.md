# Smoke Tests

Run all planted controls against a temporary fixture root with `--no-home-scan`. Do not use live plugin files for planted failure controls.

## Fixture layout

```text
<TEMP_ROOT>/
└── plugins/
    ├── cache/claude-plugins-official/discord/0.0.4/server.ts
    └── marketplaces/claude-plugins-official/external_plugins/discord/server.ts
```

## Required matrix

1. **Stock dry-run** — expect `would be patched`, exit zero, and byte-identical fixture.
2. **Stock apply** — expect `patched`, exit zero, current block once, stock absent.
3. **Idempotence** — second apply expects `already`, exit zero, byte-identical file.
4. **Each v1 variant** — dry-run expects `would be upgraded`; apply expects `upgraded`; next apply expects `already`.
5. **Unfamiliar variant** — expect refusal, nonzero exit, and byte-identical fixture.
6. **Mixed state** — stock plus current in one file; expect refusal, nonzero, no write.
7. **Duplicate state** — two stock blocks; expect refusal, nonzero, no write.
8. **Known plus unknown handler** — each known block beside a second single- or double-quoted `messageCreate` handler; expect refusal, nonzero, no write.
9. **Authorization shape** — current block contains unconditional self-ID drop, current-channel/parent-thread group lookup, and subsequent `handleInbound` call.
10. **Scoped discovery** — `--no-home-scan <TEMP_ROOT>` discovers only the explicit fixture.
11. **No roots** — `--no-home-scan` with no valid explicit root writes nothing and reports no files.
12. **Unknown option** — a misspelled `--...` option exits nonzero before discovery or write.
13. **Live dry-run** — default home scan performs no write and reports the observed installed states.

## Package gates

```text
python -m py_compile src/patch_discord_bot_filter.py
python -m json.tool hook-snippet.settings.json
python -m json.tool config/tool.json
```

Also verify:

- Required !SCHEMA files exist.
- `SKILL.md` YAML frontmatter parses.
- No `__pycache__`, `.pyc`, private paths, personal IDs, tokens, or credentials ship.
- Public docs and source agree on statuses, exit behavior, discovery paths, authorization scope, platform verification, and rollback.

## Known-bad control

Copy the package to a non-shipping temporary directory and deliberately weaken one guard, such as changing unfamiliar-state refusal to exit zero. The package gate must detect the seeded defect. A green clean run without a red control is not a completed review receipt.
