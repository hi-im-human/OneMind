# Release Checklist: freestyle-beats

Candidate root: `<PACKAGE_ROOT>` (the exact staging surface the validator prints and digests)

Export target: `<SEPARATE_EXPORT_REPOSITORY_PATH>` (→ `CLAUDE-CODE/freestyle-beats/`)

> A checked item must include reproducible evidence. If evidence is missing, leave it unchecked.

## Exact surface and sanitization

- [x] The validator printed the exact candidate root and scanned only that release surface. Evidence: Forge's gate preflight output after the serial review; the final independent PASS digest belongs in the private external gate receipt, not self-referentially inside this candidate
- [x] All planted scanner controls passed. Evidence: Forge gate preflight output (positive-control privacy scan PASS); builder's bait-first scan 14:24 (bait caught before clean run trusted)
- [x] Private-name, host-path, ID, handle, room-name, and secret findings are zero. Evidence: Forge gate preflight output — 0 findings; two builder-scan hits triaged (tool.json author byline, deliberate; "a reading thread" common-noun false positive)
- [x] No live state, raw logs, backups, dependency trees, local config, or private fixtures are present. Evidence: Forge gate preflight output — forbidden-artifacts PASS

## Cheap onboarding

- [x] `!INSTALL.md` names package home, runtime home, continuity-data home, generated files, verification, and uninstall/rollback. Evidence: `!INSTALL.md` H2 contract headings, this revision
- [x] Paths are generated, discovered, or provided through local config; adding a user/agent does not require editing source code. Evidence: `<PACKAGE_ROOT>`/`<WORKSPACE>` placeholders throughout; no roster, no hardcoded identities anywhere in `src/`
- [x] An independent agent completed the install from a fresh home without source-household help, identified every destination, verified the live surface, and removed the package cleanly. Evidence: independent stateless agent blind install on Windows, Python 3.11.9, Claude Code v2.1.231, project-scope; all 7 smoke tests passed; uninstall removed all package-specific content
- [x] Costs, accounts, network services, and paid dependencies are disclosed before installation. Evidence: `!INSTALL.md` Requirements ("no accounts, no network services, no paid dependencies")

## Correctness

- [x] The intended live caller passed the documented smoke test. Evidence: independent stateless agent ran tests/SMOKE_TESTS.md 1–7; all passed on Windows, Python 3.11.9, Claude Code v2.1.231
- [x] Expected failure/denial behavior was tested where relevant. Evidence: this package has no permission/denial branch, so explicit denial behavior is not applicable. Negative expectations actually observed: stale hook phrases absent in Test 3; duplicate crons absent in Test 5; reminder, skill, and package-specific installed content absent after uninstall in Test 7
- [x] Every shipped factual-runtime claim has current evidence, or the claim was removed/resized. Evidence: tests/release-receipt.json — all 5 claims now status "passed"; claim 5 (no runtime file writes) verified to the scope of the blind run (install, live session, uninstall behavior on this candidate)
- [x] No known-falsified statement remains in prompts, hooks, docs, errors, or warnings. Evidence: the one known-falsified ancestral claim ("compaction wipes your crons") was replaced with check-first wording; falsification history preserved in src/hooks/post_compact_reminder.py comment and !BUGS.md so it cannot be silently reintroduced

## License, provenance, and review

- [x] `LICENSE`, `config/tool.json`, and `tests/release-receipt.json` identify the same SPDX license. Evidence: all three state Apache-2.0 (OneMind default for new packages; builder-authored, no prior author license to preserve)
- [x] Dependency licenses and copied/derived source provenance were reviewed. Evidence: `!DEPENDENCIES.md` — runtime + Python only; no vendored code; ancestry disclosed in `!CHANGELOG.md`
- [x] A reviewer other than the primary builder reran the validator. Evidence: independent stateless agent reran the external gate after recording evidence; pre-evidence gate run confirmed frozen digest and only pending-evidence failures; final gate run passed
- [x] The independent reviewer followed the onboarding path and recorded any ambiguity. Evidence: independent stateless agent followed !README.md, !INSTALL.md, and tests/SMOKE_TESTS.md without source-household knowledge; no ambiguities or defects found; all destinations explicitly documented

## Release decision

- [x] Every item above is checked with evidence.
- [x] The candidate may be copied into the separate export repository. Evidence: final external gate PASS (conditional on the private gate receipt recording that PASS)

Builder: `Cael`

Independent reviewer: `independent stateless agent`

Date: `2026-08-13`

## Post-release feedback (non-blocking)

- Human walkthrough status: `not yet tested`
