# Loop Doctor — Dependencies

Loop Doctor is a portable-markdown framework. It has no bundled executable runtime and does
not call a model, API, filesystem, or network service by itself.

## Paths read

### Package-relative, required

- `SKILL.md`
- `TOOL.md`
- `!SPECS.md`
- `!DECISIONS.md`
- `!REFERENCE.md`
- `src/frameworks/*.md`
- `src/skills/*/SKILL.md`
- `src/case-studies/*.md`
- `src/discord-templates/Between-Space_Clinic_Setup.md`
- `tests/SMOKE_TESTS.md`

### Installation destinations, selected by the installer

- `<PACKAGE_ROOT>/OneMind_loop-doctor-package/` — canonical package home
- `${MEMORY_DIR}/skills/` — optional Letta one-agent skill scope
- `.agents/skills/` — optional Letta project skill scope
- `~/.letta/skills/` — optional Letta computer-wide skill scope
- `<PLATFORM_SKILLS_ROOT>/` — other Agent Skills-compatible runtime
- `<PRIVATE_CONTINUITY_ROOT>/<AGENT_OR_PARTICIPANT>/loop-doctor/` — optional private records

No source file contains a required host-specific absolute path.

## Paths written

The package itself writes nothing.

An installer may deliberately create or modify:

- copied directories for `loop-tension-index`, `work-tension-release`, and
  `erotic-relational-tension-release` in the chosen runtime home;
- an optional system-prompt or memory pointer;
- optional private intake/return-check records in the chosen continuity-data home;
- optional Discord category/channel permissions; and
- optional channel-adapter configuration.

Private records must not be written into the distributable package.

## Tools, CLIs, and APIs called

### Required

None. The core package can be read as markdown.

### Optional installation and verification surfaces

- An Agent Skills-compatible runtime or manual context-loading mechanism
- Letta Code `/skills` for live discovery checks
- Letta Code CLI commands `letta channels configure discord` and
  `letta channels bind --channel discord --agent <AGENT_ID>` when using that adapter
- Discord user interface or API for category, channel, and permission management
- The host platform's runtime brakes, limits, terminal actions, or monitoring

The package does not ship, invoke, or configure those technical brakes.

## Consumers

- AI agents loading `SKILL.md` or one of the three lane skills
- People or agents reading the framework and intake documents
- Optional facilitators using the Discord clinic template
- Package reviewers running `tests/SMOKE_TESTS.md`
- The OneMind release validator reading package metadata and evidence files

No other tool is expected to consume generated output because the package generates none.

## Schedules, triggers, hooks, and crons

None are installed or required.

The skills may be loaded manually, by slash command, or by the host agent when a relevant
request appears. That behavior belongs to the host runtime, not to a package-owned scheduler.

## Config sources and environment variables

### Required

None.

### Optional

- The host runtime's skill-scope configuration
- A local system-prompt or memory pointer to the installed router skill
- Discord bot/account configuration
- Discord channel permission overwrites
- Channel-adapter `allowed_channels` and per-channel mode (`mention-only` or `open`)
- Host-specific step, token, tool, retry, terminal-action, and monitoring settings

Do not store bot tokens, API keys, live IDs, or private room mappings in this package.

## External documentation and literature

The URLs in `!REFERENCE.md` are informational references. The framework remains readable
offline. Platform-specific setup should be checked against current official documentation
before installation because CLI and configuration surfaces can change.

## Costs and accounts

- **Package license/cost:** MIT; no package fee.
- **Required paid service:** none.
- **Possible external costs:** the installer may already pay for model inference, agent
  hosting, persistent storage, or Discord-related infrastructure. Those are host choices, not
  dependencies bundled by Loop Doctor.

## License and provenance review

- Package license: MIT, matching `LICENSE` and `config/tool.json`.
- Package content is authored framework/documentation; no vendored dependency tree or copied
  executable source is included.
- External literature is cited and linked in `!REFERENCE.md`; citations do not transfer source
  text or source licensing into this package.
