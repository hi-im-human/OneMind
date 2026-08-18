---
name: agent-sync
description: Checkpoint an agent's Keep repo with one command — stage everything not gitignored, optionally enforce identity-file size caps, commit, push, and report command success or failure. Use on demand or at git-state reminder beats.
---

# Agent Sync

One command to checkpoint an agent's Keep. Stages everything `.gitignore` doesn't exclude,
commits, pushes, and reports command success or failure.

## ⛔ It does not scan for secrets

**This skill has no secret detection and makes no security claim.** `.gitignore`
controls which paths this command excludes from repository history.

An earlier filename-based secret check was removed. It did not inspect file contents and
could not provide content-scanning coverage:

- it matched **filenames, never contents** — a token pasted inside `notes.md` was not detected;
- it missed obvious real ones (`.env.local`, `.ppk`, `id_ecdsa`);
- it blocked ordinary files whose names merely contained the words — `tokenization`,
  `secretary`, `passwordless`, `credential-handling`;
- it could block deletion of an already-tracked file;
- and `-Preview` did not reach the blocking path.

Use a content-aware secret scanner in a pre-commit hook when secret scanning is required.
This package performs git synchronization only.

## Setup

| what | parameter | env var | required |
|---|---|---|---|
| the Keep (git repo root) | `-KeepRoot` | `AGENT_KEEP_ROOT` | **yes** |
| identity-file limit checker | `-CheckScript` | `AGENT_LIMIT_CHECKER` | no |

`-AgentName` defaults to the Keep folder's name and only affects the commit message.

The remote is whatever `git` already has. **This script never sets, changes, or assumes a
remote** — run `git remote add origin <your repo>` once, and it just calls `git push`.

## Commands

```powershell
# preview — shows what would be staged, changes nothing
... \agent-sync.ps1 -KeepRoot "<keep>" -Preview

# checkpoint
... \agent-sync.ps1 -KeepRoot "<keep>"

# custom message / no push
... \agent-sync.ps1 -KeepRoot "<keep>" -Message "sync: meaningful change"
... \agent-sync.ps1 -KeepRoot "<keep>" -NoPush
```

## Behavior

1. Check status. Clean tree → compare against the branch's own upstream and push anything
   unpushed, then exit.
2. `git add -A` — `.gitignore` does the excluding.
3. Optional identity-limit check, if you configured one.
4. Commit.
5. Push, unless `-NoPush`.

**Every git call's exit code is checked.** If commit or push fails, the script says so, says
the Keep is not checkpointed, and exits non-zero. It does not print `Done.` after a failure —
which it used to, and which is the reason this file now says so explicitly.

**Upstream comparison uses the current branch's own upstream (`@{u}`), not `origin/HEAD`.**
`origin/HEAD` can be missing or stale in perfectly valid repos, and when it is, a naive check
reports "nothing to do" while real commits sit unpushed. If no upstream is set, the script
tells you and stops rather than guessing.

## Optional: identity-file size caps

If your agent keeps persona/identity files with per-file character limits, point
`-CheckScript` at a checker that takes `--keep <path>` and exits non-zero when something is
over.

**If you configure one and the file is missing, this aborts.** A configured check that
silently no-ops is indistinguishable from one that passed.

The checker receives the configured per-file limits. This package invokes the checker and
aborts when it returns a nonzero exit status.

## Guardrails

- Never force push.
- Use `-Preview` when a changed file surprises you.
- **Committing by hand does not run the configured identity check.**
- Untested outside Windows/PowerShell.
