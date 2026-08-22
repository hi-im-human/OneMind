---
description: Shared public library of technical packages and installable workspace layouts for agent runtimes.
---

# OneMind

Technical packages for agent runtimes: lifecycle hooks, transcript-tail capture,
schedule tooling, directory layouts, and related installation support.

## Directory

<!-- BEGIN GENERATED PACKAGE DIRECTORY -->
- [_meta/](_meta/README.md) — Repository maintenance scripts and regression suites; not a runtime installation surface.
- **CLAUDE-CODE/**
  - [discord-bot-to-bot-visibility/](CLAUDE-CODE/discord-bot-to-bot-visibility/!README.md) — Claude Code Discord-plugin patcher that preserves self and unknown-bot filtering while allowing explicitly allowlisted bot messages to reach the existing access gate.
  - [freestyle-beats/](CLAUDE-CODE/freestyle-beats/!README.md) — Durable personal scheduler for Claude Code session-scoped cron work, with local state recovery and maintenance.
  - [selfhook/](CLAUDE-CODE/selfhook/!README.md) — Claude Code lifecycle renderer, PreCompact shallow memory-directory generator, and configuration validator.
  - **skills/**
    - [agent-sync/](CLAUDE-CODE/skills/agent-sync/README.md) — Claude Code operator workflow for checkpointing an agent Keep repository with explicit Git failure reporting.
  - [tail-tales/](CLAUDE-CODE/tail-tales/!README.md) — Claude Code PostCompact transcript-tail hook that writes bounded Markdown continuity tails.
- **CROSS-COMPATIBLE/**
  - [loop-doctor/](CROSS-COMPATIBLE/loop-doctor/!README.md) — Cross-runtime diagnostic framework for identifying and responding to recurring agent loops.
- **OneMind_Directory_Template/**
  - [Agent_Homes/](OneMind_Directory_Template/Agent_Homes/README.md) — Container for independently owned agent runtime workspaces.
    - [_AGENT_TEMPLATE/](OneMind_Directory_Template/Agent_Homes/_AGENT_TEMPLATE/README.md) — Renamable Claude Code runtime workspace template with private memory and lifecycle coordinates.
      - [.chat_logs/](OneMind_Directory_Template/Agent_Homes/_AGENT_TEMPLATE/.chat_logs/README.md) — Runtime conversation-export archive, including configured Lumberjack output locations.
      - **.claude/**
        - [hooks/](OneMind_Directory_Template/Agent_Homes/_AGENT_TEMPLATE/.claude/hooks/README.md) — Claude Code lifecycle hook scripts registered through settings.json.
        - [skills/](OneMind_Directory_Template/Agent_Homes/_AGENT_TEMPLATE/.claude/skills/README.md) — Claude Code skill directories, each containing a named SKILL.md procedure.
  - [Energy_Co/](OneMind_Directory_Template/Energy_Co/README.md) — Shared machine-local installation root for automation packages—hooks, tools, agents, and operational infrastructure.
<!-- END GENERATED PACKAGE DIRECTORY -->

This block is generated from `description:` frontmatter in tracked package
`README.md` or `!README.md` files. Regenerate it from the repository root with:

```text
python _meta/generate_readme_tree.py --repo . --write --quiet
```

Each package is independently installable. Its package documentation defines runtime
requirements, installation paths, configuration, verification steps, and uninstall
behavior.

## Release boundary

Only reviewed package surfaces belong in this repository. Do not treat a package as
release-ready without the verification evidence its release checklist requires.

## License

Apache-2.0. See `LICENSE`.
