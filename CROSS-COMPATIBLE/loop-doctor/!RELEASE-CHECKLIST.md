# Release Checklist: Loop Doctor

Candidate root: `<PACKAGE_ROOT>/OneMind_loop-doctor-package`

Export target: `<SEPARATE_EXPORT_REPOSITORY_PATH>`

> A checked item includes reproducible evidence. An unchecked item is a real release blocker.

## Exact surface and sanitization

- [x] The validator printed the exact candidate root and scanned only that release surface. Evidence: OneMind `release_gate.py` run recorded in the private release worklog on 2026-08-13.
- [x] All planted scanner controls passed. Evidence: release-gate output reported `positive controls passed`.
- [x] Private-name, host-path, ID, handle, room-name, and secret findings are zero. Evidence: release-gate output reported `0 finding(s)`.
- [x] No live state, raw logs, backups, dependency trees, local config, or private fixtures are present. Evidence: `forbidden-artifacts: none`.

## Cheap onboarding

- [x] `!INSTALL.md` names package home, runtime home, continuity-data home, generated files, verification, and uninstall.
- [x] Paths are generated, discovered, or provided through local config; adding a user or agent does not require editing source code. Evidence: `!INSTALL.md` and `!DEPENDENCIES.md`.
- [x] An independent agent completed the install from a fresh home without source-household help, identified every destination, verified the non-Discord live surface, and removed the package cleanly. Evidence: independent final-candidate validation on 2026-08-13 and `tests/release-receipt.json`.
- [x] Costs, accounts, network services, and paid dependencies are disclosed before installation. Evidence: `!INSTALL.md` Requirements and `!DEPENDENCIES.md` Costs and accounts.

## Correctness

- [x] The intended agent caller passed all ten non-Discord smoke tests from an isolated installed skill scope; optional Discord test 9 was skipped because no server was available. Evidence: independent final-candidate validation on 2026-08-13 and `tests/release-receipt.json`.
- [x] Expected failure and denial behavior is documented for reproducible testing. Evidence: `tests/SMOKE_TESTS.md` tests 7, 10, and 11.
- [x] Every shipped factual-runtime claim has current evidence or was removed or resized. Evidence: `tests/release-receipt.json`.
- [x] No known-falsified statement remains in prompts, skills, docs, errors, or warnings. Evidence: full serial review plus independent cold read on 2026-08-13.

## License, provenance, and review

- [x] `LICENSE`, `config/tool.json`, and `tests/release-receipt.json` identify MIT. The existing authored package retained its declared license.
- [x] Dependency licenses and copied or derived source provenance were reviewed. Evidence: `!DEPENDENCIES.md` License and provenance review.
- [x] A reviewer other than the primary builder reran the validator on the final candidate. Evidence: independent final-candidate validation on 2026-08-13; all mechanical checks passed and the validator refused release only for incomplete evidence fields.
- [x] An independent reviewer followed the onboarding path and recorded ambiguity. Evidence: independent cold-reader review on 2026-08-13; two stage-label ambiguities were found and corrected.

## Release decision

- [x] Every blocking item above is checked with evidence.
- [x] The candidate may be copied into the separate export repository.

Builder/release reviewer: Forge

Independent reviewer: Independent cold-reader agent

Date: 2026-08-13

## Post-release feedback (non-blocking)

- Human walkthrough status: `not yet tested`
- Evidence or issue link: pending first outside human installation

Do not claim human testing before it occurs. Human feedback may produce a later documentation
revision; it is not required to make the package available for that test.
