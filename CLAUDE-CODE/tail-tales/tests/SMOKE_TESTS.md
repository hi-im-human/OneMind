# Tail Tales — Smoke tests

Run from package root:

```text
python tests/smoke_test.py
```

The suite uses synthetic lifecycle payloads and a temporary sandbox. It does not read
a target workspace or invoke a live Claude Code PostCompact callback.

## Required assertions

| Case | Expected result |
|---|---|
| seeded output plus empty transcript | existing output remains byte-identical |
| ordinary post-boundary transcript | tail is written with expected text |
| missing `transcript_path` | no tail write; cwd error log when cwd exists |
| nonexistent transcript path | no tail write; cwd error log |
| missing cwd | stderr diagnostic; no output or error-log path assumption |
| unknown CLI flag | current parser ignores it; documented as a compatibility hazard |
| compaction boundary | pre-boundary turns excluded |
| reasoning block | excluded from output |
| display label | derived from cwd basename when not overridden |
| channel envelope and runtime noise | envelope text retained; runtime noise excluded |
| malformed timestamp | output uses fallback timestamp; command succeeds |
| output over `HARD_CAP` | header and newest content retained with trim marker |
| one turn over `HARD_CAP` | retained fragment is explicitly marked |
| absent output directory | directory is created and output is written |

## Live runtime requirement

Before declaring an installation ready, trigger a real PostCompact event in the target
workspace. Confirm the command ran, the configured output file was written, and its
contents match the post-boundary source transcript. Record that receipt separately;
the synthetic suite cannot provide it.
