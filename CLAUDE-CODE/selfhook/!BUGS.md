# Selfhook — Known issues

## Open runtime constraints

- **Command spawn failures produce no hook payload.** Verify Python availability, package paths, settings JSON, and launch directory using `!INSTALL.md` smoke test 6.
- **Invalid `settings.json` can disable lifecycle hooks without a Selfhook error.** Parse the file after editing it.
- **The 1,800-character budget depends on observed runtime delivery behavior.** If a received payload is cut without the package marker, capture a runtime receipt and lower `PAYLOAD_BUDGET`.
- **The hook does not observe later file access.** It emits only the configured section text and file pointers.
- **The directory generator requires markers.** A `MEMORY.md` without the marker pair
  after frontmatter is refused and remains unchanged. Add the pair manually to an
  existing file or use `templates/MEMORY.md` in a new workspace.
- **The directory index is shallow.** Child folders are named but their contents are
  not rendered.

## Resolved design defects

- File-content injection was replaced with bounded pointers after truncation receipts.
- Multiple same-event outputs are consolidated as ordered sections.
- Invalid configurations emit error-only output rather than partial sections.
- The hook and checker use the same configuration validation contract.
- Escaping paths, directories as targets, unknown keys, and malformed cap targets are rejected as configuration errors.
