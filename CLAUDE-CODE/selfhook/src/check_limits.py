#!/usr/bin/env python
"""Enforce configured continuity-file caps before commit or synchronization.

Reads the same ``caps`` configuration as ``selfhook.py`` and exits nonzero for
oversized files or invalid configuration.

Usage (call from a pre-commit hook or sync script, before committing):
    python check_limits.py --config "<PACKAGE_ROOT>/config/continuity.json" [--workspace <path>]
Exit 0 = all files within limits. Exit 1 = something over — abort the commit,
trim, retry. Limits count logical characters (line endings normalized),
matching Python's read_text().
"""

import argparse
import sys
from pathlib import Path

from selfhook import load_config, validate  # the ONE shared contract, whole


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--workspace", default=None)
    args = ap.parse_args()

    try:
        cfg = load_config(Path(args.config))
    except Exception as e:
        print(f"  check_limits: cannot load config ({e}) — failing closed.")
        sys.exit(1)
    if not isinstance(cfg, dict):
        print("  check_limits: config root must be a JSON object — failing closed.")
        sys.exit(1)
    workspace = Path(args.workspace or cfg.get("workspace") or Path.cwd())

    # Validate the same root keys, workspace, sections, and caps as the hook.
    errors = validate(cfg, workspace)
    if errors:
        print("")
        for e in errors:
            print(f"  {e}")
        print("")
        sys.exit(1)

    over = []
    for entry in cfg.get("caps", []):
        path, limit = entry["path"], entry["limit"]
        f = workspace / path
        try:
            n = len(f.read_text(encoding="utf-8", errors="replace"))
        except OSError as e:
            print(f"  check_limits: cannot read capped file '{path}' ({e}) — failing closed.")
            sys.exit(1)
        if n > limit:
            over.append((path, n, limit))

    if over:
        print("")
        print("  CONTINUITY FILE OVER LIMIT — commit should abort.")
        for name, n, limit in over:
            print(f"    {name}: {n:,} chars vs {limit:,} limit  (+{n - limit:,})")
        print("")
        print("  Trim before committing. (Why limits exist: the session hook lists")
        print("  these files for reading at every session start — unbounded growth")
        print("  makes the ritual unaffordable. The cap is a drift alarm.)")
        print("")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
