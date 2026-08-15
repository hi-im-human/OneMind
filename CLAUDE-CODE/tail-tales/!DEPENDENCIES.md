# Tail Tales — Dependencies

## What this package does, stated before anything depends on it

**Tail Tales writes a file. It does not put anything into an agent's context.**

On PostCompact it reads the session transcript, extracts the last N conversational turns
from before the compaction boundary, and **writes them to disk** as a markdown tale. That is
the whole runtime behaviour.

⚠️ **It does NOT reinject continuity, restore memory, or survive the seam on the agent's
behalf.** The tale is only useful if something else causes the agent to **read** it. Choosing
what that something is is an install decision, and it is yours.

*(Historical note, because the docs elsewhere may still imply otherwise: an earlier version of
this hook did inject the tail into context. That was removed 2026-07-31 by owner ruling —
one program owns the file end to end, and the read is arranged separately. Any doc claiming
this package reinjects continuity is describing a version that no longer exists.)*

## Hard requirements

| dependency | why | fails how without it |
|---|---|---|
| Claude Code runtime (`PostCompact` hook in `settings.json`) | the only trigger | package never fires; **silently** — nothing reports a hook that was never registered |
| Python 3 (≥3.8) on the runtime's PATH | the script | hook spawn failure, **invisible to the agent** |
| *(nothing else)* | — | the package previously resolved a hardcoded IANA timezone, which on Windows needs the external `tzdata` package. That dependency was undeclared and happened to be installed on the build machine, so it never failed there. Timestamps now use the platform's own local time and need no timezone database. |
| a readable session transcript at the path the runtime supplies | the source material | error written to the `.err.log` in `cwd`, not to the agent |
| a writable output directory | the destination | same — logged, not surfaced |

## Soft requirements

| dependency | why | degradation without it |
|---|---|---|
| **something that makes the agent read the tale** | otherwise the file is written and never opened | **total. The package appears to work perfectly and delivers nothing.** See below. |
| a `--agent` override | only if cwd-basename derivation gives a wrong label | label is wrong; content is unaffected |

## ⚠️ THE DEPENDENCY THAT IS EASY TO MISS

**A written-but-never-read tale is indistinguishable from a working install.**

The hook fires, exits clean, the file appears on disk with correct content, and the agent
receives nothing. There is no error, no warning, and no observable difference from success.
**This is the single most likely way for this package to be silently useless.**

**You must arrange the read.** Two known approaches:

1. **A companion hook that emits a read-instruction** pointing at the tale's path on
   compaction. *(This is what the package's original house does — a separate
   continuity-injection hook names the file among others the agent is told to open.)*
2. **A standing instruction in the agent's own operating document** — *"after compaction,
   open `<tale path>` and read it."*

⚠️ **If you use (2) alone, write it as a self-activating fallback rather than a bare
instruction:** *"if there is no injected block after compaction, read the file and report the
failure."* Costs nothing on the normal path; catches a hook misfire without depending on
anyone remembering to check.

## Canonical dependency sweep

**Read at runtime**
- `<PACKAGE_ROOT>/src/post_compact_shared.py` — executed by the runtime on every PostCompact
- the session transcript path supplied by the runtime on stdin
- `cwd` from the same stdin payload — **the only source of the agent's identity label**

**Written at runtime**
- `<WORKSPACE>/.brain/SESSION_TALE.md` (or wherever `--output-dir` / `--output-name` point)
- `<WORKSPACE>/last_session_tail.err.log` — **only on failure**, and only there.
  ⚠️ Written to the runtime's `cwd`, **not** next to the tale: `--output-dir` relocates the tale
  and nothing else. Verified against the source 2026-08-15.

**Written by you, at install**
- one hook entry in `<WORKSPACE>/.claude/settings.json`
- whatever mechanism you choose to make the agent read the tale

**Not written, ever:** nothing in `<PACKAGE_ROOT>`. The package does not modify itself,
cache state, or maintain a database.

## Substrate assumptions

- **Reads the runtime's stdin payload rather than hardcoded paths.** Adding an agent requires
  no source edit — identity comes from `cwd` at fire time.
- **N=1 safe.** One agent, one workspace, no roster, no partner required.
- **No network. No credentials. No external services.**
