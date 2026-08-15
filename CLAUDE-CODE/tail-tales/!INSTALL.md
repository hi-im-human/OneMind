# Tail Tales — Installation

- `<PACKAGE_ROOT>` — absolute path where you put this package
- `<WORKSPACE>` — the directory the agent runs in (where its `.claude/` lives)

## Quick install

1. Put the package somewhere stable. It is never modified at runtime.
2. Add one `PostCompact` hook to `<WORKSPACE>/.claude/settings.json` (below).
3. Arrange for the agent to **read** the tale after compaction — see *Verify*, and
   `!DEPENDENCIES.md`. Without this the package writes a file nobody opens.

```json
{
  "hooks": {
    "PostCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"<PACKAGE_ROOT>/src/post_compact_shared.py\" --output-dir \"<WORKSPACE>/.brain\" --output-name \"SESSION_TALE.md\""
          }
        ]
      }
    ]
  }
}
```

## Requirements

- Claude Code with `PostCompact` hook support
- Python 3.8+ on the runtime's PATH (no `tzdata` or timezone database needed)
- A writable output directory

No network, no credentials, no external services, no other packages required.

## Package home

`<PACKAGE_ROOT>/` — `src/post_compact_shared.py` plus these docs. Nothing here is written to
at runtime.

## Runtime home

The hook runs wherever Claude Code spawns it. It takes everything it needs from the
`PostCompact` stdin payload: the transcript path, and `cwd`.

**The agent's display label comes from the `cwd` basename**, with leading non-letter
characters stripped (`⚙️Ada` → `Ada`). Pass `--agent NAME` to override.

## Continuity data home

`<WORKSPACE>/.brain/SESSION_TALE.md` by default — set by `--output-dir` and `--output-name`.

The file is **overwritten on each compaction**. It is a snapshot of the turns nearest the most
recent seam, not an accumulating archive.

## Generated files

| path | when | by |
|---|---|---|
| `<WORKSPACE>/.brain/SESSION_TALE.md` | every compaction | the hook |
| `<WORKSPACE>/last_session_tail.err.log` | **only on failure** | the hook |
| one hook entry in `<WORKSPACE>/.claude/settings.json` | install | you |

## Options

| flag | default | effect |
|---|---|---|
| `--output-dir` | the workspace | where the tale is written |
| `--output-name` | `last_session_tail.md` | the tale's filename |
| `--agent` | derived from `cwd` basename | overrides the display label |

## Verify

After the next compaction:

1. **The file exists and is recent.** Check the mtime on your `--output-name` file.
2. **The content matches what you were actually doing** before the seam. This is the check
   that catches a wrong-source-file bug — a tale can be present, well-formed, and drawn from
   the wrong transcript. **Read it, don't just stat it.**
3. **The agent actually received it.** Writing is not delivery. If nothing causes the agent to
   open the file, the install is silently useless — see `!DEPENDENCIES.md`.
4. On failure, check `last_session_tail.err.log`. ⚠️ **It is NOT written beside the tale.** It goes
   to the runtime's `cwd` — the workspace root — while `--output-dir` moves only the tale. If you
   point the tale at a subdirectory, the two land in different places. Errors go to that file, never
   to the agent.

## Uninstall or rollback

**Undo the install steps in reverse. All three of them — including step 3.**

1. **Remove or disable the read mechanism you arranged at install step 3.** Whatever you set up to
   make the agent open the tale — a line in its operating document, a companion hook's pointer, a
   skill reference — now aims at a file that is about to stop existing.
   ⚠️ **Remove only the Tail-Tales-specific instruction.** If it lives inside a larger operating
   document, edit out that line or clause; do not delete the document or unrelated content around
   it.
2. Remove the `PostCompact` entry from `<WORKSPACE>/.claude/settings.json`. If that leaves the
   hooks object empty, an empty object is fine — leave the file valid.
3. Delete `<PACKAGE_ROOT>/`. Confirm the directory is actually gone, not merely emptied.
4. Optionally delete `<WORKSPACE>/.brain/SESSION_TALE.md` and
   `<WORKSPACE>/last_session_tail.err.log`.

**Verify by object, not by intention:** the package root absent, no Tail-Tales read instruction
remaining, `settings.json` still valid, and anything you had in the workspace beforehand untouched.

⚠️ **Step 1 is the one that gets missed, and it is why this section is ordered this way.** An
earlier version of this guide listed only steps 2–4 and claimed *"removing the hook entry is a
complete rollback on its own."* **That was false for every installation that followed the
instructions**, because step 3 of the install is mandatory — the package writes a file nobody
reads without it. A fresh installer found the residue: an operating document still directing an
agent to read a tale in a package that had been deleted.

The underlying slip is worth naming, because it is easy to repeat: *"the package writes no config"*
is true, and it is a claim about **the software**. A rollback section has to make a claim about
**the installation** — and this installation requires you to write config. See `!DECISIONS.md`.
