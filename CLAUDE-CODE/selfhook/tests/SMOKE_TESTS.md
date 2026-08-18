# Selfhook — Smoke Tests

Run these after install (`!INSTALL.md`) in the order given. Each test names its
expected output; a test whose expectation you didn't observe is a FAIL even if
nothing errored.

## 1. Hook syntax + output contract (no runtime needed)

```
python "<PACKAGE_ROOT>/src/selfhook.py" --config "<PACKAGE_ROOT>/config/continuity.json" --event SessionStart < /dev/null
python "<PACKAGE_ROOT>/src/selfhook.py" --config "<PACKAGE_ROOT>/config/continuity.json" --event PostCompact  < /dev/null
```
*(Windows: pipe from `NUL`.)*

**Expect:** each prints exactly one line of JSON containing
`"hookEventName": "SessionStart"` (BOTH invocations — the runtime drops
`"PostCompact"`-named payloads, see `!DECISIONS.md`) and a non-empty
`"additionalContext"` holding your sections under `=====` banners.
**FAIL if:** any traceback, a `SELFHOOK CONFIG ERROR` payload (fix the config —
that behavior is tested next, but here it means your install config is wrong), or
an empty payload when sections subscribe to the event.

## 2. Error-only failure policy (planted failure)

Copy your config to a scratch file; inside it, point one section's `read_files` at a
file that does not exist. Run test 1's first command against the scratch config.

**Expect:** payload headed `SELFHOOK CONFIG ERROR — HOOK DID NOT RENDER`, an error
line naming the section and missing file, and **none of your valid sections
rendered** — errors are never mixed with partial content.
**FAIL if:** valid sections render alongside the error, or the missing file is
silently omitted. Delete the scratch config after.

## 3. Containment (planted failure)

In a scratch config, set one section's `read_files.dir` to `".."`. Run test 1's
first command against it.

**Expect:** error-only payload with `'dir' '..' escapes the workspace — rejected`.
No pointer outside the workspace appears anywhere in the output.
**FAIL if:** the hook renders a pointer to a path outside the workspace.

## 4. Budget cut is marked (planted failure)

In a scratch config, give one section a `text` of ~3,000 characters. Run test 1's
first command against it.

**Expect:** output length ≤ 1,800 chars of `additionalContext`, ending in the
explicit `[SELFHOOK: payload exceeded its budget and was cut HERE...]` marker.
**FAIL if:** the payload is cut with no marker, or exceeds the budget.

## 5. Settings registration is intact

Open `<WORKSPACE>/.claude/settings.json` and confirm it parses as JSON.

**Expect:** valid JSON; both hook entries present with absolute paths and the right
`--event` per registration.
**FAIL if:** parse error — one bad comma disables ALL hooks silently (`!BUGS.md`).

## 6. The banner arrives live

Change into the workspace **explicitly**, then run the receipt-producing headless
session (one command, evidence directly in its output):

```
cd <WORKSPACE>          # PowerShell: Push-Location "<WORKSPACE>"
claude -p "Reply with the exact text of any session-start banner in your context." --output-format stream-json --include-hook-events --verbose
```

The stream output IS the receipt — two fields, both mandatory before any verdict,
PASS or FAIL:

1. the `init` event's `cwd` equals `<WORKSPACE>` — a session started anywhere
   else reads a different `settings.json`; its no-banner result is an **invalid
   test**, not a failure, and your own launch report does not count as the receipt;
2. a `hook_response` event carrying the Selfhook payload (exit 0, the banner in
   `additionalContext`).

*(Ordinary interactive `claude` from the workspace is the normal usage launch and
should also show the banner — but it produces no machine receipt, so the verdict
comes from the stream command above.)*

**Expect:** `init.cwd` = workspace; `hook_response` present; the session's reply
quotes your sections' banner blocks (`===== ... =====`) with your file lists —
compare against test 1's output. This is the ONLY test that verifies delivery;
payload is not receipt.
**FAIL if:** the cwd receipt confirms the workspace and there is still no
`hook_response`/banner (check test 5, then that `python` resolves on the runtime's
PATH, then the hook paths), or the received text is cut without the marker (the
transport floor has moved — see `!BUGS.md`, lower `PAYLOAD_BUDGET`).

## 7. Checker enforces caps — both directions

```
python "<PACKAGE_ROOT>/src/check_limits.py" --config "<PACKAGE_ROOT>/config/continuity.json"
```

Run once with all capped files within limits. Then temporarily over-fill one capped
file past its limit and run again. Then, in a scratch config, misspell one cap's
`path` and run against that.

**Expect:** exit 0 → exit 1 with the over-limit report → exit 1 with
`file not found — a typo must not disable a cap silently`.
**FAIL if:** any of the three returns the wrong exit code — especially the typo
case returning 0, which is a cap silently turned off. Restore the file after.

## 8. Strict keys — a typo is never a silent no-op (planted failure)

Make two scratch copies of your config. In copy A, rename one section's `events`
key to `event`. In copy B, rename root `caps` to `cap`. Run **both** test 1's
first command **and** the checker against **each** copy (four runs total).

**Expect:** copy A → hook error-only payload naming the unknown key and the
allowed set; checker exit 1 with the same error. Copy B → hook error-only payload
including `missing required 'caps'`; checker exit 1 with the same missing-`caps`
error. The checker rejects exactly what the hook rejects.
**FAIL if:** the `event` typo renders sections anyway (on every event), the `cap`
typo exits 0, or hook and checker disagree about either copy — a config the hook
refuses to render must not pass commit.

## 9. Directory targets rejected; checker matches the hook (planted failure)

In a scratch config: point one cap's `path` at a *directory*, and one section's
`read_files` pattern at the same directory. Run the hook and the checker against
it. Then run the checker once with `--workspace` given as a *relative* path to an
existing directory.

**Expect:** hook → error-only payload (`not a regular file` for both uses);
checker → exit 1 for the directory cap, and exit 1 (`must be an absolute path`)
for the relative workspace — the checker rejects exactly what the hook rejects.
**FAIL if:** a directory renders as a file pointer, the checker tracebacks instead
of failing cleanly, or the relative workspace returns 0.

## 10. Uninstall is clean — same receipt standard as install

Before uninstalling, record hashes of your continuity files (any hash tool; note
them down). Then follow `!INSTALL.md` uninstall (settings entries FIRST), and
rerun **test 6's exact receipt-producing command** from the workspace.

An absence verdict needs the same receipt a presence verdict does — a wrong-cwd
launch would falsely PASS this test (no banner, no errors) by the identical
mechanism that falsely FAILS install delivery. All four checks mandatory:

1. `init.cwd` equals `<WORKSPACE>` in the stream output — otherwise the run is an
   invalid test, not a PASS;
2. **no** Selfhook `hook_response` and no banner anywhere in the stream or the
   session's reply;
3. `<WORKSPACE>/.claude/settings.json` parses and contains no selfhook entries;
4. continuity-file hashes match the ones recorded before uninstall — untouched
   where they always lived.

**Expect:** all four hold.
**FAIL if:** any selfhook-shaped output or registration remains, or a continuity
file changed. **INVALID (rerun, not FAIL/PASS) if:** check 1's cwd receipt shows
the session started outside the workspace.

## 11. Generated memory directory — both directions

Run the packaged generator regression suite:

```text
python "<PACKAGE_ROOT>/tests/identity_directory_tests.py"
```

**Expect:** every listed case passes. The suite covers byte-preserved LF/CRLF/BOM
writes, malformed marker refusals, frontmatter postconditions, concurrent-edit
refusal, shallow `.memory` scope, direct child folders by name, depth-2 bait absence,
missing-description tolerance, and both-direction controls.

Then run the installed generator directly:

```text
python "<PACKAGE_ROOT>/src/identity_directory.py" --config "<PACKAGE_ROOT>/config/continuity.json" --write --quiet
```

**Expect:** `WRITTEN` or `UP TO DATE`. Inspect the marker block: root Markdown files,
top-level folder headings, and direct child entries appear; no depth-2 file appears.
**FAIL if:** a file outside the marker block changes, the command reports a refusal on
a correctly prepared target, or depth-2 content renders.

---

## Record of runs

| date | runner | environment | tests | result |
|---|---|---|---|---|
| 2026-08-13 | independent stateless agent (blind, docs-only onboarding) | Windows, PowerShell 7.6.4, Python 3.11.9, Claude Code 2.1.231, PYTHONDONTWRITEBYTECODE=1 | 1–10 in order | **PASS** — 2.93 hands-on minutes; exact-cwd stream receipts on tests 6 and 10 (install session `72fc24b3…` delivered the full banner; uninstall session `93dbb29c…` showed zero hook events and all four continuity hashes unchanged). PostCompact was not live-induced — scoped to direct invocation + registration evidence (tests 1, 5). Full report: reviewer-held blind-report.md |
