#!/usr/bin/env python3
"""Regression suite for owner-declared external junction targets.

Uses a real Windows junction because the contract is specifically about the
resolved target of a workspace-relative path. It exercises the renderer,
checker, and directory generator so the three consumers retain one contract.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PACKAGE = Path(__file__).parents[1]
SRC = PACKAGE / "src"
HOOK = SRC / "selfhook.py"
CHECKER = SRC / "check_limits.py"
DIRECTORY = SRC / "identity_directory.py"

passed = failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS  {name}")
    else:
        failed += 1
        print(f"  FAIL  {name} -- {detail}")


def run(script: Path, config: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), "--config", str(config)],
        input="",
        capture_output=True,
        text=True,
    )


def make_junction(link: Path, target: Path) -> None:
    """Create the Windows reparse-point shape the contract explicitly supports."""
    env = dict(os.environ, SELFHOOK_TEST_LINK=str(link), SELFHOOK_TEST_TARGET=str(target))
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-Command",
            "New-Item -ItemType Junction -Path $env:SELFHOOK_TEST_LINK "
            "-Target $env:SELFHOOK_TEST_TARGET | Out-Null",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode:
        raise RuntimeError(f"could not create junction: {result.stderr.strip()}")


def setup() -> tuple[Path, Path, Path, Path]:
    root = Path(tempfile.mkdtemp(prefix="selfhook-trusted-root-"))
    workspace = root / "workspace"
    external = root / "external-identity"
    memory = workspace / ".memory"
    memory.mkdir(parents=True)
    external.mkdir()
    (external / "persona.md").write_text("# Persona\n", encoding="utf-8")
    (memory / "MEMORY.md").write_text(
        "---\ndescription: index\n---\n"
        "<!-- BEGIN GENERATED IDENTITY DIRECTORY -->\nold\n"
        "<!-- END GENERATED IDENTITY DIRECTORY -->\n",
        encoding="utf-8",
    )
    junction = memory / "identity"
    make_junction(junction, external)
    return root, workspace, external, junction


def write_config(path: Path, workspace: Path, roots: list[str] | None, *, directory: str = ".memory/identity") -> None:
    config = {
        "workspace": str(workspace),
        "sections": [{
            "slug": "identity",
            "header": "IDENTITY",
            "read_files": {"dir": directory, "patterns": ["persona.md"]},
        }],
        "caps": [{"path": ".memory/identity/persona.md", "limit": 1000}],
    }
    if roots is not None:
        config["trusted_roots"] = roots
    path.write_text(json.dumps(config), encoding="utf-8")


def remove_fixture(root: Path, junction: Path) -> None:
    # Remove the reparse point itself first; never recursively delete through it.
    if junction.exists() or junction.is_symlink():
        junction.rmdir()
    shutil.rmtree(root, ignore_errors=True)


if os.name != "nt":
    print("SKIP — trusted_roots junction suite requires Windows.")
    sys.exit(0)

print("\n=== trusted_roots junction regression suite ===\n")
root, workspace, external, junction = setup()
config = root / "continuity.json"
try:
    # The old/default contract: an undeclared junction target is rejected by both
    # primary consumers. This is the control against a silent default relaxation.
    write_config(config, workspace, None)
    hook = run(HOOK, config)
    checker = run(CHECKER, config)
    check("undeclared junction -> hook refuses", "SELFHOOK CONFIG ERROR" in hook.stdout, hook.stdout + hook.stderr)
    check("undeclared junction -> checker refuses", checker.returncode == 1, checker.stdout + checker.stderr)

    write_config(config, workspace, [])
    hook = run(HOOK, config)
    checker = run(CHECKER, config)
    check("empty trusted_roots -> hook still refuses", "SELFHOOK CONFIG ERROR" in hook.stdout, hook.stdout + hook.stderr)
    check("empty trusted_roots -> checker still refuses", checker.returncode == 1, checker.stdout + checker.stderr)

    # The exact target root enables all three contract consumers.
    write_config(config, workspace, [str(external)])
    hook = run(HOOK, config)
    checker = run(CHECKER, config)
    directory = run(DIRECTORY, config)
    check("declared external root -> hook renders", hook.returncode == 0 and "SELFHOOK CONFIG ERROR" not in hook.stdout, hook.stdout + hook.stderr)
    check("declared external root -> checker accepts", checker.returncode == 0, checker.stdout + checker.stderr)
    check("declared external root -> directory generator accepts", directory.returncode == 0, directory.stdout + directory.stderr)

    # A sibling root is not an authorization for the actual external target.
    sibling = root / "external-sibling"
    sibling.mkdir()
    write_config(config, workspace, [str(sibling)])
    hook = run(HOOK, config)
    checker = run(CHECKER, config)
    check("declared sibling -> hook still refuses", "SELFHOOK CONFIG ERROR" in hook.stdout, hook.stdout + hook.stderr)
    check("declared sibling -> checker still refuses", checker.returncode == 1, checker.stdout + checker.stderr)

    # trusted_roots never makes external config pointers or literal parent escapes legal.
    write_config(config, workspace, [str(external)], directory=str(external))
    hook = run(HOOK, config)
    check("absolute dir remains refused", "must be workspace-relative" in hook.stdout, hook.stdout + hook.stderr)

    write_config(config, workspace, [str(external)], directory="..")
    hook = run(HOOK, config)
    check("literal parent escape remains refused", "escapes the workspace" in hook.stdout, hook.stdout + hook.stderr)
finally:
    remove_fixture(root, junction)

print(f"\n=== {passed} passed, {failed} failed ===\n")
sys.exit(1 if failed else 0)
