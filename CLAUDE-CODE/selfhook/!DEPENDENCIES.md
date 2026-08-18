# Selfhook — Dependencies

## Required

| Dependency | Purpose | Behavior when unavailable |
|---|---|---|
| Claude Code lifecycle hooks | command delivery | package is inapplicable |
| Python 3.8+ on the runtime PATH | executes both scripts | no hook payload from the command |
| `config/continuity.json` | section and cap configuration | error-only payload |
| `<workspace>/.memory/MEMORY.md` with marker pair | identity-directory target | generator refuses without writing |

## Optional integration

| Integration | Purpose | Behavior when absent |
|---|---|---|
| Existing configured files | valid pointer targets | configuration error for absent targets |
| Commit or sync workflow | invokes `check_limits.py` | caps are not automatically enforced |

## Runtime reads

- `<PACKAGE_ROOT>/src/selfhook.py`
- `<PACKAGE_ROOT>/src/identity_directory.py`
- `<PACKAGE_ROOT>/config/continuity.json`
- Configured pointer and cap target paths for validation.
- `<workspace>/.memory/` root, its direct Markdown files/folders, and direct child
  entries during directory generation.

`identity_directory.py` writes only the generated marker block inside
`<workspace>/.memory/MEMORY.md` when called with `--write`; renderer/checker behavior
is read-only. Installation creates local configuration and lifecycle registrations.

## Observed runtime constraints

1. Hook output beyond approximately 2–5 KB can be truncated while reporting success. The package therefore uses a 1,800-character payload budget.
2. `hookSpecificOutput.hookEventName: "PostCompact"` is dropped by the verified runtime version; both registrations emit `"SessionStart"`.
3. Output from multiple commands on the same lifecycle event can be concatenated without a delimiter. Selfhook provides one sectioned payload.
