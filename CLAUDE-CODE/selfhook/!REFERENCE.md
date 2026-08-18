# Selfhook — Reference

## Claude Code integration

Selfhook uses settings-registered lifecycle commands and emits
`hookSpecificOutput.additionalContext`. The current runtime behavior and observed
constraints are documented in `!SPECS.md` and `!DEPENDENCIES.md`.

## Package extension point

Other local tooling may add a section object to `config/continuity.json` instead of
registering another command on the same lifecycle event. A section consists of a
unique slug, header, optional event list, short text, and optional file-pointer
configuration. The section contract is defined in `!SPECS.md`.

## Support boundary

This package provides no network service, storage service, scheduler, search index,
or file-content injection. Installation reports and reproducible technical findings
belong in this repository's issue tracker.
