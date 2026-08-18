"""
SessionStart hook — Freestyle Beats persisted-schedule reconciliation.

Fires when Claude Code starts, resumes, clears, forks, or restores compacted
context. It reads workspace identity from hook stdin and asks the agent to
reconcile the persisted personal schedule through CronList/CronDelete/CronCreate.

Registration in the agent's `.claude/settings.json` (replace both placeholders
with absolute paths):

    "hooks": {
      "SessionStart": [
        {
          "matcher": "",
          "hooks": [
            {
              "type": "command",
              "command": "\"<PYTHON_EXECUTABLE>\" \"<SKILL_DIR>/src/hooks/session_start_reminder.py\""
            }
          ]
        }
      ]
    }

Each installed skill copy keeps its own workspace-local schedule. This public
package does not depend on a shared or family scheduler.
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scheduler import emit_hook_notice  # noqa: E402


def main():
    emit_hook_notice("SessionStart")


if __name__ == "__main__":
    main()
