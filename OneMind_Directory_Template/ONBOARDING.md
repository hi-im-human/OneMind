# OneMind directory template — installation

This directory is a portable layout for shared package code and per-runtime
workspaces. Rename `OneMind_Directory_Template` before use; no package depends on the
template directory name.

## Layout

```text
<root>/
├── Human-Decisions.md         operator decisions required during installation
├── Energy_Co/               shared package code
└── Agent_Homes/             one runtime workspace per configured agent
```

`Energy_Co/` contains shared package copies. Each entry under `Agent_Homes/` is a
separate workspace and may be versioned independently.

## Setup sequence

1. Rename `_AGENT_TEMPLATE` to the runtime workspace label.
2. Choose the workspace location and any version-control arrangement.
3. Select a memory path or link strategy appropriate to the target runtime.
4. Install packages by following each package's `!INSTALL.md` and `!DEPENDENCIES.md`.
5. Record installation choices that require an operator in `Human-Decisions.md`; show
   the shared record early and continue unblocked branches while answers remain open.

## Installation boundaries

- Package code may write only paths declared in its installation documentation.
- Package state and registrations must remain in declared package or runtime paths.
- Do not overwrite a nonempty directory with a link. Move or back up existing content
  before changing the path type.
- Do not place credentials in Markdown files or chat transcripts. Configure secrets in
  the relevant secret manager, environment, or service configuration.

## Runtime-specific paths

Claude Code uses `.claude/settings.json` for hook registration. A `.memory` directory
may be a local folder or a runtime-specific link. Confirm the target runtime's current
path and link behavior before making either change.

## Optional package-managed paths

Some packages create their own state directories at installation time. Do not precreate
an undocumented state directory: its existence must not imply a package is installed.
