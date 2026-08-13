# Selfhook — Decisions

**Newest first.**

## 2026-08-13 — Genericized as the OneMind event multiplexer

**Sections in config, not code.** The ancestor's file list and limits were constants in
the script; consumers integrated by editing source. Public shape: drop-in section
objects (`slug`/`header`/`events`/`text`/`read_files`), deterministic config order.
A consumer package (e.g. a scheduler) contributes one section and registers no hooks
of its own.

**No command source type.** Considered and rejected: sections that run a script to
produce their text. It reopens the payload-size hole the pointer model closed and
turns a casually-edited config into an execution surface.

**Visible failure over silent partial.** Duplicate slugs, malformed sections, and
over-budget payloads all render explicit markers in the payload itself. The ancestor's
history is a catalog of transports that reported success while delivering fragments;
this package refuses to add to it.

**Glob lists all matches.** The ancestor took the first sorted match (its relationship
file varied by name). Silent first-match is a wrong-file bug waiting for an installer
whose glob catches two; listing all is correct for a read list.

**Priority text resized.** The ancestor's notice said "Do NOT message the user … no
higher priority action" — unqualified dogma that would put ritual above an urgent
human. Now: reading comes before unrelated work; an urgent request, active correction,
safety issue, or explicit pause/hold outranks it.

**Dead injection path deleted.** The ancestor still carried its pre-2026-07-31
content-injection code after the rebuild to pointers. Shipping a dead payload path
invites exactly the revert its own comments warn against. The public package never had
it.

**Caps in config; checker imports the loader.** The ancestor's checker regex-parsed
the hook's Python source to share the limit table. One JSON config both scripts read
is the same single-source guarantee without code parsing code.

**Strict keys; regular files only; one workspace contract (third/fourth review
batches, same day).** Unknown keys at any config level are errors (`_comment`
exempt), and `sections`/`caps` must be explicitly present — reproduced typos
(`event`, `read_file`, `section`, `cap`) each yielded a healthy-looking partial
configuration or silently disabled caps. Every pointer/cap target must be a regular
file: a directory passed existence checks, then rendered as a "read this" pointer or
tracebacked the checker. `validate_workspace`/`validate_root`/`validate_caps` are
shared by both scripts so the checker rejects exactly what the hook rejects.

**Workspace containment; caps fail closed (second review pass, same day).** The
workspace must be absolute, and every rendered pointer and cap target must resolve
beneath it — absolute paths, `..`, and symlink escapes are config errors. Rationale:
a pointer this hook renders is an instruction the agent will obey, so a path outside
the workspace is an instruction to read outside it. Same pass: caps validation moved
into the shared contract (`validate_caps`, used by both scripts), because the checker
returning 0 on a typo'd cap path was a cap silently turning itself off — the checker
now fails nonzero on any malformed or missing configured target, and the hook surfaces
the same errors at session start.

## Inherited from the ancestor

**Pointer, not payload (2026-07-31).** The runtime truncates hook output at ~2–5 KB
and reports success; measured receipts in `selfhook.py`'s docstring. Limits moved to
commit time where they fail loudly in the owner's workflow.

**One payload with owned boundaries (2026-08-01).** Same-event hook outputs blend into
one context field with no delimiter; measured incident in the docstring. The banner —
now the per-section banner — makes each concern its own object.

**Both registrations emit `SessionStart` (2026-05-31).** The runtime's validator
silently drops `"PostCompact"`-named payloads. Intentional mismatch, documented where
it happens.
