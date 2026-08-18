# Changelog — Selfhook

## 1.1.0 — candidate

- Added the `.memory` directory generator, a 55-case regression suite, and a clean
  marker-ready `MEMORY.md` template.
- Normal installation registers the PreCompact `--write --quiet` refresh alongside
  the existing renderer registrations.
- The generated index lists the `.memory` root and one child level only, preserving
  bytes outside its marker pair.

## 1.0.0

- Claude Code SessionStart/PostCompact lifecycle renderer.
- Ordered section configuration with banner-separated output.
- Shared validation contract for hook and character-limit checker.
- Workspace containment, regular-file targets, strict keys, and bounded error-only output.
