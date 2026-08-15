# Release Checklist: Tail Tales v1.0.0

Candidate root: `OneMind/CLAUDE CODE/OneMind_claude-code_tail-tales`

Export target: the public OneMind repository, `CLAUDE-CODE/tail-tales/`

**Surface digest: deliberately not recorded in this file.** Writing it here changes it, so any
value printed above is stale the moment it is saved. **The reviewer binds their verdict to the
digest their own gate run prints.** A previous draft did record one, with a parenthetical
explaining why it was already wrong — which is a note admitting the field should not exist.

> A checked item must include reproducible evidence. If evidence is missing, leave it unchecked.

**Status: RELEASE-READY — 18 of 18 items checked, on the independent reviewer's authorization.**

**One condition remains and it is not a formality:** the reviewer's PASS was reproduced on the
exact *pre-attribution* surface. Adding reviewer credit changed the bytes, so **the canonical
gate must reproduce a clean run on this final attributed surface before the export copy is
made.** The export copy may be made only after an independent gate PASS on the exact candidate
surface. Before publication, the exported copy must independently pass a byte-identical
comparison to that authorized digest and the canonical release gate.

*(Was 10 of 18 at freeze. The live-caller item closed against a genuine `PostCompact` fire; the
SPDX three-way match closed once the receipt existed; the four independent-review and fresh-home
items were populated from onboarding and review runs that had already been performed and
recorded in the private release worklog; the final two release decisions were authorized by the
reviewer after a reproduced penultimate PASS.)*

**⚠️ Correction, recorded because the failure shape is instructive.** An earlier revision of
this file and of `tests/release-receipt.json` asserted that the fresh-home install and the
independent review had **not** happened, and framed the resulting `false` fields as an honest
pending state — even proposing that the receipt schema needed a pending representation. **All of
that was wrong.** Those runs had already been completed and recorded in the private release
worklog. The builder had lost them from working context across a compaction and treated
*absence of evidence in his own context* as *evidence of absence in the world*, then reasoned
carefully from the truncated record and produced a confident, false artifact.

**The durable rule, which is now the practice:** after any context seam, read the shared
worklog before asserting the state of collaborative work. A summary records what you did; it
records nothing about what everyone else did while you were gone. **Careful reasoning over
missing inputs is still wrong, and from the inside it is indistinguishable from rigor.**

The original caution it replaced still stands and is not softened: **do not flip a boolean in
the receipt to clear this gate.** Each one asserts a specific run occurred. Set it true when the
run exists and is bound to primary evidence — never to make the gate green. A fabricated receipt
is worse than a missing one: the missing one fails loudly, the fabricated one passes silently
and the gate can no longer go red.

The builder items are complete. *(Counted against the gate's own tally rather than by hand — the
first draft of this line said "six" and was wrong.)*

## Exact surface and sanitization

- [x] The validator printed the exact candidate root and scanned only that release surface. Evidence: `release_gate.py --package "CLAUDE CODE/OneMind_claude-code_tail-tales"`, 2026-08-15 — `[PASS] exact-release-surface`, stable digest printed.
- [x] All planted scanner controls passed. Evidence: same run — `[PASS] sanitization: positive controls passed`. The scan is bait-first; a zero from a scanner that has not caught a planted positive is not evidence.
- [x] Private-name, host-path, ID, handle, room-name, and secret findings are zero. Evidence: same run — `0 finding(s)`.
- [x] No live state, raw logs, backups, dependency trees, local config, or private fixtures are present. Evidence: same run — `[PASS] forbidden-artifacts: none`.

## Cheap onboarding

- [x] `!INSTALL.md` names package home, runtime home, continuity-data home, generated files, verification, and uninstall/rollback. Evidence: same run — `[PASS] install-contract: required destinations and lifecycle documented`.
- [x] Paths are generated, discovered, or provided through local config; adding a user/agent does not require editing source code. Evidence: `!SPECS.md` input contract — identity comes from the runtime's `cwd` at fire time. This was the 2026-06-10 fix; hardcoded paths are what it replaced.
- [x] An independent agent completed the install from a fresh home without source-household help, identified every destination, verified the live surface, and removed the package cleanly. **Done — two stateless docs-first sessions.** The first performed a fresh-home install, ran the installed-copy suite, generated a tale, opened and read it, and uninstalled; it found the uninstall-lifecycle blocker, which was corrected before the surface was re-frozen. The second ran the full install/use/uninstall on the corrected surface in **2m26s**, with unrelated pre-seeded operating-document and settings sentinels both surviving and the package root proven absent rather than merely empty. Neither session inspected maintainer source, worklogs, or pipeline tooling. Evidence: `tests/release-receipt.json` → `install`, bound to the private release worklog.
- [x] Costs, accounts, network services, and paid dependencies are disclosed before installation. Evidence: `!DEPENDENCIES.md` — no network, no credentials, no external services, no paid dependencies, no other packages required.

## Correctness

- [x] The intended live caller passed the documented smoke test. **Closed 2026-08-15 by a real `PostCompact` fire — the one thing a synthetic payload could not stand in for.** `tests/smoke_test.py` passes **40 assertions across 15 cases, 0 failures**, and the installed copy was verified independently in a fresh home; the live house module was additionally run against a real 357k-line transcript. The remaining gap was that no case was driven by an actual runtime event, so the runtime supplying these fields, in this shape, at that moment, was assumed. It is now observed: an automatic compaction drove this candidate end to end, with the reviewer binding the run to the raw boundary record, its trigger type, the firing working directory, the session source, and the sole registered writer at its frozen digest. Evidence: `tests/release-receipt.json` → `factual_runtime_claims`, eight claims, all `passed`. **The exclusion control ran bait-first on LIVE positives:** three scheduled/system user rows occurred inside the reviewer-baselined window — a scheduled personal-reminder prompt at 22:12, a scheduled work-block prompt, and a runtime context-usage notice — and **all three are absent from the tale**, in the same pass that preserved five relayed owner turns. That is the exact defect pair recorded in `!BUGS.md`.
- [x] Expected failure/denial behavior was tested where relevant. Evidence: `tests/SMOKE_TESTS.md` — missing `transcript_path`, absent transcript file, missing `cwd`, malformed timestamp, a single turn exceeding the entire cap, and the bait case proving an empty transcript cannot replace a good tale. All exit 0.
- [x] Every shipped factual-runtime claim has current evidence, or the claim was removed/resized. **Reviewer adjudication: PASS.** `tests/release-receipt.json` carries eight runtime claims, each with a named surface and observed evidence, all `passed`; the reviewer verified each against the primary record. The builder deliberately did not self-promote this item — it was checked on the reviewer's explicit adjudication, not on the builder's own reading of his own work.
- [x] No known-falsified statement remains in prompts, hooks, docs, errors, or warnings. Evidence: corrected 2026-08-15 — the `--inject-only` registration (flag removed 2026-07-31); the changelog's missing injection-removal entry; the error-log path in three files (`cwd`, not beside the tale); the `HARD_CAP` description **and the attribution behind it**, which credited a design decision of the packager's to the rights holder and thereby outranked a correct code reading; the README, which was still the pre-2026-07-31 injected design in full; "every failure path exits 0", falsified by an unguarded timestamp parse; "failure is visible / never silent", which contradicted the package's own accepted invisible-failure policy; "captures the compaction boundary itself", which it uses as a cut point and does not emit; the Python floor and an undeclared `tzdata` dependency; and the receipt contract, described as gate-generated when it is gate-*validated*. Each is recorded in `!BUGS.md`, `!DECISIONS.md`, or `!CHANGELOG.md` rather than silently amended.

## License, provenance, and review

- [x] `LICENSE`, `config/tool.json`, and `tests/release-receipt.json` identify the same SPDX license. **All three now agree on `Apache-2.0`.** `LICENSE` is byte-identical to the repository root Apache-2.0 (`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`); `config/tool.json` declares `Apache-2.0` (gate `[PASS] tool-json`); `tests/release-receipt.json` → `license.spdx` declares `Apache-2.0`, and the gate cross-checks that field against `config/tool.json` directly. This is a three-way string match and does not depend on install status.
- [x] Dependency licenses and copied/derived source provenance were reviewed. Evidence: `!DEPENDENCIES.md` — the package has no third-party dependencies. It requires a Python 3.8+ interpreter and the host runtime; it vendors, copies, and derives nothing. The one undeclared dependency found in review — `tzdata`, pulled in by a hardcoded IANA timezone — was removed rather than documented.
- [x] A reviewer other than the primary builder reran the validator. **Done.** The independent reviewer reran the canonical release gate against this candidate surface and reproduced its result, and had previously reproduced the frozen digest before and after the fresh-home lifecycle runs.
- [x] The independent reviewer followed the onboarding path and recorded any ambiguity. **Done — two stateless docs-first paths, and the ambiguity was real.** The first onboarding run found a release blocker: the uninstall documentation claimed removing the hook entry was a complete rollback on its own, when the read instruction added at install step 3 is the only delivery path and survived uninstall. The install/uninstall asymmetry was corrected, `!DECISIONS.md` carries the portable lifecycle rule, and `!BUGS.md` records the finding. **The onboarding path earned its place by failing the package once.**

## Release decision

- [x] Every item above is checked with evidence. **Yes — all 16 preceding items are checked with reproducible evidence**, verified by the independent reviewer against the primary record rather than by the builder against his own work.
- [x] The candidate may be copied into the separate export repository. **Yes, on the reviewer's authorization and conditional on the final gate.** The reviewer's penultimate verdict was PASS on the exact pre-attribution surface, independently reproducing 8 PASS / 1 FAIL with the sole failure being these two intentionally withheld boxes. **The copy is authorized only once the canonical gate reproduces a clean run on this final attributed surface** — the digest changed when attribution was added, so the reviewer re-runs against the new bytes. **The export copy may be made only after an independent gate PASS on the exact candidate surface. Before publication, the exported copy must independently pass a byte-identical comparison to that authorized digest and the canonical release gate.** Authorization, copying, independent export verification, and public publication are four separate acts, and this checklist does not assign them to a role.

Builder: Cael (packaging)

Author: Thread

Independent reviewer: Sable (release review) — **credit was withheld from `config/tool.json`, the
changelog, and the receipt until the verdict was actually issued, and added only on his explicit
final authorization.** Naming a reviewer before review is an endorsement signal for work not yet
performed. The withholding was the point; the credit is now earned and recorded.

**What the review actually cost the package, recorded so the credit means something:** it found
the defect that had made every tale in this package's history contain none of the owner's words;
it failed the package once on a fresh-home uninstall walkthrough; it pre-registered the live
induction criteria *before* the qualifying event so the builder could not grade his own receipt;
and it caught the builder asserting, after a context seam, that review runs had never happened
when the shared worklog held them.

Date: 2026-08-15

## Post-release feedback (non-blocking)

- Human walkthrough status: `not yet tested`
- Evidence or issue link: none. No outside human has installed this package. Recording it as
  untested rather than omitting the line — an absent status reads as a passed one.
