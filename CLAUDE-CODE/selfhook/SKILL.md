---
name: selfhook
description: Operating and maintenance procedure for Selfhook's Claude Code lifecycle-hook configuration.
---

# Selfhook — Operating procedure

## When a banner arrives

The payload contains section text and file pointers only; it does not contain the
pointed-at file contents.

1. Open the complete listed files in their configured order when the supplied
   instruction applies.
2. If the payload ends with `[SELFHOOK: payload exceeded its budget...]`, do not use
   a partial final line as a path. Shorten the section text or file list in the
   configuration.
3. `SELFHOOK CONFIG ERROR — HOOK DID NOT RENDER` means no configured sections were
   rendered. Repair the listed configuration errors before relying on a banner.

## If no banner arrives

Absence alone is not a diagnostic. Run the verification sequence in `!INSTALL.md`:
validate `settings.json`, command paths, Python availability, launch directory, and
the headless runtime receipt.

## Maintain the configuration

- Add a section with a unique `slug`, nonblank `header`, optional `events`, short
  `text`, and optional `read_files` object.
- Add a cap as `{ "path": "workspace-relative-file", "limit": integer }`.
- Keep every configured path workspace-relative and within the configured absolute
  workspace root.
- After an edit, run:

  ```text
  python src/selfhook.py --config config/continuity.json --event SessionStart
  ```

  This validates rendering only. Use smoke test 6 for a runtime delivery receipt.
