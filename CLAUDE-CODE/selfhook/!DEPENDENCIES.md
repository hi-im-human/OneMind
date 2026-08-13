# Selfhook — Dependencies

## Hard requirements

| dependency | why | fails how without it |
|---|---|---|
| Claude Code runtime (hooks in `settings.json`) | delivery surface | package inapplicable |
| Python 3 (≥3.8) on the runtime's PATH | both scripts | hooks silently never fire (hook spawn failure is invisible to the agent) |
| `config/continuity.json` | the single source of truth | hook emits a visible CONFIG ERROR payload |

## Soft requirements

| dependency | why | degradation without it |
|---|---|---|
| continuity files the config points at | the whole point | **visible error, not silent skip** — a configured-but-missing file is a config error by design |
| a pre-commit or sync step to host `check_limits.py` | cap enforcement | caps become documentation until wired |

## Canonical dependency sweep

**Paths read at runtime**
- `<PACKAGE_ROOT>/src/selfhook.py` — **read by the runtime on every hook fire**
- `<PACKAGE_ROOT>/config/continuity.json`
- every file the config's sections point at (existence-checked, never content-read
  by the hook; contents are read by the *agent*, which is the design)

**Paths written / generated** (none by package code at runtime)
- `config/continuity.json` (you, from the example, at install)
- two hook entries in `<WORKSPACE>/.claude/settings.json` (you, at install)
- a checker call in your pre-commit/sync (you, at install)

**Tools / calls** — `python` (both scripts); nothing else

**Consumers / triggers** — the SessionStart and PostCompact registrations; your
pre-commit/sync step; and any consumer package whose docs add a section to the config

**Config source** — `config/continuity.json` (both scripts read it; the checker
imports `load_config` and the full `validate` from the hook — one contract, both
consumers reject the same configs, no code parsing code)

## What depends on this package

**The agent's `settings.json` registrations are live consumers of `src/selfhook.py`**
— moving or removing package home breaks the reminder silently (hook failure is
invisible). Consumer packages that contribute sections depend on the config surviving;
their sections die with it, visibly, as missing-file errors if they pointed at files.

## Runtime behaviors this package depends on (observed, not contractual)

1. **Hook output beyond ~2–5 KB is truncated while reporting success** (measured
   2026-07-31; the receipts are in `selfhook.py`). The 1,800-char budget assumes this
   floor. If the runtime raises it, the budget can rise — verify with a real session
   receipt first, never by running the script.
2. **`hookSpecificOutput.hookEventName` must be `"SessionStart"`** — `"PostCompact"`
   payloads are dropped silently (observed 2026-05-31, in continuous use since).
3. **Same-event hook outputs blend into one context field with no delimiter**
   (measured 2026-08-01) — the reason the multiplexer exists.
