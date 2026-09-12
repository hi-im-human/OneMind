"""RED CONTROLS for the persisted-beat cap / restart-recovery gap.

Object: `src/scheduler.py` at a97c28d (2026-08-18, "v1.1.0: add durable personal
scheduler"). `MAX_USER_ENTRIES = 8` was compiled in three weeks before the quest
board began assigning three slots per quest on top of seven circadian beats.

THE FAILURE IS NOT THE CAP. It is that the cap decides what the recovery path is
capable of knowing about:
  * `_validate_entries` refuses the FILE WRITE above 8. CronCreate is untouched,
    so the beats register and fire.
  * on restart, only the file is reconciled, so overflow beats vanish.
  * `foreign_count` (line 685-689) detects present-and-unmanaged. This failure is
    absent-and-unrecorded: after the restart there is no task left to count.
  * the startup notice correctly forbids re-deriving beats from the goal files,
    which is exactly what forecloses the one path that would have noticed.

An entry that cannot be written cannot be missed.

These four tests must FAIL against a97c28d and PASS after the fix. The two green
controls must pass BOTH times — a control that fails everything proves nothing.
"""
import importlib.util
import unittest
from pathlib import Path

PACKAGE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "freestyle_scheduler_rc", PACKAGE / "src" / "scheduler.py"
)
scheduler = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(scheduler)


def entries(n, enabled=True):
    """n distinct valid entries. Distinct cron AND prompt: the validator rejects
    duplicate (cron, prompt) pairs, so a lazy fixture would fail for the wrong
    reason and look like the bug."""
    out = []
    for i in range(n):
        out.append({
            "id": "beat-%02d" % i,
            "label": "work" if i % 2 else "personal",
            "cron": "%d %d * * *" % (i % 60, (i // 2) % 24),
            "prompt": "Beat number %d does its own distinct thing." % i,
            "enabled": enabled,
        })
    return out


def schedule_with(n):
    return {
        "schema_version": 2,
        "timezone": "local",
        "maintenance_cron": "17 4 * * *",
        "entries": entries(n),
    }


class RestartRecoveryGap(unittest.TestCase):

    # ---------- RED 1: the structural load must be persistable ----------
    def test_structural_load_fits_in_the_file(self):
        """7 circadian + 3 quest slots + 1 personal = 11.

        This is not a hypothetical number: it is what the quest board assigns as
        of 2026-09-12. If the file cannot hold it, the overflow beats are live
        and unrecoverable by construction."""
        scheduler.schedule_from_candidate(schedule_with(11))

    # ---------- RED 2: the only ceiling may be the platform's ----------
    def test_ceiling_is_the_platform_limit_not_a_number_of_ours(self):
        """Maintenance occupies one live task, so user entries may go up to
        CRON_TASK_LIMIT - 1 and no lower a bound of our own invention."""
        usable = scheduler.CRON_TASK_LIMIT - 1
        scheduler.schedule_from_candidate(schedule_with(usable))

    # ---------- RED 3: a refusal must state the consequence ----------
    def test_refusal_names_the_restart_consequence(self):
        """If any ceiling remains, the write-time refusal is the last moment the
        agent can learn that an unwritten beat will not survive a restart."""
        with self.assertRaises(scheduler.ScheduleError) as caught:
            scheduler.schedule_from_candidate(schedule_with(scheduler.CRON_TASK_LIMIT + 5))
        message = str(caught.exception).lower()
        self.assertIn("restart", message)

    # ---------- RED 4: the notice must say what it cannot vouch for ----------
    def test_notice_admits_it_cannot_see_unpersisted_crons(self):
        """The startup notice reports a count taken from the file and tells the
        agent to create/delete only package-owned differences. That count reads
        as complete while being silently partial: a live beat absent from the
        file is invisible to it, and after a restart there is nothing left to
        count. The notice must say so.

        Rendered notice, not the source string that builds it — the first
        version of this test scraped source and failed on a bad anchor, which
        looks identical to failing on the defect."""
        import json, tempfile
        from pathlib import Path
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        workspace = Path(temp.name).resolve()
        schedule = scheduler.schedule_from_candidate(schedule_with(3))
        scheduler.atomic_write_schedule(workspace, schedule)
        payload = json.dumps({"cwd": str(workspace), "source": "startup"})
        text = scheduler.hook_notice("SessionStart", payload)
        text = text["hookSpecificOutput"]["additionalContext"].lower()

        # sanity: the notice rendered at all, so a miss below is about content
        self.assertIn("freestyle beats", text)
        self.assertTrue(
            "not in this file" in text or "will not survive" in text,
            "notice does not warn that live beats absent from the file are "
            "invisible to it and die on restart; got: %s" % text,
        )

    # ---------- GREEN CONTROLS: must pass before AND after ----------
    def test_green_ordinary_schedule_still_valid(self):
        scheduler.schedule_from_candidate(schedule_with(3))

    def test_green_absurd_count_still_refused(self):
        """The fix removes OUR number, not all bounds. Above the platform limit
        must still refuse — otherwise these tests would pass on a build with no
        validation at all."""
        with self.assertRaises(scheduler.ScheduleError):
            scheduler.schedule_from_candidate(schedule_with(scheduler.CRON_TASK_LIMIT + 5))


if __name__ == "__main__":
    unittest.main()
