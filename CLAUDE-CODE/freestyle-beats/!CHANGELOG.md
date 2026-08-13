# Freestyle Beats — Changelog

## Current status

**Release gate passed 2026-08-13** — genericized same day; mechanical gate complete
(shape, license, install contract, bait-proven sanitization all PASS). An independent
stateless agent completed the blind install/test/uninstall phase on Windows, Python
3.11.9, Claude Code v2.1.231, project-scope: all 7 smoke tests passed, no source-household
knowledge needed, no ambiguities or defects found. The final external gate passed.
Human walkthrough not yet performed; real-world install feedback is welcome in this
repository's Issues.

---

## 2026-08-13 — v1.0.1: blend guidance + manifest tracking fix

- **Same-event hook outputs are BLENDED into one context injection** without clear
  boundaries — documented in `!INSTALL.md` and the PostCompact hook docstring, with the
  recommendation to combine several same-event hooks into one script using a short
  header per concern (headers preserve the boundaries the runtime doesn't).
- Export-repo fix shipped alongside: the repository `.gitignore` had wrongly swallowed
  `config/tool.json` (required public manifest), so v1.0.0's public tree was missing it;
  restored, and the ignore rule corrected.

## 2026-08-13 — v1.0 candidate: genericized for standalone release

- Rebuilt from the originating installation's corrected master (its two operator
  environments had drifted; the corrected, unified version is this package's ancestor).
- **Module boundary restored:** the ancestor's live skill had absorbed a sibling
  package's fixed daily-schedule table. Removed; replaced with a one-paragraph hook
  ("scheduled infrastructure beats") that keeps the load-bearing warning about
  registering literal prompt text instead of skill invocations (~78k chars/day measured
  cost of getting this wrong).
- **Runtime claim corrected:** the PostCompact hook no longer asserts "compaction wipes
  your crons" — falsified repeatedly in live use. New wording: check `CronList`,
  rebuild only what's missing, assume neither outcome.
- **Goal templates now ship in the package** (`src/templates/`) — the ancestor's
  install doc said "copy from an existing agent," which a first installer cannot do.
- All operator-specific names, paths, and coordination files removed; multi-agent
  conventions kept as an optional, clearly-marked section.
- Docs rebuilt on the canonical !SCHEMA set.

## Ancestry (before extraction)

- **2026-08-13** — one-master repair in the originating installation: package copy
  re-synced from the corrected live skill; falsified hook claim fixed; dead legacy hook
  copies deleted.
- **2026-08-01** — measured the slash-invocation context cost (~11.2k chars/fire, ~78k/day
  at 7 fires); fixed daily beats re-registered as literal prompts.
- **2026-05-31** — PostCompact hookEventName workaround discovered (validator silently
  drops `"PostCompact"` payloads; emit `"SessionStart"`).
- **2026-05-19** — initial build: two shared hook scripts + skill, deployed across a
  four-agent installation.
