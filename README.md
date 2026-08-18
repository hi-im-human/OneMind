# OneMind

Technical packages for agent runtimes: lifecycle hooks, transcript-tail capture,
schedule tooling, directory layouts, and related installation support.

## Layout

- `CLAUDE-CODE/`: packages targeting Claude Code.
- `CROSS-COMPATIBLE/`: packages with documented multi-runtime support.
- `OneMind_Directory_Template/`: optional workspace and shared-package layout. Start
  with `ONBOARDING.md`.

Each package is independently installable. Its package documentation defines runtime
requirements, installation paths, configuration, verification steps, and uninstall
behavior.

## Release boundary

Only reviewed package surfaces belong in this repository. Do not treat a package as
release-ready without the verification evidence its release checklist requires.

## License

Apache-2.0. See `LICENSE`.
