# Freestyle Beats — Dependencies

## Hard requirements

| dependency | why | failure without it |
|---|---|---|
| Claude Code 2.1.196+ | skill/project path substitution and scheduled-task runtime | package unavailable or paths unresolved |
| `CronList` | authoritative live task list | no safe reconciliation or capacity check |
| `CronCreate` | create missing/replacement tasks | restore/refresh incomplete |
| `CronDelete` | remove duplicates, drift, or prior refreshed tasks | duplicate/drift cleanup incomplete |
| Python 3.8+ absolute interpreter path | scheduler CLI and both hooks | hooks silently fail or CLI unavailable |
| writable non-symlink `<WORKSPACE>/.claude/` | canonical state and Claude runtime task storage | state/runtime scheduling fails |
| `<WORKSPACE>/.claude/settings.json` | hook registration | no automatic session/compaction reconciliation request |
| `<WORKSPACE>/.claude/skills/` | installed self-contained skill | `/freestyle-beats` unavailable |

`CLAUDE_CODE_DISABLE_CRON=1` disables scheduled tasks and is incompatible with the
package's runtime function.

## Setup-only inputs

| path | use | behavior when missing |
|---|---|---|
| `<WORKSPACE>/WORK_GOALS.md` | generate first/replacement work beats | setup/replace stops |
| `<WORKSPACE>/PERSONAL_GOALS.md` | generate first/replacement personal beats | setup/replace stops |
| `<SKILL_DIR>/src/templates/SCHEDULE.template.json` | candidate structure | setup/replace cannot prepare validated input |

After setup, goal files are not restoration sources. The persisted schedule is
canonical until explicit replacement.

## Runtime behavior relied upon

Current official source: `https://code.claude.com/docs/en/scheduled-tasks`.

- tasks are session-scoped and fresh conversations clear them;
- `--resume`/`--continue` restore only unexpired jobs;
- recurring jobs expire seven days after creation;
- `CronList` exposes task IDs, recurring status, human-readable schedules, and truncated
  prompt previews to the model; the package uses only ID/status/complete compact prefix;
- `CronDelete` deletes by eight-character task ID;
- `CronCreate` accepts five-field local-time cron expressions and recurring flag;
- recurring fires have deterministic runtime jitter;
- tasks fire only while Claude Code is open and idle, with no missed-fire catch-up;
- one session holds at most 50 scheduled tasks;
- Claude Code owns its internal task file under `.claude` and rejects symlinked task
  storage. Freestyle Beats does not use that internal file as an interface.

Any runtime change requires rerunning live acceptance tests.

## Paths read at runtime

- `<SKILL_DIR>/SKILL.md`
- `<SKILL_DIR>/src/scheduler.py`
- `<SKILL_DIR>/src/hooks/session_start_reminder.py`
- `<SKILL_DIR>/src/hooks/post_compact_reminder.py`
- `<WORKSPACE>/.claude/freestyle-beats/schedule.json`
- `<WORKSPACE>/.claude/freestyle-beats/candidate.json` during setup/replace only
- `<WORKSPACE>/.claude/freestyle-beats/live-crons.json` during plan/verify only
- `<WORKSPACE>/.claude/freestyle-beats/plan.json` during pre-delete verification only
- `<WORKSPACE>/.claude/freestyle-beats/after-create.json` during pre-delete verification only
- hook stdin JSON (`cwd`, `source`, and common event fields)
- complete live task state via `CronList`

## Paths written/generated

- `<WORKSPACE>/.claude/freestyle-beats/schedule.json` — scheduler CLI, atomic replace
- same-directory `schedule.*.tmp` — scheduler CLI, removed before return
- `candidate.json` — agent, temporary, removed after successful persistence
- `live-crons.json` — agent, complete temporary CronList normalization, removed after
  verification
- `plan.json` — scheduler, temporary saved reconciliation plan, removed after verification
- `after-create.json` — agent, temporary complete post-create CronList normalization,
  removed after verification
- installed `<SKILL_DIR>/SKILL.md` and `<SKILL_DIR>/src/**` — installer/upgrade
- two hook entries in `<WORKSPACE>/.claude/settings.json` — installer
- package-marked runtime tasks — Claude agent through cron tools

The package never reads or writes Claude Code's undocumented internal task file.

## Calls/tools

- absolute Python interpreter for hooks;
- `python <SKILL_DIR>/src/scheduler.py` for create/show/validate/maintain/plan/
  verify-predelete/verify/uninstall-plan;
- Claude Code `CronList`, `CronCreate`, and `CronDelete`;
- normal file read/write/delete tools for the two temporary JSON files.

No network API, daemon, service account, database, OS scheduled task, cloud routine, or
paid dependency is used.

## Triggers and consumers

| trigger/consumer | reads/does |
|---|---|
| SessionStart hook | validates state metadata and injects setup/reconcile context |
| PostCompact hook | validates state metadata and injects indeterminate-survival reconcile context |
| `/freestyle-beats setup` | creates canonical personal state and initial runtime jobs |
| `/freestyle-beats reconcile` | aligns package-owned live jobs with state |
| daily maintenance task | instructs the agent to invoke `/freestyle-beats maintain` |
| `/freestyle-beats maintain` | selects reconcile or refresh from last verified refresh age |
| `/freestyle-beats refresh` | create-first renewal of every package-owned job |
| `/freestyle-beats replace` | explicit state replacement plus reconciliation |

## Config sources

- hook payload `cwd` is canonical for hook workspace selection; hooks do not fall back to
  process environment when it is missing/malformed;
- `${CLAUDE_PROJECT_DIR}` is the CLI/skill workspace path;
- `${CLAUDE_SKILL_DIR}` locates bundled scheduler/templates;
- `<WORKSPACE>/.claude/settings.json` registers hooks;
- schedule state stores local-time contract, ownership instance/key, exact entries,
  maintenance cron, and verification timestamps.

## Reverse dependencies and move hazards

- Moving/removing `<SKILL_DIR>` breaks both hook commands and the skill.
- Moving the workspace changes the canonical schedule path; move the state directory
  with the workspace and update absolute hook paths if needed.
- Changing Python location breaks hooks until settings uses the new absolute interpreter.
- Replacing `schedule.json` with the template destroys instance data/receipts and is forbidden;
  use the explicit replace procedure.
- Symlinking/junctioning `.claude`, `freestyle-beats`, state, candidate, or live JSON is
  rejected by the package.

## Explicit non-dependencies

- external/shared schedules and private installation files;
- another agent's state, cron IDs, or workspace;
- prior conversation context;
- `--resume` as a durability mechanism;
- direct access to Claude Code's internal scheduler file.
