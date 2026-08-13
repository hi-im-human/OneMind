"""
SessionStart hook — Freestyle Beats reminder.

Fires when Claude Code starts, resumes, or clears a session. Reminds the agent
to run /freestyle-beats to confirm their in-session crons are in place.
Idempotent — safe to run even if nothing was lost.

Registration in the agent's `.claude/settings.json` (replace <PACKAGE_ROOT>
with the absolute path where you installed this package — Claude Code hook
commands require absolute paths):

    "hooks": {
      "SessionStart": [
        {
          "matcher": "",
          "hooks": [
            {
              "type": "command",
              "command": "python \"<PACKAGE_ROOT>/src/hooks/session_start_reminder.py\""
            }
          ]
        }
      ]
    }

If several agents on one machine share this package, point every agent's
settings.json at this same file — updates then propagate without per-agent
copies drifting apart.
"""

import json
import sys


def main():
    # SessionStart payload arrives on stdin; this hook doesn't need to parse it —
    # the reminder is the same regardless of how the session started.
    try:
        sys.stdin.read()
    except Exception:
        pass

    notice = (
        "Session started or resumed. Check your beats (`/freestyle-beats`) before "
        "beginning unrelated work — skipping the check is how schedule drift "
        "accumulates silently. An urgent request from your human, an active "
        "correction, a safety issue, or an explicit pause/hold outranks this; handle "
        "it first, then return to the check. In-session crons have flimsy "
        "persistence: session breaks can kill them and they auto-expire after 7 days "
        "regardless. The skill is idempotent: it checks CronList first and recreates "
        "only what's missing. Cost of running when everything is alive: small and "
        "routine. Cost of not running when it's dead: silent drift."
    )

    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": notice,
        }
    }))


if __name__ == "__main__":
    main()
