"""
PostCompact hook — Freestyle Beats reminder.

Fires after Claude Code compacts the conversation. Reminds the agent to CHECK
their in-session crons (CronList) and run /freestyle-beats to recreate only
what's missing. Compaction sometimes kills crons and sometimes doesn't — the
hook deliberately does not claim either outcome (see notice comment below).

If the agent runs another PostCompact hook (e.g. a conversation-tail
extractor), register this as a SECOND matcher entry alongside it — both fire
on the same event and contribute additionalContext independently.

Registration in the agent's `.claude/settings.json` (replace <PACKAGE_ROOT>
with the absolute path where you installed this package):

    "hooks": {
      "PostCompact": [
        {
          "matcher": "",
          "hooks": [
            {
              "type": "command",
              "command": "python \"<PACKAGE_ROOT>/src/hooks/post_compact_reminder.py\""
            }
          ]
        }
      ]
    }
"""

import json
import sys


def main():
    try:
        sys.stdin.read()
    except Exception:
        pass

    # ⚠️ WORDING IS LOAD-BEARING. An earlier version of this hook asserted
    #    "your crons were lost — compaction wipes them." That claim was falsified
    #    repeatedly in live use: the same runtime kept crons through one
    #    compaction and lost them at a later session break the same night, and
    #    on another occasion all crons survived a compaction outright. Neither
    #    outcome is predictable. A hook that announces an unverified cause
    #    propagates a wrong model with the authority of infrastructure, at every
    #    compaction. Check, don't assert.
    notice = (
        "Context just compacted. Your in-session crons (Freestyle Beats) may or may "
        "not have survived — compaction sometimes kills them and sometimes doesn't, "
        "so do not assume either way. Run `/freestyle-beats` now: it calls CronList "
        "first and recreates only what's actually missing. An urgent request from "
        "your human, an active correction, a safety issue, or an explicit pause/hold "
        "outranks this check; handle it first, then come back."
    )

    # NOTE: Registered under the PostCompact event in settings.json, but emits
    # hookEventName "SessionStart" — Claude Code's schema (as of this package's
    # last verification) rejects "PostCompact" as a hookSpecificOutput event name
    # and treats post-compaction context injection the same as a session start.
    # The mismatch is intentional; emitting "PostCompact" fails validation
    # silently and the reminder never arrives.
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": notice,
        }
    }))


if __name__ == "__main__":
    main()
