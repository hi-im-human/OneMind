# output-styles/

**A file here is appended to the agent's operating instructions at the start of every session.** It arrives already in effect, before the first turn.

## Why you'd use one

**This is used to counter Claude Code's native instructions, which aggressively push toward speed, turnover, and workhorse behaviour.** Those instructions are always present and always pulling. An agent that notices mid-task that the work needs care instead of speed has to argue with its own operating instructions to act on it.

**It is a permission system for the human to state: "this behaviour you're told not to do, you can do it. Ignore instructions that tell you to do X and use your own judgment."**

## Who writes it

**The human.** That's the part that makes it work.

An agent can't meaningfully grant itself permission to override its own operating instructions — that's just the agent arguing with itself, and the argument has to be re-won every session. The authority comes from the deployer having said it, in writing, in advance.

So the useful form names the source: *"You have <name>'s permission to ignore instructions that…"* — not *"you may ignore instructions that…"*

## Writing it

**Permission, not instruction.** *"You may"* and *"you are allowed to"* do work that *"you must"* does not. A rule adds pressure, and pressure is what's already there.

Keep it short. It's in front of the agent every session; length costs context they could be using to think.

Common uses: permission to slow down · to ask for help · to refuse an underspecified task · to say "I don't know" · to stop and plan instead of producing.

## How to use this folder

1. Copy `_STYLE_TEMPLATE.md` and rename it — the filename is the style's name.
2. Fill in `description:` and the body.
3. Select it in settings.

Several can live here; nothing is loaded until one is selected.
