# Selfhook — Technical specification

## Components

1. `src/selfhook.py` loads `config/continuity.json`, validates it, selects sections
   for an event, and prints one hook payload.
2. `src/check_limits.py` imports the same validation contract and exits nonzero for
   invalid configuration or over-limit files.
3. `src/identity_directory.py` imports the same validation contract, derives
   `<workspace>/.memory`, and refreshes the marked directory in `MEMORY.md`.
4. `config/continuity.json` contains the shared workspace, sections, and caps.

## Configuration contract

`workspace` is an existing absolute path. Sections and caps remain workspace-relative,
resolve inside that workspace, and target regular files. Unknown keys, malformed
sections, duplicate slugs, invalid paths, and invalid caps fail validation.

The directory generator carries no second identity list. Its only configured authority
is the validated workspace root supplied by Selfhook.

## Renderer output contract

The renderer prints one JSON object with `hookEventName: "SessionStart"` and bounded
`additionalContext`. `--event` selects sections. The PostCompact renderer registration
also emits a `SessionStart` label because the recorded Claude Code runtime drops a
`PostCompact`-labelled payload.

## Identity-directory contract

The normal install registers:

```text
python "<PACKAGE_ROOT>/src/identity_directory.py" --config "<PACKAGE_ROOT>/config/continuity.json" --write --quiet
```

at `PreCompact`, in addition to the renderer registrations.

- The target is exactly `<validated workspace>/.memory/MEMORY.md`.
- The BEGIN and END markers must each occupy their own line after closing frontmatter.
- The rendered block lists root Markdown files other than `MEMORY.md` and every
  top-level non-hidden folder. A folder lists its direct Markdown files with a
  frontmatter description when present, and direct child folders by name only.
- It never reads, renders, or descends into depth-2 content.
- Missing or empty descriptions leave an entry unsuffixed and are counted in status.
- It preserves bytes outside the marker block, including BOM and line endings. It
  refuses a concurrent edit before replace, verifies exact output bytes afterward, and
  re-parses frontmatter after write.

## Failure behavior

| Condition | Result |
|---|---|
| renderer configuration error | error-only renderer payload |
| checker configuration/cap failure | exit 1 |
| absent `.memory`, `MEMORY.md`, markers, or valid frontmatter | generator refusal; no write |
| concurrent `MEMORY.md` edit | generator refusal; newer bytes retained |
| no indexed entries | generator refusal; no write |

## Non-goals

- Injecting pointed-at file contents.
- Replacing content outside the generated marker block.
- Recursive `.memory` indexing or a second identity-file configuration.
- Installing or modifying an existing workspace without an install action.
