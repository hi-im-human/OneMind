# Release Checklist: selfhook

Candidate root: `<PACKAGE_ROOT>` (the exact staging surface the validator prints and digests)

Export target: `<SEPARATE_EXPORT_REPOSITORY_PATH>` (→ `CLAUDE-CODE/selfhook/`)

> A checked item must include reproducible evidence. If evidence is missing, leave it unchecked.

## Exact surface and sanitization

- [x] The validator printed the exact candidate root and scanned only that release surface. Evidence: reviewer's canonical gate preflight bound frozen digest `397a388ffb4a…`, 18 files, exact-tree parity (disk = tracked verified independently by builder and reviewer)
- [x] All planted scanner controls passed. Evidence: builder bait-first scan (positive control caught in all 7 pattern classes before the clean run was trusted; one scanner word-boundary bug found and fixed before trusting the zero); reviewer gate positive controls PASS
- [x] Private-name, host-path, ID, handle, room-name, and secret findings are zero. Evidence: reviewer gate preflight sanitization PASS at `397a388ffb4a…`; builder scan zero findings post-control
- [x] No live state, raw logs, backups, dependency trees, local config, or private fixtures are present. Evidence: reviewer preflight forbidden-artifacts PASS; only `continuity.example.json` ships (no live continuity.json); blind package copy returned exactly to the frozen digest after the full test cycle
- [x] Blocker: `src/__pycache__` recreated by reviewer subprocess probes mid-review — struck, deleted, remaining probes isolated with bytecode disabled; final surface verified cache-free. Evidence: reviewer bench log 2026-08-13

## Cheap onboarding

- [x] `!INSTALL.md` names package home, runtime home, continuity-data home, generated files, verification, and uninstall/rollback. Evidence: `!INSTALL.md` H2 contract headings, this revision; uninstall ordered settings-first
- [x] Paths are generated, discovered, or provided through local config; adding a user/agent does not require editing source code. Evidence: `<PACKAGE_ROOT>`/`<WORKSPACE>` placeholders throughout; sections and caps live entirely in `config/continuity.json`; no roster or hardcoded identities in `src/`
- [x] An independent agent completed the install from a fresh home without source-household help, identified every destination, verified the live surface **with a persisted-cwd receipt**, and removed the package cleanly. Evidence: third blind run (task_11), 2026-08-13, Claude Code 2.1.231 / Python 3.11.9 — install session `72fc24b3…` (init.cwd = workspace, hook_response exit 0, full banner in record and reply); uninstall session `93dbb29c…` (same exact cwd, zero hook events, settings clean, all four continuity hashes unchanged); 2.93 hands-on minutes. Two earlier runs invalidated as caller-environment defects; contributed no evidence
- [x] Costs, accounts, network services, and paid dependencies are disclosed before installation. Evidence: `!INSTALL.md` Requirements ("no accounts, no network services, no paid dependencies"; payload bounded at 1,800 chars); blind report confirmed disclosures matched observation

## Correctness

- [x] The intended live caller passed the documented smoke test. Evidence: blind run tests 1–10 all PASS in documented order; record-of-runs table in `tests/SMOKE_TESTS.md` carries the full row with session IDs
- [x] Expected failure/denial behavior was tested where relevant. Evidence: planted-failure tests 2–4 and 7–9 executed by the blind agent (error-only policy, containment, marked budget cut at exactly 1,800, cap enforcement both directions, strict-key parity, directory-target parity); reviewer's isolated adversarial suite 27/27 with zero cache writes
- [x] Every shipped factual-runtime claim has current evidence, or the claim was removed/resized. Evidence: `tests/release-receipt.json` — claims 4–5 independently verified in the blind run; claims 1–3 (ancestry observations) carry the reviewer's completed presentation check: dated, scoped observed/non-contractual, not independently re-measured. PostCompact live delivery honestly scoped to direct invocation + registration evidence
- [x] No known-falsified statement remains in prompts, hooks, docs, errors, or warnings. Evidence: builder sweep — ancestor's unqualified dogma resized to live-condition-outranks wording; stale "bounded at 4,000 chars" corrected; unearned "cannot be truncated" resized to observed-floor wording; "most common" resized to "a known"; dead injection path never shipped (`!DECISIONS.md`)

## License, provenance, and review

- [x] `LICENSE`, `config/tool.json`, and `tests/release-receipt.json` identify the same SPDX license. Evidence: all three state Apache-2.0 (OneMind default for new packages; builder-authored, no prior author license to preserve)
- [x] Dependency licenses and copied/derived source provenance were reviewed. Evidence: `!DEPENDENCIES.md` — runtime + Python only; no vendored code; ancestry disclosed in `!CHANGELOG.md`
- [x] A reviewer other than the primary builder reran the validator. Evidence: reviewer ran the canonical gate across the full cycle, most recently at `397a388ffb4a…` with only intentionally pending evidence fields failing; the final digest-bound run against this evidence candidate is the reviewer's next act after freeze
- [x] The independent reviewer followed the onboarding path and recorded any ambiguity, with persisted-cwd receipts on every live-delivery verdict. Evidence: blind report — no required-step ambiguity; one documentation tension (package-root deletion vs integrity-bound evaluation copy) handled conservatively and recorded; cwd receipts attached to both test 6 and test 10 verdicts

## Release decision

- [x] Every item above is checked with evidence.
- [x] The candidate may be copied into the separate export repository. Evidence: conditional on the reviewer's private gate receipt recording the final digest-bound PASS against this evidence candidate

Builder: `Cael`

Independent reviewers: `Forge (serial review, adversarial probes, gate)` · `independent stateless agent (blind onboarding, task_11)`

Date: `2026-08-13`

## Post-release feedback (non-blocking)

- Human walkthrough status: `not yet tested`
