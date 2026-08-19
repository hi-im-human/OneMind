#!/usr/bin/env python3
"""Regenerate a shallow .memory directory inside MEMORY.md.

The tool replaces only the bytes between its marker pair. It lists top-level
.memory files and folders plus each top-level folder's direct children; it never
descends farther. Markdown descriptions come from frontmatter when available.

Contract:
  - MEMORY.md is handled as RAW BYTES end to end. Everything before the BEGIN marker
    line and from the END marker line onward is copied byte-for-byte, untouched.
  - BOM preserved. Line endings detected from the file and preserved.
  - Both markers must sit on their own lines, AFTER the closing frontmatter delimiter.
  - Frontmatter is re-parsed after writing; a write that damaged it is rolled back.
  - Markdown files are streamed and CLOSED at the closing frontmatter delimiter. The
    body is never read into memory at all.

The component reads Selfhook's validated workspace configuration and derives the
only target path as <workspace>/.memory. It does not define a second file list.

Exit codes:  0 = clean / would-be-clean · 1 = refused · 2 = usage
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from selfhook import load_config, validate

BOM = b"\xef\xbb\xbf"
CRLF = b"\r\n"
LF = b"\n"
BEGIN = b"<!-- BEGIN GENERATED IDENTITY DIRECTORY -->"
END = b"<!-- END GENERATED IDENTITY DIRECTORY -->"
DELIM = b"---"


def refuse(msg: str):
    print(f"REFUSED — {msg}", file=sys.stderr)
    sys.exit(1)


# --------------------------------------------------------------------------- bytes


def detect_eol(raw: bytes) -> bytes:
    """Dominant line ending in the ORIGINAL file. Generated lines match it."""
    crlf = raw.count(b"\r\n")
    lf = raw.count(b"\n") - crlf
    return b"\r\n" if crlf > lf else b"\n"


def frontmatter_end(body: bytes, label: str) -> int:
    """
    Byte offset just past the closing frontmatter delimiter line.
    Operates on bytes; decodes nothing.
    """
    if not body.startswith(DELIM):
        refuse(f"{label} does not open with a `---` frontmatter delimiter")
    nl = body.find(b"\n")
    if nl == -1:
        refuse(f"{label} has an opening delimiter but no newline after it")
    if body[:nl].strip() != DELIM:
        refuse(f"{label} first line is not exactly `---`")

    pos = nl + 1
    while pos < len(body):
        nxt = body.find(b"\n", pos)
        line = body[pos:] if nxt == -1 else body[pos:nxt]
        if line.strip() == DELIM:
            return len(body) if nxt == -1 else nxt + 1
        if nxt == -1:
            break
        pos = nxt + 1
    refuse(f"{label} has no closing `---` frontmatter delimiter")


def marker_span(body: bytes, marker: bytes, name: str) -> tuple[int, int]:
    """
    Locate a marker that occupies its OWN LINE. Returns (line_start, line_end_exclusive
    including its terminator). Refuses on 0 or >1 qualifying occurrences.
    """
    hits = []
    start = 0
    while True:
        i = body.find(marker, start)
        if i == -1:
            break
        start = i + 1
        at_line_start = i == 0 or body[i - 1 : i] == b"\n"
        rest = body[i + len(marker) :]
        stripped = rest[:2] if rest[:2] == b"\r\n" else rest[:1]
        on_own_line = at_line_start and (stripped in (b"\r\n", b"\n") or rest == b"")
        if on_own_line:
            end = i + len(marker) + len(stripped)
            hits.append((i, end))
    if len(hits) != 1:
        refuse(
            f"expected exactly 1 {name} marker on its own line, found {len(hits)}"
            " (markers embedded inside other text do not count, deliberately)"
        )
    return hits[0]


# -------------------------------------------------------------------- memory files


def description_of(path: Path) -> str | None:
    """
    Filename + description only. Streams the file and STOPS at the closing frontmatter
    delimiter — the body is never read. This is the contract, in code.

    A file without parseable frontmatter or without a `description:` returns None and
    is listed without a description instead of refusing. Missing-description counts are
    reported in status output.
    """
    fm_lines: list[bytes] = []
    with path.open("rb") as fh:
        first = fh.readline()
        if first.startswith(BOM):
            first = first[len(BOM) :]
        if first.strip() != DELIM:
            return None
        while True:
            line = fh.readline()
            if not line:
                return None
            if line.strip() == DELIM:
                break  # file closes here; body never read
            fm_lines.append(line)

    text = b"".join(fm_lines).decode("utf-8", errors="replace")
    for ln in text.splitlines():
        if ln.startswith("description:"):
            desc = ln[len("description:") :].strip().strip('"').strip("'").strip()
            return desc or None
    return None


def _file_line(f: Path, rel: str) -> tuple[str, bool]:
    """One rendered entry. Returns (line, has_description)."""
    desc = description_of(f)
    if desc:
        return f"- [{f.stem}]({rel}) — {desc}", True
    return f"- [{f.stem}]({rel})", False


def print_preview(text: str) -> None:
    """Print a human preview without letting a legacy console abort the operation.

    The generated directory can contain Unicode (including its folder/file icons).
    A Windows cp1252 console cannot encode every such character. The preview is
    display-only: degrade unencodable characters to ``?`` and say so rather than
    making the requested write or check fail.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        fallback = text.encode(encoding, errors="replace").decode(encoding)
        print(fallback)
        print("[preview note: unsupported console characters were replaced]")


def build_block(mem: Path, link_prefix: str, eol: bytes) -> tuple[bytes, int, int]:
    """
    `.memory/` with only flat folders/files and depth-1 children. Per top-level folder:
    its depth-1 .md files AND its depth-1 child
    folders (child folders BY NAME ONLY — never descended into). Top-level .md files
    (except MEMORY.md itself) list after the folders, matching the current layout.
    NOTHING past depth 1 is ever read or rendered.

    Returns (block_bytes, entry_count, missing_description_count).
    """
    lines: list[str] = []
    entries = 0
    missing = 0

    top_dirs = sorted(
        (d for d in mem.iterdir() if d.is_dir() and not d.name.startswith(".")),
        key=lambda p: p.name.lower(),
    )
    top_files = sorted(
        (f for f in mem.glob("*.md") if f.name != "MEMORY.md"),
        key=lambda p: p.name.lower(),
    )

    for d in top_dirs:
        lines.append(f"## 📂 {d.name}")
        child_files = sorted(d.glob("*.md"), key=lambda p: p.name.lower())
        child_dirs = sorted(
            (c for c in d.iterdir() if c.is_dir() and not c.name.startswith(".")),
            key=lambda p: p.name.lower(),
        )
        for f in child_files:
            ln, has = _file_line(f, f"{link_prefix}{d.name}/{f.name}")
            lines.append(ln)
            entries += 1
            missing += 0 if has else 1
        for c in child_dirs:
            # By name only — deliberately no listing of contents (depth-1 boundary).
            lines.append(f"- 📁 {c.name}/")
            entries += 1
        lines.append("")

    for f in top_files:
        ln, has = _file_line(f, f"{link_prefix}{f.name}")
        lines.append("📝 " + ln[2:])  # top-level files render as 📝 entries, not list items
        entries += 1
        missing += 0 if has else 1

    if entries == 0:
        refuse(f"nothing to index under {mem} — refusing to write an empty directory")

    while lines and lines[-1] == "":
        lines.pop()
    return b"".join(ln.encode("utf-8") + eol for ln in lines), entries, missing


# ------------------------------------------------------------------------- main


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True, help="Selfhook continuity.json path.")
    ap.add_argument("--write", action="store_true", help="apply. Default is check-only.")
    ap.add_argument("--link-prefix", default="", help="prepended to every generated path; empty when MEMORY.md sits inside .memory/")
    ap.add_argument(
        "--quiet",
        action="store_true",
        help=(
            "Status counts only, never block contents. For hook use, stdout "
            "can become session context, so it emits counts rather than generated content."
        ),
    )
    args = ap.parse_args()

    try:
        cfg = load_config(Path(args.config))
    except Exception as exc:
        print(f"CONFIG PROBLEM — cannot load {args.config}: {exc}", file=sys.stderr)
        return 2
    if not isinstance(cfg, dict):
        print("CONFIG PROBLEM — Selfhook config root must be a JSON object", file=sys.stderr)
        return 2
    workspace = Path(cfg.get("workspace") or Path.cwd())
    errors = validate(cfg, workspace)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    mem = workspace / ".memory"
    if not mem.is_dir():
        print(f"CONFIG PROBLEM — .memory directory not found under workspace: {mem}", file=sys.stderr)
        return 2

    memory_md = mem / "MEMORY.md"
    if not memory_md.is_file():
        refuse(f"MEMORY.md not found at {memory_md}")

    raw = memory_md.read_bytes()
    bom, body = (raw[: len(BOM)], raw[len(BOM) :]) if raw.startswith(BOM) else (b"", raw)

    fm_end = frontmatter_end(body, "MEMORY.md")
    b_start, b_end = marker_span(body, BEGIN, "BEGIN")
    e_start, e_end = marker_span(body, END, "END")

    if b_start < fm_end:
        refuse("BEGIN marker is inside the frontmatter block — it must appear after the closing `---`")
    if e_start < fm_end:
        refuse("END marker is inside the frontmatter block — it must appear after the closing `---`")
    if e_start < b_end:
        refuse("END marker appears before BEGIN marker")

    eol = detect_eol(raw)
    prefix, suffix = raw[: len(bom) + b_end], raw[len(bom) + e_start :]
    new_block, n, missing = build_block(mem, args.link_prefix, eol)
    updated = prefix + new_block + suffix

    miss_note = f", {missing} without description" if missing else ""
    if updated == raw:
        print(f"UP TO DATE — {n} entr(ies){miss_note}.")
        return 0

    def report_changed() -> None:
        if args.quiet:
            print(f"CHANGED — {n} entr(ies){miss_note}, {len(new_block.splitlines())} line(s)")
            return
        eol_name = "CRLF" if eol == CRLF else "LF"
        bom_name = "yes" if bom else "no"
        print(f"CHANGED — {n} entr(ies){miss_note}  [eol={eol_name}, bom={bom_name}]")
        print("--- generated block ---")
        print_preview(new_block.decode("utf-8", errors="replace").rstrip())

    if not args.write:
        report_changed()
        if not args.quiet:
            print("\nCheck-only. Nothing written.")
        return 0

    fd, tmp = tempfile.mkstemp(dir=str(mem), prefix=".MEMORY.md.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(updated)

        # Test-only delay, widening the read->replace window so the concurrent-edit
        # guard below can be exercised deterministically. Inserts a sleep and does
        # nothing else; unset in every real run.
        pause = os.environ.get("IDIR_TEST_PAUSE_BEFORE_REPLACE")
        if pause:
            import time

            time.sleep(float(pause))

        # CONCURRENT-EDIT GUARD. Another editor may modify MEMORY.md while this runs. If it has
        # changed since we snapshotted it, their bytes are newer than ours. Refuse.
        if memory_md.read_bytes() != raw:
            os.unlink(tmp)
            refuse(
                "MEMORY.md changed on disk while this ran — someone else's edit is newer than "
                "the snapshot this write was built from. Nothing written; their version is intact. "
                "Re-run when the file is idle."
            )

        os.replace(tmp, memory_md)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise

    # Postcondition: EXACT bytes, not merely the right shape.
    after = memory_md.read_bytes()
    if after != updated:
        # Deliberately NOT restoring the snapshot. The difference may be a newer edit
        # that landed after our replace, and overwriting it with our older copy would
        # make this "safety" step the thing that destroys their work. Refuse loudly
        # and leave the file for a person to look at.
        refuse(
            "post-write bytes differ from what was written. NOT restoring the old snapshot — "
            "the difference may be a newer edit by someone else, and restoring would destroy it. "
            f"Inspect {memory_md} by hand."
        )

    a_body = after[len(bom) :] if after.startswith(BOM) else after
    frontmatter_end(a_body, "MEMORY.md (post-write)")  # refuses if damaged

    # The requested write and its postconditions are complete before any optional
    # human preview. A display-only encoding issue must never block this operation.
    report_changed()
    print("\nWRITTEN — exact bytes verified; frontmatter re-parsed; no concurrent edit lost.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
