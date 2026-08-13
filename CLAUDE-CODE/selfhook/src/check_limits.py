#!/usr/bin/env python
"""
check_limits.py — continuity-file cap enforcement at commit time.

The design premise (2026-07-31, this package's ancestor): size limits belong
in the OWNER'S WORKFLOW, not in the hook transport. The transport silently
truncates oversized output and reports success; a pre-commit/pre-sync check
fails LOUD, in front of the person who can fix it, before the oversized file
becomes the only copy anyone syncs.

Reads the same config as selfhook.py ('caps' list) — one source of truth,
both consumers, no parsing of code by code.

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

    # The FULL shared contract (selfhook.validate): root keys, workspace,
    # sections, and caps. The checker must reject exactly what the hook
    # rejects — a config the hook refuses to render must not pass commit,
    # and a cap that silently stops applying is worse than no cap, because
    # everyone still believes in it.
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
