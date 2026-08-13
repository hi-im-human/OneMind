"""
selfhook.py — SessionStart + PostCompact continuity hook (event multiplexer).

Emits ONE ordered payload of named sections — instructions and file POINTERS
only, never file contents. Other packages integrate by adding a section to the
config, not by registering more hooks or editing this code.

WHY POINTER, NOT PAYLOAD (measured, 2026-07-31, on this package's ancestor):
the runtime truncates oversized hook output, spills the remainder to a
persisted file, and reports success. Measured from session records:
    57.1 KB emitted -> 2,432 chars received (first file only, mid-sentence)
    32.2 KB emitted -> 2,980 chars received
    30.2 KB emitted -> ~2,000 chars received
Agents ran for days on one truncated file and nothing else, while the hook
reported success every time. The script was never the problem; the transport
ate it. A short instruction kept below the observed floor is far less likely
to be truncated (the floor is observed, not contractual), and the agent reads
the real files itself. File-size caps are enforced separately at commit time
(check_limits.py) so oversized files fail loudly in the owner's own workflow.

⚠️ THE PAYLOAD BUDGET (1,800 chars) SITS BELOW THE WORST MEASURED FLOOR
(~2,000 received). The truncation marker is reserved INSIDE the budget — a
marker appended beyond the guarantee could itself be truncated away, which
would be a warning that deletes itself exactly when needed.

⚠️ VERIFY ANY FUTURE CHANGE BY READING WHAT THE SESSION ACTUALLY RECEIVED —
not by running this script. Payload is not receipt.

WHY ONE MULTIPLEXER (measured, 2026-08-01, same ancestor): multiple hooks on
one event write into ONE additionalContext field, concatenated with NO
delimiter. An agent received another hook's directive running straight into
this instruction mid-line, obeyed the loud opening directives, and never read
its continuity files. Delivery worked; the read didn't happen. One hook owner,
one ordered payload, a banner per section — boundaries the runtime doesn't
provide, drawn on purpose.

FAILURE POLICY: any config problem — unreadable/malformed JSON, bad section
shape, duplicate slugs, unedited <WORKSPACE> placeholder, configured files
that don't exist — produces an ERROR-ONLY payload of [SELFHOOK CONFIG ERROR]
lines. Selfhook never executes a partial configuration while telling the
agent everything is fine; silent partial delivery is the failure class this
package exists to prevent.

Usage in settings.json (register under BOTH SessionStart and PostCompact;
absolute paths; on Windows double the backslashes). Pass the real event name —
sections can subscribe to specific events:

    "SessionStart": [... "command": "python \"<PACKAGE_ROOT>/src/selfhook.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --event SessionStart" ...]
    "PostCompact":  [... "command": "python \"<PACKAGE_ROOT>/src/selfhook.py\" --config \"<PACKAGE_ROOT>/config/continuity.json\" --event PostCompact" ...]
"""

import argparse
import json
import sys
from pathlib import Path

VALID_EVENTS = {"SessionStart", "PostCompact"}
# Strict key contract: a misspelled key ('event', 'read_file', 'section', 'cap')
# would otherwise produce a healthy-looking partial configuration — the exact
# failure class this package exists to prevent. '_comment' allowed everywhere.
ALLOWED_ROOT_KEYS = {"_comment", "workspace", "sections", "caps"}
ALLOWED_SECTION_KEYS = {"_comment", "slug", "header", "events", "text", "read_files"}
ALLOWED_READ_FILES_KEYS = {"_comment", "dir", "patterns"}
ALLOWED_CAP_KEYS = {"_comment", "path", "limit"}
# Below the worst measured transport floor (~2,000 chars received); see docstring.
PAYLOAD_BUDGET = 1800
CUT_MARKER = ("\n\n[SELFHOOK: payload exceeded its budget and was cut HERE — "
              "shorten section text; move content into the files sections point at.]")


def emit(notice: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            # The runtime's schema (as of last verification) accepts only
            # "SessionStart" here — "PostCompact" payloads are dropped silently.
            # Both registrations emit SessionStart-shaped output on purpose.
            "hookEventName": "SessionStart",
            "additionalContext": notice,
        }
    }))


def emit_errors(errors: list) -> None:
    """Error-only payload, bounded, never mixed with partial rendering."""
    body = "\n".join(errors[:12])
    notice = ("\n\n=============================================\n"
              "  SELFHOOK CONFIG ERROR — HOOK DID NOT RENDER\n"
              "=============================================\n\n"
              f"{body}\n\n"
              "Fix config/continuity.json; no continuity sections were shown this session.")
    if len(notice) > PAYLOAD_BUDGET:
        notice = notice[:PAYLOAD_BUDGET - len(CUT_MARKER)] + CUT_MARKER
    emit(notice)


def load_config(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def contained(workspace: Path, target: Path) -> bool:
    """True iff target — fully resolved, symlinks included — is under workspace."""
    try:
        target.resolve().relative_to(workspace.resolve())
        return True
    except (ValueError, OSError):
        return False


def check_rel_dir(errors: list, owner: str, workspace: Path, d):
    """Type-check + contain a config-supplied directory. Returns base or None.

    Every pointer this hook renders is an instruction the agent will obey —
    a path that escapes the workspace is an instruction to read outside it.
    Rejected: non-string, absolute, `..`, and symlink escapes (via resolve())."""
    E = "[SELFHOOK CONFIG ERROR]"
    if not isinstance(d, str):
        errors.append(f"{E} {owner}: 'dir' must be a string, got {type(d).__name__}")
        return None
    if Path(d).is_absolute():
        errors.append(f"{E} {owner}: 'dir' must be workspace-relative, not absolute")
        return None
    base = workspace / d
    if not contained(workspace, base):
        errors.append(f"{E} {owner}: 'dir' {d!r} escapes the workspace — rejected")
        return None
    return base


def validate_workspace(workspace: Path) -> list:
    """The workspace contract, shared by the hook and check_limits.py: an
    absolute path to an existing directory, placeholder edited. One contract —
    the checker must not accept a workspace the hook rejects."""
    E = "[SELFHOOK CONFIG ERROR]"
    if "<WORKSPACE>" in str(workspace) or not workspace.is_dir():
        return [f"{E} workspace {str(workspace)!r} is not an existing directory — "
                "edit 'workspace' in the config (the example ships a placeholder)"]
    if not workspace.is_absolute():
        return [f"{E} workspace must be an absolute path — a relative "
                "workspace makes containment depend on where the hook runs"]
    return []


def validate_root(cfg) -> list:
    """Strict root contract, shared by hook and checker: known keys only,
    'sections' and 'caps' explicitly present (use [] for none). A misspelled
    root key must fail loudly, not silently disable what it misspells."""
    E = "[SELFHOOK CONFIG ERROR]"
    if not isinstance(cfg, dict):
        return [f"{E} config root must be a JSON object"]
    errors = []
    unknown = sorted(set(cfg) - ALLOWED_ROOT_KEYS)
    if unknown:
        errors.append(f"{E} unknown root key(s) {unknown} — allowed: "
                      f"{sorted(ALLOWED_ROOT_KEYS)}")
    for req in ("sections", "caps"):
        if req not in cfg:
            errors.append(f"{E} missing required '{req}' list (use [] for none)")
    return errors


def validate(cfg, workspace: Path) -> list:
    """Validate the WHOLE contract — types before operations, containment
    before rendering. Returns error strings; empty = valid."""
    E = "[SELFHOOK CONFIG ERROR]"
    errors = validate_root(cfg)
    if errors:
        return errors  # key-level trust is gone; deeper checks would mislead
    errors = validate_workspace(workspace)
    if errors:
        return errors  # nothing below is meaningful against a bad root
    sections = cfg.get("sections", [])
    if not isinstance(sections, list):
        return errors + [f"{E} 'sections' must be a list"]
    seen = set()
    for i, s in enumerate(sections):
        if not isinstance(s, dict) or not isinstance(s.get("slug"), str) or not isinstance(s.get("header"), str):
            errors.append(f"{E} section #{i} malformed: needs string 'slug' and 'header'")
            continue
        # A blank banner defeats the named-boundary invariant; surrounding
        # whitespace would let ' id ' and 'id' coexist as "different" sections.
        if (not s["slug"].strip() or s["slug"] != s["slug"].strip()
                or not s["header"].strip() or s["header"] != s["header"].strip()):
            errors.append(f"{E} section #{i}: 'slug' and 'header' must be non-empty "
                          "with no surrounding whitespace")
            continue
        if s["slug"] in seen:
            errors.append(f"{E} duplicate section slug '{s['slug']}'")
        seen.add(s["slug"])
        owner = f"section '{s['slug']}'"
        unknown = sorted(set(s) - ALLOWED_SECTION_KEYS)
        if unknown:
            errors.append(f"{E} {owner}: unknown key(s) {unknown} — allowed: "
                          f"{sorted(ALLOWED_SECTION_KEYS)}")
        if "text" in s and not isinstance(s["text"], str):
            errors.append(f"{E} {owner}: 'text' must be a string")
        ev = s.get("events", [])
        if not isinstance(ev, list) or any(not isinstance(e, str) for e in ev):
            errors.append(f"{E} {owner}: 'events' must be a list of strings")
        elif set(ev) - VALID_EVENTS:
            errors.append(f"{E} {owner}: 'events' must be from {sorted(VALID_EVENTS)}")
        rf = s.get("read_files")
        if rf is None:
            continue
        if not isinstance(rf, dict) or not isinstance(rf.get("patterns"), list):
            errors.append(f"{E} {owner}: 'read_files' needs a 'patterns' list")
            continue
        unknown = sorted(set(rf) - ALLOWED_READ_FILES_KEYS)
        if unknown:
            errors.append(f"{E} {owner}: unknown read_files key(s) {unknown} — "
                          f"allowed: {sorted(ALLOWED_READ_FILES_KEYS)}")
            continue
        base = check_rel_dir(errors, owner, workspace, rf.get("dir", ""))
        if base is None:
            continue
        for pattern in rf["patterns"]:
            if not isinstance(pattern, str):
                errors.append(f"{E} {owner}: pattern {pattern!r} is not a string")
                continue
            if Path(pattern).is_absolute():
                errors.append(f"{E} {owner}: pattern {pattern!r} must be relative")
                continue
            if "*" in pattern:
                matches = sorted(base.glob(pattern))
                if not matches:
                    errors.append(f"{E} {owner}: glob '{pattern}' matches nothing under {base}")
                for m in matches:
                    if not contained(workspace, m):
                        errors.append(f"{E} {owner}: '{m.name}' resolves outside "
                                      "the workspace — rejected")
                    elif not m.is_file():
                        errors.append(f"{E} {owner}: glob '{pattern}' matched "
                                      f"'{m.name}', which is not a regular file — "
                                      "a directory cannot be a pointer target")
            else:
                f = base / pattern
                if not f.exists():
                    errors.append(f"{E} {owner}: configured file '{pattern}' not found under {base}")
                elif not contained(workspace, f):
                    errors.append(f"{E} {owner}: '{pattern}' resolves outside "
                                  "the workspace — rejected")
                elif not f.is_file():
                    errors.append(f"{E} {owner}: '{pattern}' is not a regular file — "
                                  "a directory cannot be a pointer target")
    errors.extend(validate_caps(cfg, workspace))
    return errors


def validate_caps(cfg, workspace: Path) -> list:
    """Caps validation — shared by the hook and check_limits.py, one contract.

    A missing or malformed cap target FAILS: a typo'd path would otherwise
    turn the cap off silently, and everyone would keep believing in it."""
    E = "[SELFHOOK CAPS ERROR]"
    errors = []
    if not isinstance(cfg, dict) or "caps" not in cfg:
        return [f"{E} missing required 'caps' list (use [] for none) — a misspelled "
                "'caps' key must not silently disable every cap"]
    caps = cfg["caps"]
    if not isinstance(caps, list):
        return [f"{E} 'caps' must be a list"]
    for i, entry in enumerate(caps):
        if (not isinstance(entry, dict) or not isinstance(entry.get("path"), str)
                or not isinstance(entry.get("limit"), int)
                or isinstance(entry.get("limit"), bool) or entry["limit"] <= 0):
            errors.append(f"{E} caps entry #{i} malformed: needs string 'path' + positive int 'limit'")
            continue
        unknown = sorted(set(entry) - ALLOWED_CAP_KEYS)
        if unknown:
            errors.append(f"{E} caps entry '{entry['path']}': unknown key(s) {unknown} "
                          f"— allowed: {sorted(ALLOWED_CAP_KEYS)}")
            continue
        if Path(entry["path"]).is_absolute():
            errors.append(f"{E} caps entry '{entry['path']}': path must be workspace-relative")
            continue
        f = workspace / entry["path"]
        if not f.exists():
            errors.append(f"{E} caps entry '{entry['path']}': file not found — "
                          "a typo must not disable a cap silently")
        elif not contained(workspace, f):
            errors.append(f"{E} caps entry '{entry['path']}': resolves outside "
                          "the workspace — rejected")
        elif not f.is_file():
            errors.append(f"{E} caps entry '{entry['path']}': not a regular file — "
                          "only files can be capped")
    return errors


def render_section(workspace: Path, section: dict) -> str:
    bar = "=" * 45
    parts = [f"{bar}\n  {section['header']}\n{bar}"]
    if section.get("text"):
        parts.append(section["text"])
    rf = section.get("read_files")
    if rf:
        base = workspace / rf.get("dir", "")
        paths = []
        for pattern in rf.get("patterns", []):
            if "*" in pattern:
                paths.extend(sorted(base.glob(pattern)))  # ALL matches, deliberately
            else:
                paths.append(base / pattern)  # existence already validated
        if paths:
            parts.append("\n".join(f"- {p}" for p in paths))
    return "\n\n".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--event", default="SessionStart", choices=sorted(VALID_EVENTS))
    parser.add_argument("--workspace", default=None)
    args, _ = parser.parse_known_args()

    # Hook payload arrives on stdin; nothing in it changes the instruction.
    try:
        sys.stdin.read()
    except Exception:
        pass

    try:
        cfg = load_config(Path(args.config))
    except FileNotFoundError:
        emit_errors([f"[SELFHOOK CONFIG ERROR] config not found: {args.config}"])
        return
    except json.JSONDecodeError as e:
        emit_errors([f"[SELFHOOK CONFIG ERROR] config is not valid JSON: {e}"])
        return
    except OSError as e:
        emit_errors([f"[SELFHOOK CONFIG ERROR] cannot read config: {e}"])
        return

    workspace = Path(args.workspace or (cfg.get("workspace") if isinstance(cfg, dict) else "") or Path.cwd())

    errors = validate(cfg, workspace)
    if errors:
        emit_errors(errors)   # error-only: never render a partial configuration
        return

    active = [s for s in cfg.get("sections", [])
              if not s.get("events") or args.event in s["events"]]
    rendered = [r for r in (render_section(workspace, s) for s in active) if r.strip()]
    if not rendered:
        sys.exit(0)  # nothing subscribed to this event — not an error

    notice = "\n\n" + "\n\n".join(rendered)
    if len(notice) > PAYLOAD_BUDGET:
        # Marker reserved INSIDE the budget — a marker past the transport floor
        # could itself be truncated away.
        notice = notice[:PAYLOAD_BUDGET - len(CUT_MARKER)] + CUT_MARKER
    emit(notice)


if __name__ == "__main__":
    main()
