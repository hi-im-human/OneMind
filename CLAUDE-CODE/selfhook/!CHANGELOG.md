# Selfhook — Changelog

## Current status

v1.0 built and hardened 2026-08-13 through five review batches by the independent
reviewer (builder probe suite 25/25; reviewer's isolated adversarial suite 27/27). Blind
stateless-agent onboarding PASS the same day — tests 1–10 in order, 2.93 hands-on
minutes, exact-cwd stream receipts on both install and uninstall verdicts. Evidence
statuses: `tests/release-receipt.json`. Human walkthrough not yet performed —
feedback welcome via this repository's Issues.

---

## 2026-08-13 — v1.0 candidate: genericized as the OneMind event multiplexer

- **Sections in config, not code**: `slug`/`header`/`events`/`text`/`read_files`,
  deterministic config order, one banner per section. Consumer packages integrate by
  adding a section, never by registering competing hooks. No command source type.
- **Error-only failure policy**: any config problem (malformed JSON, bad section shape,
  duplicate slugs, missing configured files, unedited `<WORKSPACE>` placeholder)
  renders a bounded `SELFHOOK CONFIG ERROR — HOOK DID NOT RENDER` payload with zero
  sections. Never a partial configuration wearing a working face.
- **Payload budget 1,800 chars**, below the worst measured transport floor (~2,000
  received), with the truncation marker reserved *inside* the budget.
- **Containment + fail-closed caps** (reviewer's second pass, same day): field types
  checked before any set/path operation; workspace must be absolute; every rendered
  pointer and cap target constrained beneath it (absolute paths, `..`, symlink
  escapes rejected); caps validated by a contract shared between hook and checker,
  so a typo'd cap path is a visible failure in both, never a silently disabled cap.
- **Whole-contract checker + named banners** (reviewer's final consistency batch,
  same day): the checker now runs the identical full `validate()` as the hook —
  any config the hook refuses to render fails the commit, including section-level
  typos; blank or whitespace-padded `slug`/`header` are rejected (a blank banner
  defeats the named-boundary invariant); smoke test 8 made procedurally explicit
  (hook AND checker against both typo copies).
- **Strict-key contract** (reviewer's schema pass, same day): unknown keys at
  root/section/read_files/cap levels are config errors (`_comment` exempt);
  `sections` and `caps` must be explicitly present. Reproduced typos (`event`,
  `read_file`, `section`, `cap`) had produced healthy-looking partial configs or
  silently disabled caps. Same pass: truncation wording resized to the observed
  floor (the absolute "cannot be truncated" was not earned), README status set to
  unreleased-candidate, uninstall ordered settings-first, SKILL.md frontmatter +
  cut-fragment warning added.
- **Regular-file + shared-workspace contract** (reviewer's third batch, same day):
  every pointer/cap target must be a regular file (directories rejected in exact,
  glob, and cap paths); `validate_workspace` shared by both scripts so the checker
  rejects exactly what the hook rejects; capped-file read errors fail the checker
  closed instead of tracebacking.
- Dead pre-2026-07-31 content-injection path, hardcoded roster/root, and cross-package
  prose from the ancestor: never shipped. Caps moved to config; the checker reads the
  same config instead of regex-parsing Python.
- Priority text resized: reading comes before unrelated work; an urgent request,
  active correction, safety issue, or explicit pause/hold outranks it.

## Ancestry (before extraction)

- **2026-08-01** — banner/separator added after a measured blend incident (same-event
  hook outputs concatenate with no delimiter; an agent obeyed the loud opening
  directives and never read its files).
- **2026-07-31** — the pointer rebuild: runtime truncates hook output at ~2–5 KB and
  reports success (measured receipts in `selfhook.py`); injection replaced with a
  read-instruction; limits moved to commit-time enforcement.
- **2026-05-31** — runtime validator drops `"PostCompact"`-named payloads; both
  registrations emit `"SessionStart"`.
