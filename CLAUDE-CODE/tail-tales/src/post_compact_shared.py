"""Extract a bounded post-compaction session tail from the runtime payload.

The hook reads ``transcript_path`` and ``cwd`` from PostCompact stdin, writes one
tail file to the supplied workspace, and does not inject tail content into context.
The display label derives from the workspace basename unless ``--agent`` overrides it.
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# A relayed message (chat bridge, mail, any external channel) arrives wrapped in
# a <channel ...>…</channel> envelope. The speaker's actual words are INSIDE it,
# and the envelope's `user` attribute says who spoke.
CHANNEL_RE = re.compile(r"<channel\b([^>]*)>(.*?)</channel>", re.DOTALL)
CHANNEL_USER_RE = re.compile(r'\buser="([^"]*)"')

# Tag-shaped opener: `<` then a LETTER. Distinguishes real markup from ordinary
# speech that merely begins with `<` — "<3 this matters", "<-- like that one".
TAG_OPEN_RE = re.compile(r"^</?[A-Za-z][\w:.-]*(\s|/?>)")

RESUME_BANNER = "This session is being continued from a previous conversation"

# Timestamps render in the runtime machine's local timezone without requiring a
# named timezone database.
TAIL_TURNS = 40       # conversational turns (user/agent)

# The writer enforces the cap. When trimming is required, it removes oldest turns
# so content nearest the compaction boundary remains available.
HARD_CAP = 30000

# Label written for direct user turns in the tail.
OWNER_LABEL = "User"

ERR_LOG_NAME = "last_session_tail.err.log"


def owner_words(text):
    """Return direct or envelope-unwrapped user text; skip runtime markup."""
    if not text:
        return []
    relayed = [(CHANNEL_USER_RE.search(attrs), body.strip())
               for attrs, body in CHANNEL_RE.findall(text)]
    relayed = [(m.group(1) if m else None, b) for m, b in relayed if b]
    if relayed:
        return relayed
    if TAG_OPEN_RE.match(text):
        return []
    if text.startswith(RESUME_BANNER):
        return []
    return [(None, text)]


def ts_local(entry):
    """Parse an entry timestamp, or return None for malformed values."""
    raw = entry.get("timestamp")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone()
    except (ValueError, TypeError, OverflowError):
        return None


def is_skill_invocation(text):
    """Return true for known skill/cron payload preambles only."""
    head = text[:400]
    return (
        head.startswith("Base directory for this skill:")
        or "\nBase directory for this skill:" in head
        or (text.startswith("<command-name>") and "circadian-heartbeat" in head)
    )


def get_recent_turns(path, agent_label, n=TAIL_TURNS):
    turns = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []

    for raw in lines:
        if not raw.strip():
            continue
        try:
            entry = json.loads(raw)
        except Exception:
            continue

        etype = entry.get("type")
        ts = ts_local(entry)

        if etype == "system" and entry.get("subtype") == "compact_boundary":
            turns.append({"type": "boundary", "ts": ts})
            continue

        if etype == "user":
            content = entry.get("message", {}).get("content", "")
            if isinstance(content, list) and all(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content
            ):
                continue
            if isinstance(content, str):
                text = content.strip()
            elif isinstance(content, list):
                text = "\n".join(
                    b.get("text", "") for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                ).strip()
            else:
                text = ""
            # Parse channel envelopes before runtime-row exclusions: relayed
            # messages can carry the same metadata as scheduled prompts.
            spoken = owner_words(text)
            if not spoken:
                continue
            relayed = any(speaker is not None for speaker, _ in spoken)
            if not relayed and (entry.get("isMeta") is True
                                or entry.get("promptSource") == "system"):
                continue          # machine-authored and not relayed: a prompt
            for speaker, words in spoken:
                if is_skill_invocation(words):
                    continue
                turns.append({"type": "owner", "ts": ts,
                              "text": words, "speaker": speaker})

        elif etype == "assistant":
            content = entry.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                btype = block.get("type")
                # Exclude reasoning and tool-use blocks from persisted output.
                if btype == "text":
                    t = block.get("text", "").strip()
                    if t:
                        # Keep one internal label for detection, counting, and formatting.
                        turns.append({"type": "agent", "ts": ts, "text": t})

    last_boundary = max(
        (i for i, t in enumerate(turns) if t["type"] == "boundary"),
        default=-1,
    )
    relevant = turns[last_boundary + 1:] if last_boundary >= 0 else turns

    conv = 0
    start = 0
    for i in range(len(relevant) - 1, -1, -1):
        if relevant[i]["type"] in ("owner", "agent"):
            conv += 1
            if conv >= n:
                start = i
                break
    return relevant[start:]


def collapse_repeats(turns):
    """Collapse only adjacent text-equal turns from the same speaker and type."""
    out = []
    for t in turns:
        prev = out[-1] if out else None
        if (prev and prev["type"] == t["type"] and prev["text"] == t["text"]
                and prev.get("speaker") == t.get("speaker")):
            prev["repeats"] = prev.get("repeats", 1) + 1
            continue
        out.append(dict(t))
    return out


def format_turn(t, agent_label):
    ts_str = t["ts"].strftime("%H:%M:%S") if t.get("ts") else "?"
    typ = t["type"]
    rep = t.get("repeats", 1)
    suffix = f"  *(×{rep} — identical message repeated)*" if rep > 1 else ""
    if typ == "owner":
        # Preserve the channel-envelope speaker label when present.
        speaker = t.get("speaker") or OWNER_LABEL
        return f"**[{ts_str}] {speaker}:** {t['text']}{suffix}\n"
    if typ == "agent":
        return f"**[{ts_str}] {agent_label}:** {t['text']}{suffix}\n"
    return ""


TRIM_NOTE = ("*⚠️ Trimmed to the {cap:,}-character cap. {n} older turn(s) dropped — "
             "the turns nearest the compaction seam are kept, the oldest are cut first. "
             "This file is the only copy; the dropped turns are not recoverable from it.*")

PARTIAL_MARKER = "**[… opening of this turn cut to fit the cap …]** "


def build_tale(header, body, cap=HARD_CAP):
    """Assemble the tale at or under `cap` characters, dropping the OLDEST turns.

    Returns (text, dropped_turn_count).

    Truncation removes oldest turns so the newest compaction-adjacent material
    remains in the bounded output.

    The header always survives, so a trimmed tale still says whose it is, when
    it was written, and which transcript it came from. A trim is announced in
    the file itself: this is the only copy, and a silent trim would be
    indistinguishable from a quiet session.
    """
    full = "\n".join(header + body)
    if len(full) <= cap:
        return full, 0

    # Reserve the notice up front so adding it can never push us back over.
    note = TRIM_NOTE.format(cap=cap, n=len(body))
    shell = header[:-1] + [note, ""]
    budget = cap - len("\n".join(shell)) - 1

    kept, used = [], 0
    for entry in reversed(body):          # newest first — oldest fall off the top
        cost = len(entry) + 1
        if used + cost > budget:
            break
        kept.append(entry)
        used += cost
    kept.reverse()

    if not kept and body:
        # Degenerate case: one turn alone exceeds the whole budget. Keep its
        # TAIL, consistent with top-truncation, and label it — so a fragment is
        # never mistaken for a complete message.
        room = budget - len(PARTIAL_MARKER) - 1
        if room > 0:
            kept = [PARTIAL_MARKER + body[-1][-room:]]

    dropped = len(body) - len(kept)
    text = "\n".join(header[:-1] + [TRIM_NOTE.format(cap=cap, n=dropped), ""] + kept)

    # If recomputing the trim notice exceeds the cap, remove more oldest entries.
    while len(text) > cap and kept:
        kept.pop(0)
        dropped += 1
        text = "\n".join(header[:-1] + [TRIM_NOTE.format(cap=cap, n=dropped), ""] + kept)

    return text, dropped


def derive_agent_label(cwd_path, override=None):
    """Override wins. Otherwise: cwd basename with leading non-letter chars
    stripped (`⚙️Ada` → `Ada`). If that strip yields empty, fall back to the
    raw basename so the script never crashes on weird workspace names.
    """
    if override:
        return override
    name = cwd_path.name
    stripped = name.lstrip("".join(c for c in name if not c.isalpha()))
    return stripped or name


def log_err(cwd_path, msg):
    """Best-effort: append a failure note to a sibling file in the workspace
    so next-agent sees it on session start. Never raises.
    """
    try:
        err = cwd_path / ERR_LOG_NAME
        ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
        with err.open("a", encoding="utf-8") as f:
            f.write(f"--- {ts} ---\n{msg}\n\n")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--agent", default=None,
                        help="Override agent display label (default: derived from cwd basename)")
    parser.add_argument("--output-dir", default=None,
                        help="Override output directory for the tail file (default: cwd)")
    parser.add_argument("--output-name", default="last_session_tail.md",
                        help="Override output filename (default: last_session_tail.md)")
    args, _ = parser.parse_known_args()

    # Read and parse stdin payload for transcript_path and cwd.
    try:
        payload_text = sys.stdin.read()
        payload = json.loads(payload_text) if payload_text else {}
    except Exception as e:
        # Can't even parse stdin — there's no workspace to log into. Bail silently.
        sys.stderr.write(f"tail-tales: failed to parse stdin: {e}\n")
        return

    transcript_str = payload.get("transcript_path")
    cwd_str = payload.get("cwd")

    # Write eligible failures to the workspace log when a workspace is available.
    if not cwd_str:
        sys.stderr.write("tail-tales: stdin payload missing cwd\n")
        return
    cwd_path = Path(cwd_str)
    if not transcript_str:
        log_err(cwd_path, "stdin payload missing transcript_path")
        return

    transcript = Path(transcript_str)
    output_dir = Path(args.output_dir) if args.output_dir else cwd_path
    output = output_dir / args.output_name
    agent_label = derive_agent_label(cwd_path, override=args.agent)

    if not transcript.exists():
        log_err(cwd_path, f"transcript_path does not exist: {transcript}")
        return

    turns = get_recent_turns(transcript, agent_label)
    if not turns:
        log_err(cwd_path, f"no turns extracted from {transcript.name} (boundary at end?)")
        return

    turns = collapse_repeats(turns)
    conv_turns = sum(1 for t in turns if t["type"] in ("owner", "agent"))

    now = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %Z")
    header = [
        f"# {agent_label} — Last Session Tail",
        f"*Written by post_compact hook at {now}*",
        f"*Source: `{transcript.name}`*",
        f"*Last {conv_turns} conversational turns before compaction "
        f"(reasoning + tool calls excluded; consecutive duplicates collapsed)*",
        "",
        "---",
        "",
    ]
    body = [b for t in turns if (b := format_turn(t, agent_label))]

    # Write the bounded tail to disk; this hook does not inject its contents.
    full_text, dropped = build_tale(header, body)
    try:
        # Generate the output directory. A fresh install points --output-dir at a
        # workspace subdirectory that does not exist yet; without this the very
        # first compaction wrote nothing and logged a failure the agent never saw.
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(full_text, encoding="utf-8")
        # NOTE: a trim is NOT logged to the error file. Trimming at the cap is
        # normal, expected operation, and every public contract in this package
        # states that `last_session_tail.err.log` appears ONLY on failure. An
        # earlier version logged here, which would have made a routine long day
        # look like a fault. The trim announces itself inside the tale instead,
        # where the reader of the tale will actually see it.
    except Exception as e:
        log_err(cwd_path, f"write failed for {output}: {e}")


if __name__ == "__main__":
    main()
