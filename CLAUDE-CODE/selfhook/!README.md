# Selfhook — Continuity Hook + Event Multiplexer for Claude Code Agents

## What it is

One SessionStart/PostCompact hook that tells an agent, at the moment its context is
fresh or freshly compacted, **which continuity files to read and in what order** — its
identity notes, its user notes, its last-session tail, whatever the config lists. It
emits a short instruction under loud banners. It never injects file contents.

It is also the **event multiplexer** for a workspace: when several tools want to say
something at session start, they contribute *sections* to Selfhook's one payload
instead of registering competing hooks whose outputs blend into an unreadable block.

A companion script, `check_limits.py`, enforces per-file character caps at commit time
from the same config — so continuity files that grow past their read-budget fail
loudly in the owner's workflow instead of silently bloating the ritual.

## Why pointers instead of content

Because the transport lies. Measured on this package's ancestor (2026-07-31): hook
output beyond ~2–5 KB is truncated by the runtime, the remainder spilled to a file
nobody is told about, and the hook reports success. Agents ran for days on one
truncated file believing they had their whole memory. A short read-instruction kept
below the observed floor is far less likely to be truncated — the floor is observed,
not contractual — and the agent reads the real files itself.

## Why one multiplexer

Because same-event hooks blend. Measured on the same ancestor (2026-08-01): multiple
hooks' output is concatenated into one context field with no delimiter — an agent
received another tool's directive running into its continuity instruction mid-line,
obeyed the loud opening, and never read its files. One hook owner, one ordered
payload, one banner per section: boundaries drawn on purpose.

## What's inside

```
src/selfhook.py                  the hook (multiplexer)
src/check_limits.py              commit-time cap enforcement, same config
config/continuity.example.json   copy → continuity.json, make it yours
```

## Requirements

- Claude Code (hooks registered in `settings.json`)
- Python 3 (≥3.8) on the runtime's PATH
- Continuity files worth reading — the config's example layout
  (`.memory/identity/` + a few named files) is a suggestion, not a requirement

## Quick start

See `!INSTALL.md`. Short version: copy the example config and edit it, register the
hook under SessionStart and PostCompact with `--event` naming each, wire
`check_limits.py` into your pre-commit or sync step, start a session, watch the
banner arrive.

## Honest limits

- The hook can only *instruct*; whether the agent actually reads the files is the
  agent's discipline. The banner design measurably improves the odds; it can't force.
- Caps are enforced only where you wire the checker. Unwired, they're documentation.
- Section text lives in config — treat it like code in review, because agents obey it.

## Status

The underlying *pattern* is proven — the pointer-not-payload model and banner have
run daily in a multi-agent installation since 2026-07-31. This multiplexer
packaging is new (2026-08-13); its verification evidence, including the blind
stateless-agent onboarding record, lives in `tests/release-receipt.json` and
`!RELEASE-CHECKLIST.md`. Human walkthrough not yet performed. Install feedback
welcome in this repository's Issues.
