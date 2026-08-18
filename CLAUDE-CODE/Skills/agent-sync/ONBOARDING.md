# agent-sync — onboarding

For a human and agent setting this up together for the first time. Assumes Windows,
PowerShell, and git. Takes about five minutes.

## What this is

Your agent keeps its memory, notes, and work in a folder. That folder is a git repo. This is
**one command that checkpoints it** — stages everything not gitignored, commits, pushes, and
tells you honestly whether that worked.

This command is intended for agent-run checkpoints, including scheduled invocations. It exits
nonzero when a git operation fails instead of reporting a completed checkpoint.

## ⛔ What it does not do

**It does not scan for secrets.** No security claim, at all. Exclusions are `.gitignore`'s job.

A previous version included a filename-based secret check. It did not inspect file contents,
missed names such as `.env.local` and `id_ecdsa`, matched ordinary filenames such as
`tokenization` and `secretary`, and could block deletion of an already tracked file.

Use a content-aware secret scanner in a pre-commit hook when secret scanning is required.

## Install

**1. Put the files somewhere stable.** They're never modified at runtime.

```
<somewhere>/agent-sync/
   agent-sync.ps1
   SKILL.md
   ONBOARDING.md
```

**2. Make the agent's folder a git repo, if it isn't.**

```powershell
cd "<the agent's folder>"
git init
git remote add origin <your repo url>
git push -u origin main      # sets the upstream the script compares against
```

Any host works. The script never touches your remote config.

**3. Write a `.gitignore` before the first run.** Use it to exclude credentials, caches, and
large files. **This is the only exclusion mechanism in this package** — there is no secret scan
behind it.

**4. Give the agent the skill.** Copy `SKILL.md` into its skills directory (for Claude Code:
`<agent folder>/.claude/skills/agent-sync/SKILL.md`).

## Running it

```powershell
# see what would happen, change nothing
powershell -NoProfile -ExecutionPolicy Bypass -File "<path>\agent-sync.ps1" -KeepRoot "<agent folder>" -Preview

# actually checkpoint
powershell -NoProfile -ExecutionPolicy Bypass -File "<path>\agent-sync.ps1" -KeepRoot "<agent folder>"
```

Tired of typing the path? Set it once:

```powershell
[Environment]::SetEnvironmentVariable("AGENT_KEEP_ROOT", "<agent folder>", "User")
```

## Situations you will actually hit

**"It says nothing to commit but I made changes."** They're covered by `.gitignore`.
`git status --ignored` will show you.

**"Push failed."** The script now says so and exits non-zero instead of printing `Done.` Fix
`git push` on its own first, then re-run.

**"No upstream set."** Run `git push -u origin <branch>` once. The script refuses to guess,
because guessing is how commits sit unpushed while a tool reports everything is fine.

**"Can I run this on a schedule?"** Yes. A scheduled invocation stages repository state present
at its run time, including files that are still being edited.

## Optional: identity-file size caps

If your agent keeps persona/identity files with per-file character limits and you have a
checker script, point `-CheckScript` at it. The checker interface accepts `--keep <path>` and
returns nonzero for an exceeded limit. Leave it unset and the step is skipped.

**If you set it and the file is missing, the script aborts** rather than continuing quietly. A
configured check that silently no-ops looks exactly like one that passed.

The configured checker evaluates its own per-file limits. Agent-sync invokes it before commit
and aborts on a nonzero result.

## What it does not do

- **No secret scanning.** Said three times in this document on purpose.
- **No history rewriting.** If something bad is already committed, use `git filter-repo` or
  BFG, and rotate the credential regardless.
- **No conflict resolution, no branching, no merge handling.** One repo, one branch, one
  command.
- **Untested outside Windows/PowerShell.** It has not been run on Mac or Linux, and I'm telling
  you that rather than letting you find out.
