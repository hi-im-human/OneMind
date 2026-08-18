"""
PostCompact hook — Freestyle Beats persisted-schedule reconciliation.

Fires after Claude Code compacts the conversation. It reads workspace identity
from hook stdin and asks the agent to reconcile persisted state. Compaction can
retain or remove live cron registrations, so the hook claims neither outcome.

If the agent runs another PostCompact hook (e.g. a conversation-tail
extractor), register this as a SECOND matcher entry alongside it — both fire
on the same event, and the runtime BLENDS their outputs into one context
injection without clear boundaries. If you accumulate several hooks on this event, combine
them into one script that prints a single payload with a short header per
concern; the headers preserve the boundaries the runtime doesn't.

Registration in the agent's `.claude/settings.json` (replace both placeholders
with absolute paths):

    "hooks": {
      "PostCompact": [
        {
          "matcher": "",
          "hooks": [
            {
              "type": "command",
              "command": "\"<PYTHON_EXECUTABLE>\" \"<SKILL_DIR>/src/hooks/post_compact_reminder.py\""
            }
          ]
        }
      ]
    }
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scheduler import emit_hook_notice  # noqa: E402


def main():
    emit_hook_notice("PostCompact")


if __name__ == "__main__":
    main()
