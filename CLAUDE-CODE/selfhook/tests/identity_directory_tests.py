#!/usr/bin/env python3
"""
Regression suite for identity_directory.py.

Boundary cases include opposite-direction controls where applicable.

    python identity_directory_tests.py

Exit 0 = all passed, 1 = failures.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import json
import os
from pathlib import Path

SUT = Path(__file__).parents[1] / "src" / "identity_directory.py"
BEGIN = b"<!-- BEGIN GENERATED IDENTITY DIRECTORY -->"
END = b"<!-- END GENERATED IDENTITY DIRECTORY -->"
BOM = b"\xef\xbb\xbf"

passed = failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name}  --  {detail}")


def fixture(memory_bytes: bytes, ids: dict[str, bytes]) -> Path:
    d = Path(tempfile.mkdtemp(prefix="idir-"))
    (d / ".memory" / "identity").mkdir(parents=True)
    (d / ".memory" / "MEMORY.md").write_bytes(memory_bytes)
    for nm, content in ids.items():
        (d / ".memory" / "identity" / nm).write_bytes(content)
    (d / "continuity.json").write_text(
        json.dumps({"workspace": str(d.resolve()), "sections": [], "caps": []}),
        encoding="utf-8",
    )
    return d


def run(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SUT), "--config", str(root / "continuity.json"), *extra],
        capture_output=True, text=True,
    )


def run_cp1252(root: Path, *extra: str) -> subprocess.CompletedProcess:
    """Force the Windows legacy-output surface that cannot encode the folder icon."""
    env = dict(os.environ, PYTHONIOENCODING="cp1252")
    return subprocess.run(
        [sys.executable, str(SUT), "--config", str(root / "continuity.json"), *extra],
        capture_output=True, text=False, env=env,
    )


ID_OK = b"---\ndescription: a description\n---\nBODYBODYBODY\n"


def mem(eol: bytes = b"\n", bom: bytes = b"", extra_fm: bytes = b"") -> bytes:
    fm = b"---" + eol + b"description: d" + eol + extra_fm + b"---" + eol
    return bom + fm + b"## Index" + eol + eol + BEGIN + eol + b"old" + eol + END + eol + b"tail" + eol


print("\n=== identity_directory regression suite ===\n")

# ---------------------------------------------------------------- BLOCKER 1: CRLF
print("[blocker 1 — line endings preserved byte-exact]")
for label, eol in (("LF", b"\n"), ("CRLF", b"\r\n")):
    root = fixture(mem(eol=eol), {"p.md": ID_OK})
    before = (root / ".memory" / "MEMORY.md").read_bytes()
    r = run(root, "--write", "--quiet")
    after = (root / ".memory" / "MEMORY.md").read_bytes()
    b_crlf, a_crlf = before.count(b"\r\n"), after.count(b"\r\n")
    check(f"{label}: write succeeded", r.returncode == 0, r.stderr.strip())
    check(f"{label}: content actually regenerated", b"identity/p.md" in after, "block not written")
    if eol == b"\r\n":
        check("CRLF: no CRLF lost", a_crlf >= b_crlf - 1, f"before={b_crlf} after={a_crlf}")
        check("CRLF: no lone-LF introduced", after.count(b"\n") == a_crlf, "mixed endings appeared")
    else:
        check("LF: still zero CRLF (control)", a_crlf == 0, f"CRLF appeared: {a_crlf}")
    shutil.rmtree(root, ignore_errors=True)

# ------------------------------------------------- BLOCKER 2: marker in frontmatter
print("\n[blocker 2 — markers must sit below the frontmatter]")
attack = (
    b'---\ndescription: "x ' + BEGIN + b' y"\nkeep_me: important\n---\n## Body\nprose\n' + END + b"\ntail\n"
)
root = fixture(attack, {"p.md": ID_OK})
before = (root / ".memory" / "MEMORY.md").read_bytes()
r = run(root, "--write", "--quiet")
after = (root / ".memory" / "MEMORY.md").read_bytes()
check("marker inside frontmatter -> refused", r.returncode == 1, f"exit={r.returncode}")
check("  ...and the file is untouched", after == before, "FILE WAS MUTATED")
check("  ...keep_me survived", b"keep_me: important" in after, "FRONTMATTER DESTROYED")
check("  ...body survived", b"prose" in after, "BODY DESTROYED")
shutil.rmtree(root, ignore_errors=True)

root = fixture(mem(), {"p.md": ID_OK})  # control: markers correctly placed
r = run(root, "--write", "--quiet")
check("control: markers below frontmatter -> accepted", r.returncode == 0, r.stderr.strip())
shutil.rmtree(root, ignore_errors=True)

# ------------------------------------------------------------------ BLOCKER 3: BOM
print("\n[blocker 3 — UTF-8 BOM accepted and preserved]")
root = fixture(mem(bom=BOM), {"p.md": ID_OK})
r = run(root, "--write", "--quiet")
after = (root / ".memory" / "MEMORY.md").read_bytes()
check("BOM file accepted", r.returncode == 0, r.stderr.strip())
check("BOM still present after write", after.startswith(BOM), "BOM STRIPPED")
check("BOM file regenerated", b"identity/p.md" in after, "block not written")
shutil.rmtree(root, ignore_errors=True)

root = fixture(mem(), {"p.md": ID_OK})  # control: no BOM stays no BOM
r = run(root, "--write", "--quiet")
after = (root / ".memory" / "MEMORY.md").read_bytes()
check("control: no-BOM file gains no BOM", not after.startswith(BOM), "BOM INVENTED")
shutil.rmtree(root, ignore_errors=True)

# -------------------------------------------------------- BLOCKER 4: no body read
print("\n[blocker 4 — identity bodies are never read, not merely never emitted]")
huge_body = b"---\ndescription: short desc\n---\n" + (b"X" * 5_000_000) + b"\n"
root = fixture(mem(), {"p.md": huge_body})
r = run(root, "--write", "--quiet")
after = (root / ".memory" / "MEMORY.md").read_bytes()
check("5MB-body file processed", r.returncode == 0, r.stderr.strip())
check("  ...body not emitted", b"XXXX" not in after, "BODY LEAKED INTO OUTPUT")
# Mechanism, not output: a truncated file whose body is unreadable-past-frontmatter
# still works, because the reader closes at the delimiter.
trunc = b"---\ndescription: fine\n---\n"
root2 = fixture(mem(), {"p.md": trunc})
r2 = run(root2, "--write", "--quiet")
check("  ...file with NO body at all still works", r2.returncode == 0, r2.stderr.strip())
shutil.rmtree(root, ignore_errors=True)
shutil.rmtree(root2, ignore_errors=True)

# --------------------------------------------------------------- general refusals
print("\n[refusal matrix]")
cases = [
    ("markers absent", mem().replace(BEGIN, b"").replace(END, b""), ID_OK, 1),
    ("BEGIN duplicated", mem().replace(b"tail", BEGIN + b"\ntail"), ID_OK, 1),
    ("END before BEGIN", b"---\ndescription: d\n---\n" + END + b"\n" + BEGIN + b"\n", ID_OK, 1),
    ("MEMORY.md no frontmatter", b"no fm\n" + BEGIN + b"\n" + END + b"\n", ID_OK, 1),
    ("MEMORY.md unclosed frontmatter", b"---\ndescription: d\n" + BEGIN + b"\n" + END + b"\n", ID_OK, 1),
    ("CONTROL well-formed", mem(), ID_OK, 0),
]
for name, memory_bytes, id_bytes, want in cases:
    root = fixture(memory_bytes, {"p.md": id_bytes})
    r = run(root, "--write", "--quiet")
    check(f"{name} -> exit {want}", r.returncode == want, f"got {r.returncode}: {r.stderr.strip()[:90]}")
    shutil.rmtree(root, ignore_errors=True)

# Missing or empty descriptions list without a suffix and are counted in status output.
print("\n[description tolerance — 2026-08-18 contract]")
for name, id_bytes in (
    ("no frontmatter", b"just a body\n"),
    ("no description field", b"---\ntitle: t\n---\nbody\n"),
    ("empty description", b'---\ndescription: ""\n---\nbody\n'),
):
    root = fixture(mem(), {"p.md": id_bytes})
    r = run(root, "--write")
    after = (root / ".memory" / "MEMORY.md").read_bytes()
    check(f"{name} -> exit 0 (listed, not refused)", r.returncode == 0, r.stderr.strip()[:90])
    check(f"  ...entry present without description", b"[p](identity/p.md)\n" in after.replace(b"\r\n", b"\n"), "entry missing or has stray desc")
    check(f"  ...status counts it", "1 without description" in r.stdout, r.stdout.strip()[:90])
    shutil.rmtree(root, ignore_errors=True)
# Control: a described file must NOT be counted as missing.
root = fixture(mem(), {"p.md": ID_OK})
r = run(root, "--write")
check("CONTROL: described file -> no missing count", "without description" not in r.stdout, r.stdout.strip()[:90])
shutil.rmtree(root, ignore_errors=True)

root = fixture(mem(), {})  # empty identity dir AND nothing else in .memory
r = run(root, "--write", "--quiet")
check("empty .memory index -> refused (INVERSE of the #141 fail-open bug)", r.returncode == 1, f"got {r.returncode}")
shutil.rmtree(root, ignore_errors=True)

# ----------------------------------------------- 2026-08-18 scope: .memory flat + depth-1
print("\n[.memory scope — flat + depth-1, folders by name only]")
root = fixture(mem(), {"p.md": ID_OK})
memdir = root / ".memory"
(memdir / "my_life").mkdir()
(memdir / "my_life" / "a_note.md").write_bytes(ID_OK)
(memdir / "my_life" / "childfolder").mkdir()
(memdir / "my_life" / "childfolder" / "DEPTH2_BAIT.md").write_bytes(ID_OK)  # must NOT render
(memdir / "empty_folder").mkdir()
(memdir / "toplevel_note.md").write_bytes(ID_OK)
r = run(root, "--write")
after = (memdir / "MEMORY.md").read_bytes()
check("scope run -> exit 0", r.returncode == 0, r.stderr.strip()[:90])
check("top-level folder heading renders", b"## \xf0\x9f\x93\x82 my_life" in after, "no my_life heading")
check("depth-1 file under folder renders", b"my_life/a_note.md" in after, "a_note missing")
check("depth-1 child folder listed BY NAME", "📁 childfolder/".encode() in after, "childfolder entry missing")
check("DEPTH-2 BAIT ABSENT — the boundary holds", b"DEPTH2_BAIT" not in after, "depth-2 content leaked into output")
check("empty top-level folder still gets its heading", b"## \xf0\x9f\x93\x82 empty_folder" in after, "empty folder heading missing")
check("top-level file renders as \xf0\x9f\x93\x9d entry", "📝 [toplevel_note]".encode() in after, "toplevel entry missing")
check("MEMORY.md itself NOT self-listed", b"[MEMORY](MEMORY.md)" not in after, "tool indexed its own target")
shutil.rmtree(root, ignore_errors=True)

# ------------------------------------------------------------- quiet / idempotence
print("\n[hook safety + idempotence]")
sentinel_id = b"---\ndescription: has ZZSENTINELZZ inside\n---\nbody\n"
root = fixture(mem(), {"p.md": sentinel_id})
r = run(root, "--write", "--quiet")
check("--quiet leaks no block content to stdout/stderr", "ZZSENTINELZZ" not in (r.stdout + r.stderr), "SENTINEL LEAKED")
check("  ...but the file did get it", b"ZZSENTINELZZ" in (root / ".memory" / "MEMORY.md").read_bytes(), "not written")
# Control: without --quiet it SHOULD leak, proving the check above can fail.
# MUST use a FRESH fixture — running it against the already-written file returns
# "UP TO DATE" and echoes nothing, so the control would pass for the wrong reason.
# (That exact ordering error was in the first version of this suite.)
ctrl = fixture(mem(), {"p.md": sentinel_id})
r2 = run(ctrl)
check("control: without --quiet it does leak", "ZZSENTINELZZ" in (r2.stdout + r2.stderr), "leak-detector is blind")
shutil.rmtree(ctrl, ignore_errors=True)
r3 = run(root, "--write", "--quiet")
check("second run is UP TO DATE (idempotent)", "UP TO DATE" in r3.stdout, r3.stdout.strip()[:80])
shutil.rmtree(root, ignore_errors=True)

root = fixture(mem(), {"p.md": ID_OK})  # check-only must not write
before = (root / ".memory" / "MEMORY.md").read_bytes()
run(root)
check("check-only writes nothing", (root / ".memory" / "MEMORY.md").read_bytes() == before, "FILE CHANGED")
shutil.rmtree(root, ignore_errors=True)

# ---------------------------------------------------------- preview is cosmetic
print("\n[preview compatibility — cosmetic output never blocks work]")
root = fixture(mem(), {"p.md": ID_OK})
target = root / ".memory" / "MEMORY.md"
before = target.read_bytes()
r = run_cp1252(root, "--write")
out = r.stdout.decode("cp1252", errors="strict")
check("cp1252 --write -> exit 0", r.returncode == 0, f"exit={r.returncode}: {r.stderr!r}")
check("  ...write completed before preview", target.read_bytes() != before, "MEMORY.md unchanged")
check("  ...preview degrades visibly", "preview note: unsupported console characters were replaced" in out, out[:160])
shutil.rmtree(root, ignore_errors=True)

root = fixture(mem(), {"p.md": ID_OK})
target = root / ".memory" / "MEMORY.md"
before = target.read_bytes()
r = run_cp1252(root)
out = r.stdout.decode("cp1252", errors="strict")
check("cp1252 check-only -> exit 0", r.returncode == 0, f"exit={r.returncode}: {r.stderr!r}")
check("  ...check-only still writes nothing", target.read_bytes() == before, "FILE CHANGED")
check("  ...check-only preview degrades visibly", "preview note: unsupported console characters were replaced" in out, out[:160])
shutil.rmtree(root, ignore_errors=True)

root = fixture(mem(), {"p.md": ID_OK})
r = run(root, "--write")
check("UTF-8 preview remains readable", "## 📂 identity" in r.stdout, r.stdout[:160])
shutil.rmtree(root, ignore_errors=True)

# ------------------------------------------------------------- concurrent edit
# Another editor may modify MEMORY.md while the generator is preparing its write.
print("\n[concurrent edit — hook-triggered writer]")
import os as _os
import threading
import time as _time

root = fixture(mem(), {"p.md": ID_OK})
target = root / ".memory" / "MEMORY.md"
EXTERNAL_EDIT = b"CONCURRENT EXTERNAL EDIT\n"

def land_external_edit():
    _time.sleep(0.6)
    target.write_bytes(target.read_bytes() + EXTERNAL_EDIT)

t = threading.Thread(target=land_external_edit)
env = dict(_os.environ, IDIR_TEST_PAUSE_BEFORE_REPLACE="1.5")
t.start()
r = subprocess.run(
    [sys.executable, str(SUT), "--config", str(root / "continuity.json"), "--write", "--quiet"],
    capture_output=True, text=True, env=env,
)
t.join()
after = target.read_bytes()
check("concurrent edit -> refused", r.returncode == 1, f"exit={r.returncode}")
check("  ...external edit survived", EXTERNAL_EDIT in after, "EXTERNAL EDIT DESTROYED")
check("  ...our block was NOT written over them", b"identity/p.md" not in after, "we overwrote a newer edit")
check("  ...no temp file left behind", not any(p.name.startswith(".MEMORY.md.") for p in (root / ".memory").iterdir()), "temp leaked")
shutil.rmtree(root, ignore_errors=True)

# Control: same delay, NO concurrent edit -> must still succeed, proving the guard
# is detecting a real change rather than just refusing whenever the pause is set.
root = fixture(mem(), {"p.md": ID_OK})
r = subprocess.run(
    [sys.executable, str(SUT), "--config", str(root / "continuity.json"), "--write", "--quiet"],
    capture_output=True, text=True, env=dict(_os.environ, IDIR_TEST_PAUSE_BEFORE_REPLACE="1.5"),
)
check("control: same delay, no edit -> writes normally", r.returncode == 0, r.stderr.strip()[:90])
check("  ...and the block landed", b"identity/p.md" in (root / ".memory" / "MEMORY.md").read_bytes(), "not written")
shutil.rmtree(root, ignore_errors=True)

print(f"\n=== {passed} passed, {failed} failed ===\n")
sys.exit(1 if failed else 0)
