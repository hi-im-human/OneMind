---
description: Claude Code operator workflow for checkpointing an agent Keep repository with explicit Git failure reporting.
---

# Agent Sync

`agent-sync.ps1` stages non-ignored repository changes, runs an optional identity-limit
checker, commits, pushes, and returns command success or failure. It does not scan for
secrets; configure `.gitignore` and an external content-aware scanner separately when
that coverage is required.

Read `SKILL.md` for routine operation and `ONBOARDING.md` for first-time setup.
