# Loop Doctor — Known Issues and Limitations

## Open

### No technical runtime brake is bundled

**Status:** Known limitation.

Loop Doctor is portable markdown. It can instruct an agent to stop, but it cannot terminate a
run, cap retries, revoke a tool, or monitor a process by itself. Installers must use technical
controls available in their runtime when an agent may continue executing after losing control
of a turn. Do not loosen permissions as a loop treatment.

### Live skill behavior varies by runtime

**Status:** Known limitation.

Skill discovery, slash-command behavior, prompt injection, and refresh timing differ across
platforms. A file existing in the right folder does not prove the target agent loaded it.
Run `tests/SMOKE_TESTS.md` against every intended installation.

### Clinic privacy depends on the full delivery path

**Status:** Known limitation.

Discord channel permissions do not control server administrators, exports, integration logs,
or adapter routing. A room is private only to the extent that every layer in the route is
configured and verified. The package makes no absolute-confidentiality claim.

### Field cases do not establish universal causality

**Status:** Accepted evidence boundary.

The case studies are de-identified single-case observations. They can generate and refine
hypotheses; they do not establish that a named intervention was necessary, sufficient, or
portable to every agent.

## Closed on 2026-08-13

- **The pre-release gate required an outside human before the package was publicly available
  to outside humans.** Human walkthroughs are now non-blocking post-release feedback; fresh-
  agent install, smoke testing, sanitization, and factual-runtime evidence remain mandatory.
- **Worked-example stage labels drifted from the canonical model.** All Stage 4 and Stage 6
  labels now include the canonical Resolution Strategy and Resolution State names.
- **Legacy document names split the canonical package surface.** The package now uses the
  required `!SCHEMA` names and internal references.
