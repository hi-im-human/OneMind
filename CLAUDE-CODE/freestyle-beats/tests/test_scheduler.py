import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
MODULE_PATH = PACKAGE / "src" / "scheduler.py"
SPEC = importlib.util.spec_from_file_location("freestyle_scheduler", MODULE_PATH)
scheduler = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(scheduler)


def candidate(prompt="Do the exact task."):
    return {
        "schema_version": 2,
        "timezone": "local",
        "maintenance_cron": "17 4 * * *",
        "entries": [
            {
                "id": "work-one",
                "label": "work",
                "cron": "17 9 * * *",
                "prompt": prompt,
                "enabled": True,
            },
            {
                "id": "personal-one",
                "label": "personal",
                "cron": "23 18 * * *",
                "prompt": "Take one personal action.",
                "enabled": True,
            },
        ],
    }


def live_from_expected(schedule):
    return [
        {
            "id": f"id{index:06d}"[-8:],
            "cron": task["cron"],
            "prompt": task["prompt"],
            "recurring": True,
        }
        for index, task in enumerate(scheduler.expected_tasks(schedule), start=1)
    ]


class SchedulerTests(unittest.TestCase):
    def make_workspace(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Path(temp.name).resolve()

    def persist(self, workspace, data=None):
        schedule = scheduler.schedule_from_candidate(data or candidate())
        scheduler.atomic_write_schedule(workspace, schedule)
        return scheduler.load_schedule(workspace)

    def test_round_trip_preserves_literal_prompt(self):
        workspace = self.make_workspace()
        prompt = 'Quotes " stay; backslash \\ stays; snowman ☃\nsecond line.  '
        schedule = self.persist(workspace, candidate(prompt))
        self.assertEqual(prompt, schedule["entries"][0]["prompt"])

    def test_invalid_replacement_keeps_existing_state(self):
        workspace = self.make_workspace()
        first = self.persist(workspace)
        path = scheduler.schedule_path(workspace)
        before = path.read_bytes()
        broken = candidate()
        broken["entries"][0]["cron"] = "99 99 * * *"
        with self.assertRaises(scheduler.ScheduleError):
            scheduler.schedule_from_candidate(broken, previous=first)
        self.assertEqual(before, path.read_bytes())

    def test_replacement_preserves_origin_date_but_resets_verification_receipts(self):
        original = scheduler.schedule_from_candidate(candidate())
        original["last_reconciled_at"] = "2026-08-17T10:00:00+00:00"
        original["last_refreshed_at"] = "2026-08-17T10:00:00+00:00"
        replacement_data = candidate("Replacement task.")
        replacement = scheduler.schedule_from_candidate(replacement_data, previous=original)
        self.assertEqual(original["created_at"], replacement["created_at"])
        self.assertIsNone(replacement["last_reconciled_at"])
        self.assertIsNone(replacement["last_refreshed_at"])

    def test_schema_rejects_unknown_keys_and_duplicates(self):
        bad = candidate()
        bad["surprise"] = True
        with self.assertRaisesRegex(scheduler.ScheduleError, "unknown keys"):
            scheduler.schedule_from_candidate(bad)

        duplicate = candidate()
        duplicate["entries"][1]["cron"] = duplicate["entries"][0]["cron"]
        duplicate["entries"][1]["prompt"] = duplicate["entries"][0]["prompt"]
        with self.assertRaisesRegex(scheduler.ScheduleError, "duplicate cron"):
            scheduler.schedule_from_candidate(duplicate)

    def test_persisted_timestamp_validation_rejects_naive_and_out_of_order_values(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        naive = dict(schedule, updated_at="2026-08-17T12:00:00")
        with self.assertRaisesRegex(scheduler.ScheduleError, "timezone-aware UTC"):
            scheduler.validate_schedule(naive)

        earlier = dict(
            schedule,
            created_at="2026-08-17T12:00:00+00:00",
            updated_at="2026-08-17T11:00:00+00:00",
        )
        with self.assertRaisesRegex(scheduler.ScheduleError, "must not precede"):
            scheduler.validate_schedule(earlier)

    def test_at_least_two_entries_must_remain_enabled(self):
        bad = candidate()
        bad["entries"][1]["enabled"] = False
        with self.assertRaisesRegex(scheduler.ScheduleError, "at least 2 enabled"):
            scheduler.schedule_from_candidate(bad)

    def test_prompt_rejects_skill_invocation_and_reserved_marker(self):
        for prompt in (
            "/review-pr",
            "Do it [freestyle-beats:fake|work]",
            "Do it [fb1:reserved]",
        ):
            bad = candidate(prompt)
            with self.assertRaises(scheduler.ScheduleError):
                scheduler.schedule_from_candidate(bad)

    def test_cron_validation(self):
        valid = ("17 4 */5 * *", "0 9 * * 1-5", "1,15,30 0-23/2 * * 0,7")
        for expression in valid:
            self.assertEqual(expression, scheduler.validate_cron(expression))
        for expression in (
            "* * * *",
            "60 4 * * *",
            "0 24 * * *",
            "0 0 * JAN *",
            "*/999 4 * * *",
            "5/2 4 * * *",
        ):
            with self.assertRaises(scheduler.ScheduleError):
                scheduler.validate_cron(expression)

    def test_missing_live_state_creates_all_expected_tasks(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        plan = scheduler.plan_actions(schedule, [])
        creates = [action for action in plan["actions"] if action["action"] == "create"]
        self.assertEqual(3, len(creates))
        self.assertEqual(
            {"work-one", "personal-one", "maintenance"},
            {action["entry_id"] for action in creates},
        )

    def test_exact_state_is_idempotent_and_foreign_tasks_are_untouched(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        live = live_from_expected(schedule)
        live.append(
            {"id": "foreign1", "cron": "0 12 * * *", "prompt": "Foreign", "recurring": True}
        )
        plan = scheduler.plan_actions(schedule, live)
        self.assertEqual([], plan["actions"])
        self.assertEqual(3, len(plan["kept"]))
        self.assertEqual(1, plan["foreign_task_count"])

    def test_model_visible_cronlist_prefix_is_sufficient(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        visible = []
        for index, task in enumerate(scheduler.expected_tasks(schedule), start=1):
            self.assertLessEqual(len(task["prompt"].split(" ", 1)[0]), 70)
            visible.append(
                {
                    "id": f"id{index:06d}",
                    "prompt": task["prompt"][:78] + "…",
                    "recurring": True,
                }
            )
        normalized = scheduler.normalize_live_tasks({"tasks": visible})
        self.assertEqual([], scheduler.plan_actions(schedule, normalized)["actions"])
        self.assertTrue(scheduler.verify_live_state(schedule, normalized)["ok"])

    def test_cut_marker_prefix_stops_instead_of_becoming_foreign(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        live = [{"id": "deadbeef", "prompt": "[fb1:cut…", "recurring": True}]
        with self.assertRaisesRegex(scheduler.ScheduleError, "truncated or malformed"):
            scheduler.plan_actions(schedule, live)

    def test_duplicate_drift_and_orphan_are_repaired_without_foreign_delete(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        live = live_from_expected(schedule)
        live.append(dict(live[0], id="dupe0001"))
        wanted = scheduler.expected_tasks(schedule)[1]
        old_digest = scheduler.payload_digest(
            wanted["entry_id"],
            wanted["label"],
            wanted["kind"],
            "24 18 * * *",
            schedule["entries"][1]["prompt"],
        )
        live[1] = dict(
            live[1],
            cron="Every day at 6:24 PM",
            prompt=scheduler.marker(
                schedule, wanted["entry_id"], wanted["label"], old_digest
            )
            + " Old prompt preview…",
        )
        live.append(
            {
                "id": "orphan01",
                "cron": "7 7 * * *",
                "prompt": scheduler.marker(
                    schedule,
                    "old-entry",
                    "work",
                    scheduler.payload_digest(
                        "old-entry", "work", "beat", "7 7 * * *", "Old"
                    ),
                )
                + " Old",
                "recurring": True,
            }
        )
        live.append(
            {"id": "foreign1", "cron": "0 12 * * *", "prompt": "Foreign", "recurring": True}
        )
        plan = scheduler.plan_actions(schedule, live)
        delete_ids = {
            action["cron_id"]
            for action in plan["actions"]
            if action["action"] == "delete"
        }
        create_ids = {
            action["entry_id"]
            for action in plan["actions"]
            if action["action"] == "create"
        }
        self.assertIn(live[1]["id"], delete_ids)
        self.assertIn("orphan01", delete_ids)
        self.assertEqual(1, len({"dupe0001", live[0]["id"]} & delete_ids))
        self.assertEqual({"personal-one"}, create_ids)
        self.assertNotIn("foreign1", delete_ids)

    def test_public_or_wrong_instance_marker_is_foreign_and_never_deleted(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        other = scheduler.schedule_from_candidate(candidate())
        live = live_from_expected(schedule)
        live.extend(
            [
                {
                    "id": "spoof001",
                    "cron": "7 7 * * *",
                    "prompt": "[fb1:000000000000:00000000:000000000000:00000000000000000000] Spoof",
                    "recurring": True,
                },
                {
                    "id": "other001",
                    "cron": "8 8 * * *",
                    "prompt": scheduler.marker(
                        other,
                        "other",
                        "work",
                        scheduler.payload_digest(
                            "other", "work", "beat", "8 8 * * *", "Other"
                        ),
                    )
                    + " Other",
                    "recurring": True,
                },
            ]
        )
        plan = scheduler.plan_actions(schedule, live)
        delete_ids = {
            action["cron_id"]
            for action in plan["actions"]
            if action["action"] == "delete"
        }
        self.assertFalse({"spoof001", "other001"} & delete_ids)
        self.assertEqual(2, plan["foreign_task_count"])

    def test_refresh_recreates_every_managed_task(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        live = live_from_expected(schedule)
        plan = scheduler.plan_actions(schedule, live, refresh=True)
        self.assertEqual(3, sum(x["action"] == "delete" for x in plan["actions"]))
        self.assertEqual(3, sum(x["action"] == "create" for x in plan["actions"]))
        first_delete = next(i for i, action in enumerate(plan["actions"]) if action["action"] == "delete")
        last_create = max(i for i, action in enumerate(plan["actions"]) if action["action"] == "create")
        self.assertLess(last_create, first_delete)

    def test_predelete_verification_requires_observed_replacements(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        live = live_from_expected(schedule)
        plan = scheduler.plan_actions(schedule, live, refresh=True)
        before = scheduler.verify_predelete(schedule, live, plan)
        self.assertFalse(before["ok"])
        self.assertTrue(any("expected at least 2" in problem for problem in before["problems"]))

        after = list(live)
        for index, task in enumerate(scheduler.expected_tasks(schedule), start=100):
            after.append(
                {
                    "id": f"id{index:06d}",
                    "cron": task["cron"],
                    "prompt": task["prompt"],
                    "recurring": True,
                }
            )
        verified = scheduler.verify_predelete(schedule, after, plan)
        self.assertTrue(verified["ok"], verified)

    def test_uninstall_plan_deletes_only_signed_current_instance_tasks(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        other = scheduler.schedule_from_candidate(candidate())
        live = live_from_expected(schedule)
        live.extend(
            [
                {
                    "id": "foreign1",
                    "cron": "0 8 * * *",
                    "prompt": "Foreign",
                    "recurring": True,
                },
                {
                    "id": "other001",
                    "cron": "0 9 * * *",
                    "prompt": scheduler.marker(
                        other,
                        "other",
                        "work",
                        scheduler.payload_digest(
                            "other", "work", "beat", "0 9 * * *", "Other"
                        ),
                    )
                    + " Other",
                    "recurring": True,
                },
            ]
        )
        uninstall = scheduler.plan_uninstall(schedule, live)
        self.assertEqual(3, uninstall["owned_task_count"])
        self.assertEqual(2, uninstall["foreign_task_count"])
        self.assertEqual(
            {"id000001", "id000002", "id000003"},
            {action["cron_id"] for action in uninstall["delete_actions"]},
        )

    def test_create_first_capacity_guard_blocks_without_actions(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        live = live_from_expected(schedule)
        for index in range(47):
            live.append(
                {
                    "id": f"f{index:07d}",
                    "cron": "0 12 * * *",
                    "prompt": f"Foreign {index}",
                    "recurring": True,
                }
            )
        plan = scheduler.plan_actions(schedule, live, refresh=True)
        self.assertTrue(plan["blocked"])
        self.assertEqual([], plan["actions"])
        self.assertGreater(plan["projected_peak_task_count"], 50)

    def test_maintenance_mode_refreshes_at_five_days_not_every_daily_fire(self):
        schedule = scheduler.schedule_from_candidate(candidate())
        self.assertEqual("refresh", scheduler.maintenance_mode(schedule)["mode"])
        schedule["last_refreshed_at"] = "2026-08-10T12:00:00+00:00"
        schedule["updated_at"] = "2026-08-10T12:00:00+00:00"
        before = scheduler.maintenance_mode(
            schedule,
            scheduler.parse_utc_timestamp("2026-08-15T11:59:59+00:00", "test"),
        )
        due = scheduler.maintenance_mode(
            schedule,
            scheduler.parse_utc_timestamp("2026-08-15T12:00:00+00:00", "test"),
        )
        self.assertEqual("reconcile", before["mode"])
        self.assertEqual("refresh", due["mode"])

    def test_session_death_and_expiry_simulation_restore_exact_state(self):
        workspace = self.make_workspace()
        schedule = self.persist(workspace)
        empty_plan = scheduler.plan_actions(schedule, [])
        created = [x for x in empty_plan["actions"] if x["action"] == "create"]
        restored_live = [
            {
                "id": f"new{index:05d}"[-8:],
                "cron": task["cron"],
                "prompt": task["prompt"],
                "recurring": task["recurring"],
            }
            for index, task in enumerate(created, start=1)
        ]
        self.assertTrue(scheduler.verify_live_state(schedule, restored_live)["ok"])
        self.assertEqual([], scheduler.plan_actions(schedule, restored_live)["actions"])

    def test_verify_records_only_after_exact_success(self):
        workspace = self.make_workspace()
        schedule = self.persist(workspace)
        live_path = scheduler.schedule_path(workspace).parent / "live.json"
        live_path.write_text(
            json.dumps({"tasks": live_from_expected(schedule)}), encoding="utf-8"
        )
        args = type("Args", (), {"live": str(live_path), "record_mode": "refresh"})
        result = scheduler._command_verify(args, workspace)
        self.assertTrue(result["ok"])
        updated = scheduler.load_schedule(workspace)
        self.assertIsNotNone(updated["last_reconciled_at"])
        self.assertIsNotNone(updated["last_refreshed_at"])

    def test_failed_verify_leaves_receipts_byte_identical(self):
        workspace = self.make_workspace()
        self.persist(workspace)
        state_path = scheduler.schedule_path(workspace)
        before = state_path.read_bytes()
        live_path = state_path.parent / "live.json"
        live_path.write_text(json.dumps({"tasks": []}), encoding="utf-8")
        args = type("Args", (), {"live": str(live_path), "record_mode": "refresh"})
        result = scheduler._command_verify(args, workspace)
        self.assertFalse(result["ok"])
        self.assertEqual(before, state_path.read_bytes())

    def test_plan_output_and_predelete_cli_round_trip(self):
        workspace = self.make_workspace()
        schedule = self.persist(workspace)
        state_dir = scheduler.schedule_path(workspace).parent
        live_path = state_dir / "live.json"
        plan_path = state_dir / "plan.json"
        after_path = state_dir / "after-create.json"
        live = live_from_expected(schedule)
        live_path.write_text(json.dumps({"tasks": live}), encoding="utf-8")
        plan_args = type(
            "Args",
            (),
            {"live": str(live_path), "refresh": True, "output": str(plan_path)},
        )
        plan = scheduler._command_plan(plan_args, workspace)
        self.assertTrue(plan_path.is_file())
        saved = json.loads(plan_path.read_text(encoding="utf-8"))
        self.assertEqual(plan["schedule_fingerprint"], saved["schedule_fingerprint"])

        after = list(live)
        for index, task in enumerate(scheduler.expected_tasks(schedule), start=200):
            after.append(
                {
                    "id": f"id{index:06d}",
                    "cron": task["cron"],
                    "prompt": task["prompt"],
                    "recurring": True,
                }
            )
        after_path.write_text(json.dumps({"tasks": after}), encoding="utf-8")
        verify_args = type("Args", (), {"live": str(after_path), "plan": str(plan_path)})
        result = scheduler._command_verify_predelete(verify_args, workspace)
        self.assertTrue(result["ok"], result)

    def test_hook_uses_payload_cwd_and_fails_visible_on_bad_state(self):
        workspace = self.make_workspace()
        schedule = self.persist(workspace)
        payload = json.dumps({"cwd": str(workspace), "source": "startup"})
        output = scheduler.hook_notice("SessionStart", payload)
        text = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn(scheduler.schedule_fingerprint(schedule), text)
        self.assertIn("/freestyle-beats reconcile", text)

        scheduler.schedule_path(workspace).write_text("{bad", encoding="utf-8")
        error_output = scheduler.hook_notice("SessionStart", payload)
        error_text = error_output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("ERROR", error_text)
        self.assertIn("Do not create or delete", error_text)

    def test_cli_uses_project_env(self):
        workspace = self.make_workspace()
        self.persist(workspace)
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(workspace))
        result = subprocess.run(
            [sys.executable, str(MODULE_PATH), "validate"],
            cwd=str(PACKAGE),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_show_redacts_ownership_key_but_emits_signed_runtime_tasks(self):
        workspace = self.make_workspace()
        schedule = self.persist(workspace)
        shown = scheduler._command_show(workspace)
        self.assertEqual("<redacted>", shown["schedule"]["ownership_key"])
        self.assertNotIn(schedule["ownership_key"], json.dumps(shown))
        self.assertTrue(
            all(scheduler.parse_marker(task["prompt"], schedule) for task in shown["runtime_tasks"])
        )

    def test_hook_missing_cwd_does_not_fall_back_to_environment(self):
        workspace = self.make_workspace()
        self.persist(workspace)
        old = os.environ.get("CLAUDE_PROJECT_DIR")
        os.environ["CLAUDE_PROJECT_DIR"] = str(workspace)
        try:
            output = scheduler.hook_notice("SessionStart", json.dumps({"source": "startup"}))
        finally:
            if old is None:
                os.environ.pop("CLAUDE_PROJECT_DIR", None)
            else:
                os.environ["CLAUDE_PROJECT_DIR"] = old
        text = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("ERROR", text)
        self.assertIn("missing required cwd", text)
        self.assertNotIn(scheduler.schedule_fingerprint(scheduler.load_schedule(workspace)), text)

    def test_candidate_and_live_paths_must_stay_in_state_directory(self):
        workspace = self.make_workspace()
        outside = workspace / "outside.json"
        outside.write_text(json.dumps(candidate()), encoding="utf-8")
        with self.assertRaisesRegex(scheduler.ScheduleError, "must stay under"):
            scheduler.contained_state_input(workspace, str(outside), "candidate")

    def test_candidate_loader_accepts_utf8_bom(self):
        workspace = self.make_workspace()
        path = scheduler.schedule_path(workspace).parent / "candidate.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(candidate()), encoding="utf-8-sig")
        loaded = scheduler._load_candidate(workspace, str(path))
        self.assertEqual(2, loaded["schema_version"])

    def test_symlinked_claude_directory_is_rejected_when_supported(self):
        workspace = self.make_workspace()
        target = workspace / "real-claude"
        target.mkdir()
        try:
            os.symlink(target, workspace / ".claude", target_is_directory=True)
        except (OSError, NotImplementedError) as exc:
            self.skipTest(f"symlink creation unavailable: {exc}")
        with self.assertRaisesRegex(scheduler.ScheduleError, "symlink/reparse"):
            scheduler.schedule_path(workspace)


if __name__ == "__main__":
    unittest.main(verbosity=2)
