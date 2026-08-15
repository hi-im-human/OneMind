# Tool Card: tail-tales

## What it does

A `PostCompact` hook. Reads the session transcript at the compaction boundary and writes the last
~40 conversational turns to a markdown file, verbatim. It preserves the exact wording that a
compaction summary paraphrases away.

**It writes a file. It does not put anything into an agent's context.**

## Use when

- An agent needs the literal wording from before a compaction, not a summary of it.
- Continuity across the seam matters more than context economy.
- You can arrange, separately, for something to make the agent read the file.

## Do not use when

- You expect it to restore continuity on its own. It cannot — the read is your job to arrange.
- You need an accumulating history. One file, overwritten every compaction.
- You need failures surfaced to the agent. They go to a log file it will not open by itself.

## Inputs

Not called directly. The runtime supplies a JSON payload on stdin.

| Input | Required | Meaning |
|---|---:|---|
| `transcript_path` (stdin) | yes | source transcript, JSONL |
| `cwd` (stdin) | yes | workspace — error-log destination and default agent label |
| `--output-dir` | no | where the tale is written (default: `cwd`) |
| `--output-name` | no | tale filename (default: `last_session_tail.md`) |
| `--agent` | no | overrides the label derived from the `cwd` basename |

⚠️ Unrecognised flags are **silently accepted and ignored** — no error, no warning, exit 0. A
stale registration is indistinguishable from a live one.

## Returns

Nothing on stdout. A markdown file at the configured path: header (agent, write time, source
transcript, turn count), separator, then the turns.

## Safety

- **Read-only:** no — writes one file.
- **Writes files:** yes. The tale; plus `last_session_tail.err.log` in `cwd` on failure only.
- **Destructive:** the tale is **overwritten every compaction**. It is a snapshot, not an archive.
  It will not overwrite a good tale with an empty one — the module returns before the write when
  no turns extract.
- **Requires confirmation:** no.
- **Network / credentials:** none. No external services.
- **Notes:** every failure path exits 0 and writes nothing, so the runtime is never broken by a
  failure here. The cost is that failure is invisible from inside the agent.

## Related

`SKILL.md` for how an agent should read a tale. `!DEPENDENCIES.md` for the thing you must arrange
yourself — without it the package appears to work perfectly and delivers nothing.
