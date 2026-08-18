#!/usr/bin/env python3
"""Generate the marker-bounded OneMind package directory in the root README."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BOM = b"\xef\xbb\xbf"
BEGIN = b"<!-- BEGIN GENERATED PACKAGE DIRECTORY -->"
END = b"<!-- END GENERATED PACKAGE DIRECTORY -->"
DELIM = b"---"


def refuse(message: str) -> None:
    print(f"REFUSED — {message}", file=sys.stderr)
    raise SystemExit(1)


def detect_eol(raw: bytes) -> bytes:
    return b"\r\n" if raw.count(b"\r\n") > raw.count(b"\n") - raw.count(b"\r\n") else b"\n"


def frontmatter_end(body: bytes, label: str) -> int:
    if not body.startswith(DELIM):
        refuse(f"{label} does not open with a `---` frontmatter delimiter")
    first_newline = body.find(b"\n")
    if first_newline == -1 or body[:first_newline].strip() != DELIM:
        refuse(f"{label} has an invalid opening frontmatter delimiter")
    position = first_newline + 1
    while position < len(body):
        next_newline = body.find(b"\n", position)
        line = body[position:] if next_newline == -1 else body[position:next_newline]
        if line.strip() == DELIM:
            return len(body) if next_newline == -1 else next_newline + 1
        if next_newline == -1:
            break
        position = next_newline + 1
    refuse(f"{label} has no closing frontmatter delimiter")


def marker_span(body: bytes, marker: bytes, label: str) -> tuple[int, int]:
    hits: list[tuple[int, int]] = []
    start = 0
    while True:
        found = body.find(marker, start)
        if found == -1:
            break
        start = found + 1
        at_line_start = found == 0 or body[found - 1:found] == b"\n"
        rest = body[found + len(marker):]
        terminator = b"\r\n" if rest.startswith(b"\r\n") else b"\n" if rest.startswith(b"\n") else b""
        if at_line_start and (terminator or not rest):
            hits.append((found, found + len(marker) + len(terminator)))
    if len(hits) != 1:
        refuse(f"expected exactly one {label} marker on its own line, found {len(hits)}")
    return hits[0]


def description(path: Path) -> str | None:
    """Return only a README frontmatter description; never read its body."""
    with path.open("rb") as handle:
        first = handle.readline()
        if first.startswith(BOM):
            first = first[len(BOM):]
        if first.strip() != DELIM:
            return None
        lines: list[bytes] = []
        while True:
            line = handle.readline()
            if not line or line.strip() == DELIM:
                break
            lines.append(line)
    for line in b"".join(lines).decode("utf-8", errors="replace").splitlines():
        if line.startswith("description:"):
            desc = line[len("description:"):].strip().strip('"').strip("'").strip()
            return desc or None
    return None


def tracked_readmes(repo: Path) -> dict[Path, Path]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z", "--", "**/README.md", "**/!README.md"],
        capture_output=True,
        check=True,
    )
    selected: dict[Path, Path] = {}
    for encoded in result.stdout.split(b"\0"):
        if not encoded:
            continue
        relative = Path(encoded.decode("utf-8"))
        if relative.parent == Path("."):
            continue
        current = selected.get(relative.parent)
        if current is None or relative.name == "!README.md":
            selected[relative.parent] = relative
    return selected


def build_tree(repo: Path) -> tuple[bytes, int]:
    readmes = tracked_readmes(repo)
    if not readmes:
        refuse("no tracked package README files found")

    nodes: dict[Path, dict] = {Path("."): {}}
    metadata: dict[Path, tuple[Path, str | None]] = {}
    for directory, readme in readmes.items():
        metadata[directory] = (readme, description(repo / readme))
        cursor = nodes[Path(".")]
        for part in directory.parts:
            cursor = cursor.setdefault(part, {})

    lines: list[str] = []

    def walk(tree: dict, parent: Path, depth: int) -> None:
        for name in sorted(tree, key=str.lower):
            directory = parent / name
            readme, desc = metadata.get(directory, (None, None))
            indent = "  " * depth
            if readme is None:
                lines.append(f"{indent}- **{name}/**")
            else:
                suffix = f" — {desc}" if desc else ""
                lines.append(f"{indent}- [{name}/]({readme.as_posix()}){suffix}")
            walk(tree[name], directory, depth + 1)

    walk(nodes[Path(".")], Path("."), 0)
    return ("\n".join(lines) + "\n").encode("utf-8"), len(metadata)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    root_readme = repo / "README.md"
    if not repo.is_dir() or not (repo / ".git").exists() or not root_readme.is_file():
        print("ARGUMENT PROBLEM — --repo must be a Git worktree with a root README.md", file=sys.stderr)
        return 2

    raw = root_readme.read_bytes()
    bom, body = (raw[:len(BOM)], raw[len(BOM):]) if raw.startswith(BOM) else (b"", raw)
    frontmatter_end(body, "root README.md")
    begin_start, begin_end = marker_span(body, BEGIN, "BEGIN")
    end_start, _ = marker_span(body, END, "END")
    if begin_start < frontmatter_end(body, "root README.md") or end_start < begin_end:
        refuse("generated markers must appear after frontmatter with END after BEGIN")

    block, count = build_tree(repo)
    eol = detect_eol(raw)
    block = block.replace(b"\n", eol)
    updated = raw[:len(bom) + begin_end] + block + raw[len(bom) + end_start:]
    if updated == raw:
        print(f"UP TO DATE — {count} README-bearing directory/directories.")
        return 0
    if args.quiet:
        print(f"CHANGED — {count} README-bearing directory/directories.")
    else:
        print(block.decode("utf-8", errors="replace").rstrip())
    if not args.write:
        return 0

    descriptor, temporary = tempfile.mkstemp(dir=str(repo), prefix=".README.md.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(updated)
        if root_readme.read_bytes() != raw:
            os.unlink(temporary)
            refuse("root README.md changed while generation ran; nothing written")
        os.replace(temporary, root_readme)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    if root_readme.read_bytes() != updated:
        refuse("post-write bytes differ; inspect root README.md manually")
    frontmatter_end((updated[len(bom):] if bom else updated), "root README.md (post-write)")
    print("WRITTEN — exact bytes verified; frontmatter re-parsed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
