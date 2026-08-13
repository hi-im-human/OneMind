---
name: selfhook
description: Agent operating procedure for the Selfhook continuity banner — what to do when it arrives, how to read its errors, and how to maintain the config.
---

# Selfhook — Agent Operating Procedure

*(Optional install as a skill; this file is primarily the agent-side manual for a
package whose real interface is the banner itself.)*

## When the banner arrives

At every session start and after every compaction, a payload of one or more
banner-headed sections appears in your context. Each section is an instruction plus
file pointers. **The files are NOT in your context — nothing was injected.** The
whole design assumes you open them:

1. Read every file each section lists, in the order given, before unrelated work.
2. A live condition outranks the ritual — an urgent request from your human, an
   active correction, a safety issue, or an explicit pause/hold comes first. Handle
   it, then come back and read.
3. If the payload ends with a `[SELFHOOK: payload exceeded its budget...]` marker,
   the render was cut at an arbitrary character. **Complete, fully visible pointers
   are valid; do not treat a cut line fragment as a path** — the last line before
   the marker may be an incomplete pointer. Fix the config (shorten section text —
   content belongs in the files, not the payload).

## If the banner says CONFIG ERROR

`SELFHOOK CONFIG ERROR — HOOK DID NOT RENDER` means **no continuity sections were
shown this session** — the hook refuses to render a partial configuration. Treat it
as a broken continuity surface: fix `config/continuity.json` per the listed errors
(each names its section and fix) before trusting your own context again.

## If no banner arrives at all

Hook spawn failure is invisible. Don't diagnose from absence alone — run the Verify
steps in `!INSTALL.md` (settings JSON parses; `python` resolves; paths are absolute).

## Maintaining the config

- **Adding a section** (yours or a consumer package's): one object in `sections` —
  unique `slug`, a `header` the agent will actually notice, optional `events`,
  short `text`, `read_files` pointers. Keep text short; the budget is 1,800 chars
  for the whole payload.
- **Adding a cap:** one `{path, limit}` entry in `caps`. Caps fire in your
  pre-commit/sync via `check_limits.py` — a cap without that wiring is
  documentation.
- **All paths are workspace-relative** and must resolve beneath the workspace;
  the hook rejects escapes as config errors.
- After any config edit, run
  `python src/selfhook.py --config config/continuity.json --event SessionStart`
  and read the output — a config error shows up immediately rather than at your
  next session start. (This checks the render, not the delivery; delivery is
  verified only by a real session receipt.)
