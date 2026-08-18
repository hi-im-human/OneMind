from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

GENERATOR = Path(__file__).parents[1] / "generate_readme_tree.py"
BEGIN = "<!-- BEGIN GENERATED PACKAGE DIRECTORY -->"
END = "<!-- END GENERATED PACKAGE DIRECTORY -->"


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def fixture() -> Path:
    root = Path(tempfile.mkdtemp(prefix="onemind-readme-tree-"))
    write(root / "README.md", f"---\ndescription: root\n---\n# Root\n\n{BEGIN}\n{END}\n\nTail stays.\n")
    write(root / "CLAUDE-CODE" / "selfhook" / "!README.md", "---\ndescription: Hook multiplexer.\n---\nprivate body\n")
    write(root / "CLAUDE-CODE" / "selfhook" / "README.md", "---\ndescription: This standard README loses precedence.\n---\nprivate body\n")
    write(root / "CLAUDE-CODE" / "skills" / "agent-sync" / "README.md", "---\ndescription: Sync helper.\n---\nprivate body\n")
    write(root / "MIGRATION" / "sample" / "README.md", "# Missing description\n")
    write(root / "CLAUDE-CODE" / "selfhook" / "src" / "README.md", "---\ndescription: Must stay untracked.\n---\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "README.md", "CLAUDE-CODE/selfhook/!README.md", "CLAUDE-CODE/selfhook/README.md", "CLAUDE-CODE/skills/agent-sync/README.md", "MIGRATION/sample/README.md"], check=True)
    return root


def run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(GENERATOR), "--repo", str(root), *args], capture_output=True, text=True)


root = fixture()
before = (root / "README.md").read_bytes()
first = run(root, "--write", "--quiet")
after = (root / "README.md").read_text(encoding="utf-8")
checks = [
    ("write succeeds", first.returncode == 0),
    ("description renders", "[selfhook/](CLAUDE-CODE/selfhook/!README.md) — Hook multiplexer." in after),
    ("!README takes precedence", "This standard README loses precedence." not in after),
    ("nested skill renders", "[agent-sync/](CLAUDE-CODE/skills/agent-sync/README.md) — Sync helper." in after),
    ("missing description stays visible", "[sample/](MIGRATION/sample/README.md)" in after),
    ("untracked README absent", "Must stay untracked" not in after),
    ("tail preserved", after.endswith("Tail stays.\n")),
    ("marker survived", BEGIN in after and END in after),
]
second = run(root, "--write", "--quiet")
checks.append(("second run idempotent", second.returncode == 0 and "UP TO DATE" in second.stdout))

bad = root / "bad"
bad.mkdir()
write(bad / "README.md", "# no frontmatter\n" + BEGIN + "\n" + END + "\n")
subprocess.run(["git", "init", "-q", str(bad)], check=True)
subprocess.run(["git", "-C", str(bad), "add", "README.md"], check=True)
rejected = run(bad, "--write")
checks.append(("unmarked frontmatter boundary refuses", rejected.returncode == 1))

missing_markers = root / "missing-markers"
missing_markers.mkdir()
valid_without_markers = "---\ndescription: root\n---\n# Root\n\nHand-written text.\n"
write(missing_markers / "README.md", valid_without_markers)
subprocess.run(["git", "init", "-q", str(missing_markers)], check=True)
subprocess.run(["git", "-C", str(missing_markers), "add", "README.md"], check=True)
before_missing = (missing_markers / "README.md").read_bytes()
missing_result = run(missing_markers, "--write")
checks.append(("valid README without markers refuses", missing_result.returncode == 1))
checks.append(("missing-marker refusal preserves bytes", (missing_markers / "README.md").read_bytes() == before_missing))

duplicate_markers = root / "duplicate-markers"
duplicate_markers.mkdir()
valid_with_duplicates = f"---\ndescription: root\n---\n{BEGIN}\n{END}\n{BEGIN}\n{END}\n"
write(duplicate_markers / "README.md", valid_with_duplicates)
subprocess.run(["git", "init", "-q", str(duplicate_markers)], check=True)
subprocess.run(["git", "-C", str(duplicate_markers), "add", "README.md"], check=True)
before_duplicate = (duplicate_markers / "README.md").read_bytes()
duplicate_result = run(duplicate_markers, "--write")
checks.append(("duplicate markers refuse", duplicate_result.returncode == 1))
checks.append(("duplicate-marker refusal preserves bytes", (duplicate_markers / "README.md").read_bytes() == before_duplicate))

for label, eol in (("LF", b"\n"), ("CRLF", b"\r\n")):
    eol_root = fixture()
    readme = eol_root / "README.md"
    source = readme.read_text(encoding="utf-8").replace("\n", eol.decode("ascii"))
    readme.write_bytes(b"\xef\xbb\xbf" + source.encode("utf-8"))
    eol_result = run(eol_root, "--write", "--quiet")
    eol_after = readme.read_bytes()
    checks.append((f"{label} root generation succeeds", eol_result.returncode == 0))
    checks.append((f"{label} root BOM preserved", eol_after.startswith(b"\xef\xbb\xbf")))
    if eol == b"\r\n":
        checks.append(("CRLF root has no lone LF", eol_after.count(b"\n") == eol_after.count(b"\r\n")))
    else:
        checks.append(("LF root has no CRLF", b"\r\n" not in eol_after))

for label, passed in checks:
    print(f"{'PASS' if passed else 'FAIL'} {label}")
if not all(passed for _, passed in checks):
    raise SystemExit(1)
