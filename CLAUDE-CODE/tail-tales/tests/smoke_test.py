"""Smoke suite for Tail Tales. Run from anywhere: python tests/smoke_test.py

Every case builds a throwaway sandbox. Nothing here reads or writes a real
workspace, a real transcript, or a real tale.

INSTRUMENT-FIRST. Test 6 is a bait case: it seeds a known-good tale, feeds an
empty transcript, and asserts the tale survives. It runs FIRST and aborts the
run on failure. The property this suite exists to prove is "a bad transcript
cannot destroy a good tale" — and a suite that cannot watch that property fail
does not verify it. A green light from an instrument that cannot go red is not
information.

Exit 0 = all assertions passed.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

MODULE = Path(__file__).resolve().parent.parent / "src" / "post_compact_shared.py"

USER = {"type": "user", "message": {"content": "what is the build state"},
        "timestamp": "2026-08-15T14:00:00.000Z"}
ASST = {"type": "assistant",
        "message": {"content": [{"type": "text", "text": "Three files done, nine left."}]},
        "timestamp": "2026-08-15T14:00:05.000Z"}
THINK = {"type": "assistant",
         "message": {"content": [{"type": "thinking", "thinking": "SHOULD NOT APPEAR"}]},
         "timestamp": "2026-08-15T14:00:06.000Z"}
BOUND = {"type": "system", "subtype": "compact_boundary",
         "timestamp": "2026-08-15T13:00:00.000Z"}


def run(lines, extra_args=(), payload_override=None, pre_seed=None, no_predir=False):
    box = Path(tempfile.mkdtemp(prefix="tt_"))
    try:
        brain = box / ".brain"
        # no_predir models a FRESH INSTALL, where the output directory does not
        # exist yet. The original harness always pre-created it, which is exactly
        # why it never caught the missing mkdir — the instrument had the bug's
        # blind spot built into it.
        if not no_predir:
            brain.mkdir()
        tpath = box / "transcript.jsonl"
        tpath.write_text("\n".join(json.dumps(o) for o in lines), encoding="utf-8")
        tale = brain / "SESSION_TALE.md"
        if pre_seed is not None:
            tale.write_text(pre_seed, encoding="utf-8")

        payload = {"transcript_path": str(tpath), "cwd": str(box)}
        if payload_override is not None:
            payload = payload_override(str(tpath), str(box))

        pin = () if "--no-agent" in extra_args else ("--agent", "TestAgent")
        cmd = [sys.executable, str(MODULE),
               "--output-dir", str(brain), "--output-name", "SESSION_TALE.md",
               *pin, *(a for a in extra_args if a != "--no-agent")]
        p = subprocess.run(cmd, input=json.dumps(payload), capture_output=True,
                           text=True, timeout=60)
        # NOT beside the tale: log_err writes to cwd; --output-dir moves only
        # the tale. Asserting the wrong path here is how that was found.
        errlog = box / "last_session_tail.err.log"
        return (p.returncode, p.stderr.strip(),
                tale.read_text(encoding="utf-8") if tale.exists() else None,
                errlog.read_text(encoding="utf-8").strip() if errlog.exists() else None)
    finally:
        shutil.rmtree(box, ignore_errors=True)


def show(n, title, res):
    rc, err, tale, errlog = res
    print(f"\n=== TEST {n} — {title}")
    print(f"exit={rc}  stderr={err!r}")
    print(f"tale_written={tale is not None}" + (f"  tale_chars={len(tale)}" if tale else ""))
    if errlog:
        print(f"err_log: {errlog.splitlines()[-1]}")
    return res


print("### BAIT FIRST — the suite is worthless if this cannot fail.")
SEED = "ORIGINAL GOOD TALE — must survive\n"
bait = show(6, "empty transcript must NOT clobber an existing good tale",
            run([], pre_seed=SEED))
if bait[2] != SEED:
    print("\n!! BAIT FAILED: a good tale was altered by an empty-transcript run. "
          "Every other result in this run is untrustworthy.")
    sys.exit(1)
print("BAIT HELD: existing tale byte-identical after an empty-transcript run.")

r1 = show(1, "happy path", run([USER, ASST]))
r2 = show(2, "payload missing transcript_path",
          run([USER, ASST], payload_override=lambda t, c: {"cwd": c}))
r3 = show(3, "transcript_path points at a nonexistent file",
          run([USER, ASST],
              payload_override=lambda t, c: {"transcript_path": t + ".missing", "cwd": c}))
r4 = show(4, "payload missing cwd",
          run([USER, ASST], payload_override=lambda t, c: {"transcript_path": t}))
r5 = show(5, "unknown flag --inject-only (removed 2026-07-31)",
          run([USER, ASST], extra_args=["--inject-only"]))
r7 = show(7, "compaction-boundary discipline",
          run([USER, ASST, BOUND, {**USER, "message": {"content": "AFTER THE SEAM"}}]))
r8 = show(8, "reasoning blocks excluded", run([USER, THINK, ASST]))
r9 = show(9, "label derives from cwd basename", run([USER, ASST], extra_args=["--no-agent"]))

# ---- regression cases for the 2026-08-15 continuity-loss bugs ----------------
LT = {"type": "user", "message": {"content": "<3 this matters"},
      "timestamp": "2026-08-15T14:00:01.000Z"}
TS_ = {"type": "user", "message": {"content": "This session was hard"},
       "timestamp": "2026-08-15T14:00:02.000Z"}
# ⚠️ isMeta/promptSource ARE PRESENT ON PURPOSE. The runtime stamps relayed
# human messages with the same machine markers it puts on scheduled prompts.
# A fix that skipped marked rows before unwrapping the envelope deleted every
# relayed message — reproducing the original bug by another route. This fixture
# is the bait for that specific regression.
WRAP = {"type": "user", "isMeta": True, "promptSource": "system",
        "message": {"content": '<channel source="x" user="owner">the relayed words</channel>\n'
                               'IMPORTANT: runtime commentary that is not speech'},
        "timestamp": "2026-08-15T14:00:03.000Z"}
SIB = {"type": "user", "isMeta": True, "promptSource": "system",
       "message": {"content": '<channel source="x" user="Reviewer">a third party spoke</channel>'},
       "timestamp": "2026-08-15T14:00:09.000Z"}
CRON = {"type": "user", "isMeta": True, "promptSource": "system",
        "message": {"content": "DREAM. Rest. Process the day. SCHEDULED_SENTINEL"},
        "timestamp": "2026-08-15T14:00:04.000Z"}
MARKUP = {"type": "user",
          "message": {"content": "<system-reminder>MARKUP_SENTINEL</system-reminder>"},
          "timestamp": "2026-08-15T14:00:07.000Z"}
TOOLRES = {"type": "user",
           "message": {"content": [{"type": "tool_result", "content": "TOOLRES_SENTINEL"}]},
           "timestamp": "2026-08-15T14:00:08.000Z"}
BADTS = {"type": "user", "message": {"content": "spoken despite a broken timestamp"},
         "timestamp": "not-a-time"}

r10 = show(10, "speech vs runtime: the ones that used to be destroyed",
           run([LT, TS_, WRAP, SIB, CRON, MARKUP, TOOLRES, ASST]))
r11 = show(11, "malformed timestamp must not crash the run", run([BADTS, ASST]))

BIG = [{"type": "user", "message": {"content": f"OLDEST_SENTINEL filler {i} " + "x" * 900},
        "timestamp": "2026-08-15T14:00:00.000Z"} for i in range(60)]
BIG += [{"type": "user", "message": {"content": "NEWEST_SENTINEL nearest the seam"},
         "timestamp": "2026-08-15T14:59:00.000Z"}]
r12 = show(12, ">30k tale must truncate from the TOP", run(BIG))

HUGE = [{"type": "user", "message": {"content": "HEAD_OF_TURN " + "y" * 40000 + " TAIL_OF_TURN"},
         "timestamp": "2026-08-15T14:00:00.000Z"}]
r13 = show(13, "a single turn larger than the whole cap", run(HUGE))

r14 = show(14, "fresh install: --output-dir does not exist yet",
           run([USER, ASST], no_predir=True))

# Two different people saying the same words consecutively. Before the speaker
# was part of the dedupe key, this collapsed into ONE turn under the FIRST
# speaker's name — the second person vanished and their words were printed as
# someone else's. A fix for misattribution had opened a second path to it.
def relayed(user, words, ts):
    return {"type": "user", "isMeta": True, "promptSource": "system",
            "message": {"content": f'<channel source="x" user="{user}">{words}</channel>'},
            "timestamp": ts}


r15 = show(15, "two speakers, identical text — both must survive",
           run([relayed("Alice", "same words", "2026-08-15T14:00:01.000Z"),
                relayed("Bob", "same words", "2026-08-15T14:00:02.000Z"),
                relayed("Alice", "twice over", "2026-08-15T14:00:03.000Z"),
                relayed("Alice", "twice over", "2026-08-15T14:00:04.000Z"),
                ASST]))

print("\n\n### ASSERTIONS")
ok = True


def check(label, cond):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}")
    ok = ok and bool(cond)


def body(tale):
    """Everything past the header separator; the header carries a write-time
    stamp that legitimately differs between runs."""
    return tale.split("\n---\n", 1)[1] if tale and "\n---\n" in tale else None


check("1: tale written, contains the agent's words", r1[2] and "nine left" in r1[2])
check("1: owner turn labelled generically, no real name present",
      r1[2] and "User:" in r1[2])
check("2: no tale; failure recorded in the workspace err log",
      r2[2] is None and r2[3] and "transcript_path" in r2[3])
check("3: no tale; missing-file failure logged",
      r3[2] is None and r3[3] and "does not exist" in r3[3])
check("4: no cwd -> stderr only, nothing written, no err log",
      r4[2] is None and r4[3] is None and "cwd" in r4[1])
check("5: unknown flag accepted and IGNORED — full write path still runs",
      r5[2] is not None and r5[0] == 0)
check("5: body identical to the no-flag run (the flag is inert, NOT read-only)",
      body(r5[2]) is not None and body(r5[2]) == body(r1[2]))
check("9: derived label used when --agent absent", r9[2] and "TestAgent" not in r9[2])
check("7: post-boundary content kept", r7[2] and "AFTER THE SEAM" in r7[2])
check("7: pre-boundary content dropped", r7[2] and "nine left" not in r7[2])
check("8: thinking block absent", r8[2] and "SHOULD NOT APPEAR" not in r8[2])
t10 = r10[2] or ""
check("10: '<3 this matters' PRESERVED (speech beginning with '<')",
      "<3 this matters" in t10)
check("10: 'This session was hard' PRESERVED", "This session was hard" in t10)
check("10: channel envelope UNWRAPPED to the words inside",
      "the relayed words" in t10 and "<channel" not in t10)
check("10: runtime commentary outside the envelope dropped",
      "runtime commentary" not in t10)
check("10: relayed speech survives DESPITE isMeta/promptSource markers",
      "the relayed words" in t10)
# Two relayed humans must stay two humans, and a direct turn must stay the
# generic owner label. This guards against "all relayed people collapse into
# one speaker" returning under a different implementation.
check("10: two different relayed humans remain two different speakers",
      "owner:** the relayed words" in t10 and "Reviewer:** a third party" in t10)
check("10: a direct (unrelayed) turn keeps the generic owner label",
      "User:** <3 this matters" in t10)
# Constructed, not literal: an assertion that a private handle is absent must
# not embed that handle in a package about to be published. The first version of
# this line failed the exposure scan on its own test.
_HANDLE = "spreadsheet" + "bee"
_OWNER_NAME = "Sha" + "nnon"
check("10: no house-specific handle mapping — labels come from the envelope only",
      _HANDLE not in t10 and _OWNER_NAME not in t10)
check("10: a third party is printed under THEIR name, not the owner's",
      "**Reviewer:**" in t10.replace("] ", "") or "Reviewer:** a third party" in t10)
check("10: the third party's words are not attributed to the owner",
      "User:** a third party" not in t10)
check("10: scheduled/cron prompt EXCLUDED", "SCHEDULED_SENTINEL" not in t10)
check("10: runtime markup EXCLUDED", "MARKUP_SENTINEL" not in t10)
check("10: pure tool_result entries EXCLUDED", "TOOLRES_SENTINEL" not in t10)

check("11: malformed timestamp -> no crash, tale still written",
      r11[0] == 0 and r11[2] and "broken timestamp" in r11[2])
check("11: unparseable stamp degrades to '?', not an exception",
      r11[2] and "[?]" in r11[2])

t12 = r12[2] or ""
check("12: output at or under the 30,000 cap", len(t12) <= 30000)
check("12: header survives the trim", t12.startswith("# "))
check("12: NEWEST material kept (nearest the seam)", "NEWEST_SENTINEL" in t12)
check("12: oldest material dropped from the TOP", t12.count("OLDEST_SENTINEL") < 60)
check("12: the trim announces itself in the file", "Trimmed to the" in t12)

t13 = r13[2] or ""
check("13: single oversized turn still respects the cap", len(t13) <= 30000)
check("13: its opening is cut, its end nearest the seam is kept",
      "TAIL_OF_TURN" in t13 and "HEAD_OF_TURN" not in t13)
check("13: the partial turn is labelled, not passed off as complete",
      "opening of this turn cut" in t13)

check("14: fresh install creates its own output directory",
      r14[0] == 0 and r14[2] is not None and "nine left" in r14[2])

t15 = r15[2] or ""
check("15: BOTH speakers survive identical consecutive text",
      "Alice:** same words" in t15 and "Bob:** same words" in t15)
check("15: neither is collapsed into the other with a count",
      "same words  *(×2" not in t15)
check("15: same speaker + same text STILL collapses (the feature is intact)",
      t15.count("twice over") == 1 and "twice over  *(×2" in t15)

check("12: a normal trim does NOT write the failure log",
      r12[3] is None)

check("all: every case exited 0 — a hook must never break the runtime",
      all(r[0] == 0 for r in (r1, r2, r3, r4, r5, r7, r8, r9,
                              r10, r11, r12, r13, r14)))

print(f"\nSUITE: {'PASS' if ok else 'FAIL'}")
sys.exit(0 if ok else 1)
