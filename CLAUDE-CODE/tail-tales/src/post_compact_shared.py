"""
Tail Tales — shared PostCompact hook, one copy for every Claude Code agent.

Replaces a set of near-identical per-agent scripts (post_compact_<agent>.py, one
per agent, each with its own hardcoded paths). All per-agent config is now
derived from the PostCompact stdin payload Claude Code already hands the hook at
fire time:

    transcript_path → which jsonl just compacted (canonical)
    cwd             → which agent's workspace (canonical)

Hardcoded PROJECTS_DIR / OUTPUT constants are gone. When an agent's workspace
moves, this script keeps working with zero edits — because the runtime told it
where to look, not a constant somebody had to remember to update.

Agent display name (for "Ada (thinking):" / "Bly:" labels) comes from the
cwd basename with leading non-letter chars stripped (e.g. `⚙️Ada` → `Ada`).
An `--agent` argv flag overrides if the auto-derivation ever needs to.

2026-07-31: Injection removed (owner ruling). Tail Tales now ONLY writes the session
tail file to disk. Selfhook replacement tells agents to read their files
(including SESSION_TALE.md) on compaction — no injection needed here.

Origin: 2026-06-10, after one agent's per-agent script silently captured a
week-stale tail because PROJECTS_DIR still pointed at the old workspace path.
Doctrine: runtime-payload-as-source-of-truth beats hardcoded constants for any
per-agent script. (Adopted house-wide after the incident above.)
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

# Timestamps render in the RUNTIME MACHINE'S OWN LOCAL TIME.
#
# This was previously a hardcoded IANA zone. Two problems, both real for anyone
# installing this outside the household it was written in: it stamped every
# tale with a timezone the reader does not live in, and on Windows `zoneinfo`
# needs the external `tzdata` package to resolve an IANA name at all — an
# undeclared dependency that happened to be installed on the build machine, so
# nothing ever failed here. `.astimezone()` with no argument asks the platform,
# needs no timezone database, and is right by default wherever it runs.
TAIL_TURNS = 40       # conversational turns (owner/agent)

# HARD_CAP — THE LIVE CONTRACT, enforced in build_tale() on the write path.
# There is ONE file, the agent reads it directly, and nothing injects a copy of
# it, so the write path is the only place a limit can live. Over the cap, the
# OLDEST turns are dropped: the material nearest the compaction seam is what a
# returning agent needs, so it is the last to go. Owner rulings, 2026-08-15:
#   "The enforcement comes from the write-path."
#   "truncation is from the *top* of the file, not the bottom."
#   "No git enforcement on Tail Tales."
HARD_CAP = 30000

# --- HISTORY, 2026-07-29. ⚠️ REVERSED IN PART — DOES NOT DESCRIBE CURRENT ------
# ⚠️ Item 4 below is OBSOLETE. This hook no longer injects anything; injection
# was removed 2026-07-31 and the agent reads the file itself. Kept because the
# MEASUREMENTS are why the cap exists at all, and because a design record that
# quietly deletes its reversed half teaches the next reader nothing. Do not read
# any of this as an explanation of how enforcement works now — that is the
# block above.
#
# MEASURED before changing anything: every agent's tail was over the old
# 20,000-char inject cap, none of them slightly.
#     43,291 · 35,975 · 37,843 · 72,596  (four agents, one house)
# The cap had never once been met, so it was not a limit — it fired every
# compaction and silently dropped the END of the file, i.e. the most recent
# material before the seam. ~109,705 chars lost across four agents each time.
# **That is why truncation now runs from the top.**
#
# Four changes made then:
#   1. THINKING DROPPED. Reasoning was capped at 300 chars, so it arrived as
#      truncated fragments — the anxiety without the resolution. It is also the
#      single most RECONSTRUCTABLE thing in the file: same agent, same situation,
#      similar thoughts. The owner's exact words cannot be regenerated at all.
#      Spending the budget on our deliberation stored the recoverable and
#      dropped the irrecoverable.  [STILL LIVE]
#   2. TOOL CALLS DROPPED — never carried texture, only volume.  [STILL LIVE]
#   3. CONSECUTIVE DUPLICATE MESSAGES COLLAPSED — a relog/auth error repeating
#      N times now reads once with a count.  [STILL LIVE — but the key now
#      includes the SPEAKER; see collapse_repeats().]
#   4. HARD CAP at 30,000, and this hook INJECTS the tail itself rather than
#      telling the agent to go read it.  ⛔ **REVERSED 2026-07-31.** The cap
#      survived and moved to the write path; the injection did not survive at
#      all. For two weeks this package's own records explained the cap's
#      non-enforcement in terms of an injected copy that no longer existed.
# ---------------------------------------------------------------------------

# Where to log failures so they're visible to next-agent (sibling of the tail).
# Label written for the human's turns in the tail. Set to whatever the owner
# is called in your house; it appears in every user turn of every tale.
OWNER_LABEL = "User"

ERR_LOG_NAME = "last_session_tail.err.log"


def owner_words(text):
    """Return [(speaker_or_None, words), ...] spoken in a `user` turn. [] to skip.

    ⚠️ THE BUG THIS REPLACES — the worst one this package ever had, because it
    destroyed exactly the material the package exists to preserve.

    The old test was `not text.startswith("<")`, meant to skip runtime markup.
    But every message relayed through an external channel arrives wrapped in a
    `<channel ...>` envelope. So the filter discarded ALL of them. Measured on a
    single live transcript: **12,181 owner turns dropped.** Across four agents,
    every "owner" line that survived into a tale was a scheduler prompt — not
    one was a person speaking. The file whose header promises the owner's exact
    words contained none of them, and had not for its entire existence.

    The design rationale made it worse rather than better: reasoning was dropped
    on the grounds that the agent's thoughts are reconstructable while the
    owner's words are not. The filter then discarded the irreplaceable half and
    kept the recoverable one.

    Three behaviours, in order:
      1. Channel envelopes are UNWRAPPED, not skipped — the inner text is the
         message, and the envelope's `user` attribute names who said it, so a
         relayed sibling is never printed under the owner's name. Trailing
         runtime commentary outside the envelope is dropped.
      2. Genuine markup (a `<` followed by a LETTER) is skipped. Ordinary speech
         beginning with `<` — "<3 this matters" — is kept, because `3` is not a
         letter and the old blanket test ate sentences like that too.
      3. Only the exact resume banner is skipped, not every line that happens to
         begin "This session".
    """
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
    """Parse an entry timestamp, or return None.

    GUARDED DELIBERATELY. A single malformed timestamp anywhere in the
    transcript used to raise ValueError out of main(), producing a traceback,
    exit 1, no tale, and no error log — which falsified this package's own
    "every failure path exits 0" claim. One bad row must not cost the whole
    tale; format_turn already renders a missing timestamp as `?`.
    """
    raw = entry.get("timestamp")
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).astimezone()
    except (ValueError, TypeError, OverflowError):
        return None


def is_skill_invocation(text):
    """True if a 'user' turn is really a skill/cron payload, not the owner talking.

    WHY (measured, 2026-08-01): every /circadian-heartbeat fires with the
    full SKILL.md attached and it was being recorded as an 11,235-char owner
    turn. Seven crons a day, 40-turn window. Measured across the four CC agents:

        agent A  37,151 chars | 33,720 boilerplate (91%)
        agent B  46,019 chars | 33,715 boilerplate (73%)
        agent C  17,139 chars | 11,242 boilerplate (66%)

    One agent had ~3,400 chars of real conversation left in an entire tail. The
    tale exists to hold the material nearest the seam; skill text was eating it.
    Kept deliberately narrow — matches the invocation preamble, not content that
    merely mentions a skill.
    """
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
            # ⚠️ ORDER IS LOAD-BEARING. The envelope test runs FIRST, because a
            # relayed message is POSITIVE EVIDENCE OF A PERSON and must outrank
            # every machine-row heuristic below it.
            #
            # This ordering exists because getting it wrong reproduced the very
            # bug being fixed. The runtime marks relayed human messages with the
            # SAME `isMeta` / `promptSource` fields it puts on scheduled prompts.
            # A skip-if-marked test placed ahead of the unwrap therefore deletes
            # every relayed message — which is exactly what the old `startswith`
            # filter did, arriving by a different route.
            #
            # Owner ruling 2026-08-15: "No cron injections should be shown in
            # Tail Tales. My user messages SHOULD be there."
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
                # `thinking` and `tool_use` deliberately skipped (2026-07-29).
                # Reasoning is reconstructable by the same agent; the owner's words
                # are not. Tool calls were pure volume.
                if btype == "text":
                    t = block.get("text", "").strip()
                    if t:
                        # Intentionally uniform internal label across detect/count/format.
                        # Do not re-split into per-agent labels; that recreated the old
                        # copy/rename sync footgun identified in owner review.
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
    """Collapse consecutive turns with identical text from THE SAME SPEAKER.

    Added 2026-07-29 (owner ruling): a relog/auth error that fires N times used to eat
    N slots of a budget that was already over cap. Now it reads once, with a count.
    Only CONSECUTIVE identical text collapses — a phrase legitimately repeated
    later in the conversation is left alone, because that repetition is real.

    ⚠️ SPEAKER IS PART OF THE KEY, AND MUST STAY THERE (fixed 2026-08-15).

    The key was `type` + `text` only. That was harmless while every relayed turn
    rendered under one label — and became a defect the moment relayed speakers
    were preserved, because two different people saying the same words
    consecutively collapsed into one turn under the FIRST speaker's name.
    Measured: three turns from two speakers produced a single
    `Alice: same words (×3)`. Bob did not merely lose his attribution; he
    disappeared, and his words were printed as someone else's.

    **A fix for misattribution opened a second path to misattribution.** In a
    continuity record the speaker is not decoration — whoever the file says
    spoke is who the next agent will believe spoke.
    """
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
        # A relayed turn is printed under the name the envelope gave it, so a
        # third party's words are never rendered as the owner's. Attribution in
        # a continuity record is not cosmetic — whoever the file says spoke is
        # who the next agent will believe spoke.
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

    THE DIRECTION IS LOAD-BEARING. Truncation is from the TOP — owner ruling,
    2026-08-15: "truncation is from the *top* of the file, not the bottom."
    The turns nearest the compaction seam are exactly what a returning agent
    needs, so they are the last thing to go. An earlier cap elsewhere in this
    household cut from the end and silently removed precisely that material.

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

    # Guarantee the invariant by construction rather than by arithmetic: if the
    # recomputed notice nudged us over, shed further OLDEST entries. Never slice
    # the tail — that would cut the newest material and invert the ruling.
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

    # Read and parse stdin payload — canonical source for transcript_path and cwd.
    try:
        payload_text = sys.stdin.read()
        payload = json.loads(payload_text) if payload_text else {}
    except Exception as e:
        # Can't even parse stdin — there's no workspace to log into. Bail silently.
        sys.stderr.write(f"tail-tales: failed to parse stdin: {e}\n")
        return

    transcript_str = payload.get("transcript_path")
    cwd_str = payload.get("cwd")

    # Safety-review hardening (2026-06-11): if we have a workspace,
    # failures must be visible there; stderr-only is acceptable only when
    # there is no trustworthy workspace to write to.
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

    # Write the tail to disk. The agent reads it via the continuity file list.
    # Injection removed 2026-07-31 (owner ruling): Tail Tales writes only, and a
    # separate hook tells agents to read their continuity files on compaction.
    #
    # THE CAP IS ENFORCED HERE, ON THE WRITE PATH. There is exactly one file and
    # no injected copy, so this is the only place a limit can live. Owner ruling
    # 2026-08-15: "Enforcement on Tail Tales is NOT necessary [at git]. Tail Tales
    # are re-written every compaction. The enforcement comes from the write-path."
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
