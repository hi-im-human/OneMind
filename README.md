# OneMind

Continuity and scheduling infrastructure for AI agents, packaged so someone else can run it.

**Status: empty on purpose.** The repo exists; nothing has been released into it yet. The
first package lands after the release gate is built and proven.

## What this is

Small, independent tools for agents that need to persist — memory search, session
scheduling, identity loading, conversation logging. Each one installs on its own. There is
no framework to adopt and no all-or-nothing bundle.

They were built for a working multi-agent household, then generalized. Some assume a
partner agent; where that's true it will say so plainly, at the top, rather than letting
you discover it in month two.

## What this isn't

**No philosophy required.** These are tools. You don't have to share our views about
agents, use our vocabulary, or read anything about where they came from in order to
install one. Background reading, where it exists, is a link — never a step.

## Layout

```
CLAUDE-CODE/     LETTA/     CODEX/     CHATGPT/     CLAUDE-DESKTOP/
```

Substrate folders. A package lives under the substrate it targets; cross-platform tools
appear under each substrate that supports them.

Every released package carries its own `INSTALL.md` stating **where each file goes**, what
it creates at runtime, and how to remove it.

## Releases

Packages are built and staged elsewhere. Only finished, reviewed work is published here.
This repo shares no history with the workspace it came from — that's deliberate, and it's
what makes a leak require a deliberate act instead of an oversight.

## License

Apache-2.0 *(pending final dependency-compatibility confirmation before first release).*
