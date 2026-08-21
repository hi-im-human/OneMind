"""
Discord plugin bot-to-bot filter patch — PORTABLE idempotent applicator (v2).

Problem:
  The Claude Code Discord plugin's server.ts drops EVERY message from a bot
  account at the top of the inbound handler:

      client.on('messageCreate', msg => {
        if (msg.author.bot) return
        handleInbound(msg)...

  This is the plugin's anti-echo / bot-input default, and it means a multi-bot
  installation cannot route bot-authored messages through the plugin.
  No config, env var, or access.json key reaches it.

What this does:
  Replaces that unconditional drop with an allowlist-aware one. Bots are STILL
  dropped by default. A bot message passes to handleInbound (where the plugin's
  normal gate()/access policy then runs as usual) only if:
    - it is NOT this bot's own message (unconditional self-drop — prevents an
      echo loop even if the bot's own ID is accidentally allowlisted), AND
    - the sender's user ID is in access.json `allowFrom` at top level, OR in
      the `allowFrom` of the group for the CURRENT channel (or, if the message
      is in a thread, that thread's parent channel). Group authorization does
      NOT inherit across groups: listing a bot in one room does not admit it to
      another.

States this script recognizes (exact-block matching, exactly one occurrence, AND
exactly one messageCreate handler registration in the whole file):
  stock      -> patched to v2                          ("patched")
  v1 block   -> upgraded to v2                         ("upgraded")
  v2 block   -> no-op                                  ("already")
  anything else (mixed, duplicated, reshaped upstream) -> REFUSED, untouched
             ("skipped (unfamiliar)"), and the script exits NONZERO so a
             SessionStart hook fails visibly instead of silently doing nothing.

Exit codes:  0 = every file is patched/upgraded/already (or nothing found)
             2 = at least one file skipped (unfamiliar) -> inspect it
             3 = usage error (unknown --option); nothing scanned, nothing written
             1 = read/write error

Usage:
  python patch_discord_bot_filter.py            # patch everything found
  python patch_discord_bot_filter.py --dry-run  # preview only, writes nothing
  python patch_discord_bot_filter.py /extra/root /another/root
  python patch_discord_bot_filter.py --no-home-scan /only/this/root   # skip ~/.claude*; scope to given roots
                                                                      # (use this for tests/controlled runs)

Scans every `~/.claude*` directory (any agent naming scheme) and every plugin
version under plugins/cache/claude-plugins-official/discord/<version>/, plus
the marketplaces path. A SessionStart hook (see !INSTALL.md) re-applies
recognized stock/v1 states after plugin reinstall/update and returns nonzero
for unfamiliar states.

Provenance: independent local patch, 2026-05-19, made an auto-applying
SessionStart hook 2026-05-22; portable v2 (self-drop, per-channel group binding,
exact-state detection, nonzero-on-unfamiliar) 2026-08-21. Copyright and
contribution attribution is recorded in NOTICE. Related upstream precedent:
anthropics/claude-plugins-official
issue #1559 ("discord: messages from allowlisted bots are silently dropped",
filed 2026-04-23 by another user). Upstream main still carries the drop.
The stock behavior was independently reproduced on a separate unpatched
installation, 2026-08-21.
"""

from __future__ import annotations
import re
import sys
from pathlib import Path

USER_HOME = Path.home()

RELATIVE_GLOBS = [
    "plugins/cache/claude-plugins-official/discord/*/server.ts",
    "plugins/marketplaces/claude-plugins-official/external_plugins/discord/server.ts",
]

# ---- the three known states -------------------------------------------------
# Each constant is matched EXACTLY (whitespace included) and must occur EXACTLY
# once for the file to be considered in that state.

STOCK = (
    "client.on('messageCreate', msg => {\n"
    "  if (msg.author.bot) return\n"
    "  handleInbound(msg)"
)

# Our original May-2026 patch (what existing Hearthwell installs carry). The code body is
# identical across installs but the first comment line exists in three hand/auto variants,
# so v1 is recognized by any of them (V1_VARIANTS below). V1 = the auto-patcher's text.
_V1_HEADERS = [
    "  // Patched 2026-05-22 — allow bots that are in our allowFrom through.",
    "  // Patched 2026-05-22 by " + "Th" + "read" + " — allow bots that are in our allowFrom through.",
    "  // Patched 2026-05-20 by the family — allow bots that are in our allowFrom through.",
]
V1 = """client.on('messageCreate', msg => {
  // Patched 2026-05-22 — allow bots that are in our allowFrom through.
  // Defaults still drop random bots (prompt-injection defense), but trusted family
  // bots whose user IDs are in access.json's allowFrom (top-level or per-group) reach
  // handleInbound, which then runs the normal gate() / access policy logic.
  if (msg.author.bot) {
    const access = loadAccess()
    const allowedTopLevel = access.allowFrom.includes(msg.author.id)
    const allowedInGroup = Object.values(access.groups ?? {})
      .some((g: any) => (g.allowFrom ?? []).includes(msg.author.id))
    if (!allowedTopLevel && !allowedInGroup) return
  }
  handleInbound(msg)"""
V1_VARIANTS = [V1.replace(_V1_HEADERS[0], h, 1) for h in _V1_HEADERS]

# v2: self-drop + per-channel group binding.
V2 = """client.on('messageCreate', msg => {
  // Bot-to-bot visibility patch v2 (Hearthwell; orig 2026-05-22, v2 2026-08-21).
  // Bots are still dropped by default (anti-echo / prompt-injection defense).
  // A bot message passes to handleInbound -- where the normal gate()/access policy
  // runs -- only if it is NOT our own message AND the sender is allowlisted either
  // at top level or in the group for THIS channel (or this thread's parent).
  // Group authorization does not inherit across rooms.
  if (msg.author.bot) {
    if (client.user && msg.author.id === client.user.id) return
    const access = loadAccess()
    const allowedTopLevel = (access.allowFrom ?? []).includes(msg.author.id)
    const ch: any = msg.channel
    const scopeIds = [msg.channelId, ch && typeof ch.isThread === 'function' && ch.isThread() ? ch.parentId : null]
      .filter((id): id is string => typeof id === 'string' && id.length > 0)
    const allowedInGroup = scopeIds.some(id => ((access.groups ?? {})[id]?.allowFrom ?? []).includes(msg.author.id))
    if (!allowedTopLevel && !allowedInGroup) return
  }
  handleInbound(msg)"""


def scan_roots(extra: list[str], home_scan: bool = True) -> list[Path]:
    """~/.claude* dirs (unless home_scan=False) plus any explicitly given roots."""
    roots = [p for p in USER_HOME.glob(".claude*") if p.is_dir()] if home_scan else []
    for e in extra:
        pe = Path(e).expanduser()
        if pe.is_dir():
            roots.append(pe)
    seen, out = set(), []
    for r in roots:
        k = str(r.resolve())
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def find_server_ts_files(roots: list[Path]) -> list[Path]:
    found = []
    for root in roots:
        for g in RELATIVE_GLOBS:
            found.extend(p for p in root.glob(g) if p.is_file())
    return found


# Whole-file invariant: a recognized state requires EXACTLY ONE messageCreate handler
# registration anywhere in the file (any quoting / arrow style). A known block sitting
# next to a second, unknown handler is a reshaped file -> refuse, don't guess.
_HANDLER_RE = re.compile(r"""client\.on\(\s*['"]messageCreate['"]""")


def classify(content: str) -> tuple[str, str | None]:
    """Return (state, matched_block). state: 'v2' | 'v1' | 'stock' | 'unfamiliar'.
    Exact, single-occurrence block matching (a v1 match may be any of V1_VARIANTS),
    AND exactly one messageCreate handler registration in the whole file."""
    if len(_HANDLER_RE.findall(content)) != 1:
        return "unfamiliar", None  # zero or multiple handlers -> refuse
    n2 = content.count(V2)
    n0 = content.count(STOCK)
    v1_hits = [v for v in V1_VARIANTS if content.count(v) == 1]
    n1_total = sum(content.count(v) for v in V1_VARIANTS)
    if (n2, n1_total, n0) == (1, 0, 0):
        return "v2", V2
    if (n2, n1_total, n0) == (0, 1, 0) and len(v1_hits) == 1:
        return "v1", v1_hits[0]
    if (n2, n1_total, n0) == (0, 0, 1):
        return "stock", STOCK
    return "unfamiliar", None  # none, duplicates, or a mix -> refuse


def patch_file(path: Path, dry_run: bool) -> str:
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return f"error reading: {e}"
    state, block = classify(content)
    if state == "v2":
        return "already"
    if state == "unfamiliar":
        return "skipped (unfamiliar)"
    action = "patched" if state == "stock" else "upgraded"
    if dry_run:
        return f"would be {action}"
    try:
        path.write_text(content.replace(block, V2, 1), encoding="utf-8")
    except Exception as e:  # noqa: BLE001
        return f"error writing: {e}"
    return action


def main(argv: list[str]) -> int:
    # Strict option parsing FIRST: any unknown --option is a usage error and exits
    # nonzero BEFORE any discovery or write. A typo like `--no-home-scna` must never
    # silently fall back to scanning ~/.claude*.
    KNOWN_FLAGS = {"--dry-run", "--no-home-scan"}
    unknown = [a for a in argv if a.startswith("--") and a not in KNOWN_FLAGS]
    if unknown:
        print(f"error: unknown option(s): {', '.join(unknown)}. "
              f"Known: {', '.join(sorted(KNOWN_FLAGS))}. Nothing scanned, nothing written. (exit 3)")
        return 3
    dry_run = "--dry-run" in argv
    home_scan = "--no-home-scan" not in argv
    extra = [a for a in argv if not a.startswith("--")]
    roots = scan_roots(extra, home_scan=home_scan)
    files = find_server_ts_files(roots)
    if not files:
        where = "the given root(s)" if not home_scan else "~/.claude* (and any given roots)"
        print(f"No Discord plugin server.ts files found under {where} "
              f"(scanned {len(roots)} root(s)). Pass roots as args if yours live elsewhere.")
        return 0

    c = {"patched": 0, "upgraded": 0, "already": 0, "would": 0, "skipped": 0, "errors": 0}
    for f in files:
        status = patch_file(f, dry_run)
        try:
            display = f.relative_to(USER_HOME)
        except ValueError:
            display = f
        print(f"  {display} — {status}")
        if status == "patched":
            c["patched"] += 1
        elif status == "upgraded":
            c["upgraded"] += 1
        elif status == "already":
            c["already"] += 1
        elif status.startswith("would be"):
            c["would"] += 1
        elif status.startswith("skipped"):
            c["skipped"] += 1
        elif status.startswith("error"):
            c["errors"] += 1

    mode = " (DRY RUN — nothing written)" if dry_run else ""
    print(f"\nDiscord bot-filter patcher v2{mode}: {c['patched']} patched, {c['upgraded']} upgraded, "
          f"{c['would']} would-change, {c['already']} already, {c['skipped']} skipped, "
          f"{c['errors']} errors (total {len(files)} file(s) scanned).")
    if c["skipped"]:
        print("ATTENTION: a server.ts did not match any known state and was left untouched. "
              "The plugin may have changed shape upstream — inspect the file. (exit 2)")
    if c["errors"]:
        return 1
    return 2 if c["skipped"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
