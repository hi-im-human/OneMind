#!/usr/bin/env python3
"""Persist and reconcile one workspace-local Freestyle Beats schedule.

This module owns durable schedule state only. Claude Code's CronList,
CronCreate, and CronDelete tools remain the only supported interface to the
runtime task registry; this package does not read or edit Claude Code's
undocumented internal task files.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import secrets
import stat
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence


SCHEMA_VERSION = 2
STATE_RELATIVE_PATH = Path(".claude") / "freestyle-beats" / "schedule.json"
DEFAULT_MAINTENANCE_CRON = "17 4 * * *"
MAINTENANCE_ID = "maintenance"
CRON_TASK_LIMIT = 50
REFRESH_AFTER = timedelta(days=5)
MAX_USER_ENTRIES = 8
MIN_USER_ENTRIES = 2
MAX_PROMPT_CHARS = 2000
ENTRY_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
MARKER_RE = re.compile(
    r"^\[fb1:(?P<instance>[0-9a-f]{12}):(?P<token>[0-9a-f]{8}):"
    r"(?P<digest>[0-9a-f]{12}):(?P<signature>[0-9a-f]{20})\](?:\s|$)"
)
CRON_BOUNDS = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7))


class ScheduleError(ValueError):
    """Raised when state, paths, or normalized runtime data are invalid."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_utc_timestamp(value: Any, where: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ScheduleError(f"{where} must be a non-empty UTC timestamp string")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ScheduleError(f"{where} is not a valid ISO-8601 timestamp: {value}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise ScheduleError(f"{where} must be timezone-aware UTC: {value}")
    return parsed.astimezone(timezone.utc)


def _is_reparse_or_symlink(path: Path) -> bool:
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return False
    file_attributes = getattr(info, "st_file_attributes", 0)
    return stat.S_ISLNK(info.st_mode) or bool(file_attributes & 0x400)


def reject_reparse_components(workspace: Path, target: Path) -> None:
    root = workspace.resolve()
    try:
        relative = target.absolute().relative_to(root)
    except ValueError as exc:
        raise ScheduleError(f"path escapes workspace: {target}") from exc
    current = root
    for part in relative.parts:
        current = current / part
        if _is_reparse_or_symlink(current):
            raise ScheduleError(f"path component must not be a symlink/reparse point: {current}")


def _json_dump(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def resolve_workspace(
    explicit: Optional[str] = None,
    payload: Optional[Mapping[str, Any]] = None,
) -> Path:
    """Resolve a real workspace from an explicit path, hook payload, or env.

    WHY (2026-08-17): package cwd is not a workspace identity. Claude's hook
    payload and CLAUDE_PROJECT_DIR are runtime-provided sources that do not
    silently drift to the package installation directory.
    """

    candidate: Optional[str] = explicit
    if candidate is None and payload is not None:
        payload_cwd = payload.get("cwd")
        if isinstance(payload_cwd, str) and payload_cwd.strip():
            candidate = payload_cwd
    if candidate is None:
        env_path = os.environ.get("CLAUDE_PROJECT_DIR")
        if env_path and env_path.strip():
            candidate = env_path
    if candidate is None:
        raise ScheduleError(
            "workspace unavailable: pass --workspace or provide hook payload cwd/"
            "CLAUDE_PROJECT_DIR"
        )

    workspace = Path(candidate).expanduser()
    if not workspace.is_absolute():
        raise ScheduleError(f"workspace must be absolute: {candidate}")
    if not workspace.exists() or not workspace.is_dir():
        raise ScheduleError(f"workspace does not exist or is not a directory: {workspace}")
    return workspace.resolve()


def schedule_path(workspace: Path) -> Path:
    root = workspace.resolve()
    path = root / STATE_RELATIVE_PATH
    reject_reparse_components(root, path)
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ScheduleError(f"schedule path escapes workspace: {resolved}") from exc
    return path


def _validate_exact_keys(
    value: Mapping[str, Any],
    allowed: Iterable[str],
    required: Iterable[str],
    where: str,
) -> None:
    allowed_set = set(allowed)
    required_set = set(required)
    unknown = sorted(set(value) - allowed_set)
    missing = sorted(required_set - set(value))
    if unknown:
        raise ScheduleError(f"{where} contains unknown keys: {', '.join(unknown)}")
    if missing:
        raise ScheduleError(f"{where} is missing keys: {', '.join(missing)}")


def _parse_cron_atom(atom: str, low: int, high: int, where: str) -> None:
    base = atom
    if "/" in atom:
        if atom.count("/") != 1:
            raise ScheduleError(f"{where} has invalid step syntax: {atom}")
        base, step_text = atom.split("/", 1)
        if not step_text.isdigit() or int(step_text) <= 0:
            raise ScheduleError(f"{where} has invalid step: {atom}")
        if int(step_text) > (high - low + 1):
            raise ScheduleError(f"{where} step exceeds field span: {atom}")
        if base != "*" and "-" not in base:
            raise ScheduleError(
                f"{where} step requires '*' or an explicit range: {atom}"
            )

    if base == "*":
        return
    if "-" in base:
        if base.count("-") != 1:
            raise ScheduleError(f"{where} has invalid range: {atom}")
        start_text, end_text = base.split("-", 1)
        if not start_text.isdigit() or not end_text.isdigit():
            raise ScheduleError(f"{where} has non-numeric range: {atom}")
        start, end = int(start_text), int(end_text)
        if start < low or end > high or start > end:
            raise ScheduleError(f"{where} range is outside {low}-{high}: {atom}")
        return
    if not base.isdigit():
        raise ScheduleError(f"{where} has unsupported syntax: {atom}")
    number = int(base)
    if number < low or number > high:
        raise ScheduleError(f"{where} value is outside {low}-{high}: {number}")


def validate_cron(expression: Any, where: str = "cron") -> str:
    if not isinstance(expression, str):
        raise ScheduleError(f"{where} must be a string")
    fields = expression.split()
    if len(fields) != 5:
        raise ScheduleError(f"{where} must contain exactly five fields")
    for index, (field, bounds) in enumerate(zip(fields, CRON_BOUNDS), start=1):
        if not field or re.search(r"[^0-9*/,-]", field):
            raise ScheduleError(f"{where} field {index} has unsupported characters: {field}")
        for atom in field.split(","):
            if not atom:
                raise ScheduleError(f"{where} field {index} contains an empty list item")
            _parse_cron_atom(atom, bounds[0], bounds[1], f"{where} field {index}")
    return " ".join(fields)


def _validate_entry(raw: Any, index: int) -> Dict[str, Any]:
    where = f"entries[{index}]"
    if not isinstance(raw, Mapping):
        raise ScheduleError(f"{where} must be an object")
    _validate_exact_keys(
        raw,
        allowed=("id", "label", "cron", "prompt", "enabled"),
        required=("id", "label", "cron", "prompt"),
        where=where,
    )

    entry_id = raw["id"]
    if not isinstance(entry_id, str) or not ENTRY_ID_RE.fullmatch(entry_id):
        raise ScheduleError(
            f"{where}.id must match {ENTRY_ID_RE.pattern}: {entry_id!r}"
        )
    if entry_id == MAINTENANCE_ID:
        raise ScheduleError(f"{where}.id is reserved: {MAINTENANCE_ID}")

    label = raw["label"]
    if label not in ("work", "personal"):
        raise ScheduleError(f"{where}.label must be 'work' or 'personal'")

    prompt = raw["prompt"]
    if not isinstance(prompt, str) or not prompt.strip():
        raise ScheduleError(f"{where}.prompt must be a non-empty string")
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ScheduleError(
            f"{where}.prompt exceeds {MAX_PROMPT_CHARS} characters: {len(prompt)}"
        )
    if prompt.lstrip().startswith("/"):
        raise ScheduleError(
            f"{where}.prompt must be literal task text, not a skill invocation"
        )
    if "[freestyle-beats:" in prompt or "[fb1:" in prompt:
        raise ScheduleError(f"{where}.prompt contains the reserved package marker")

    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ScheduleError(f"{where}.enabled must be boolean")

    return {
        "id": entry_id,
        "label": label,
        "cron": validate_cron(raw["cron"], f"{where}.cron"),
        "prompt": prompt,
        "enabled": enabled,
    }


def _validate_entries(raw_entries: Any) -> List[Dict[str, Any]]:
    if not isinstance(raw_entries, list):
        raise ScheduleError("entries must be an array")
    if not MIN_USER_ENTRIES <= len(raw_entries) <= MAX_USER_ENTRIES:
        raise ScheduleError(
            f"entries must contain {MIN_USER_ENTRIES}-{MAX_USER_ENTRIES} user beats"
        )
    entries = [_validate_entry(raw, index) for index, raw in enumerate(raw_entries)]
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        raise ScheduleError("entries contain duplicate ids")
    semantic_keys = [(entry["cron"], entry["prompt"]) for entry in entries]
    if len(semantic_keys) != len(set(semantic_keys)):
        raise ScheduleError("entries contain duplicate cron + prompt pairs")
    enabled_count = sum(1 for entry in entries if entry["enabled"])
    if enabled_count < MIN_USER_ENTRIES:
        raise ScheduleError(
            f"entries must contain at least {MIN_USER_ENTRIES} enabled user beats"
        )
    return entries


def schedule_from_candidate(candidate: Any, previous: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    if not isinstance(candidate, Mapping):
        raise ScheduleError("candidate schedule must be an object")
    _validate_exact_keys(
        candidate,
        allowed=("schema_version", "timezone", "maintenance_cron", "entries"),
        required=("timezone", "entries"),
        where="candidate schedule",
    )
    if candidate.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
        raise ScheduleError(f"candidate schema_version must equal {SCHEMA_VERSION}")
    if candidate["timezone"] != "local":
        raise ScheduleError(
            "timezone must be 'local'; Claude Code interprets cron expressions in local time"
        )

    now = utc_now()
    created_at = previous.get("created_at", now) if previous else now
    instance_id = previous.get("instance_id") if previous else secrets.token_hex(6)
    ownership_key = previous.get("ownership_key") if previous else secrets.token_hex(32)
    return {
        "schema_version": SCHEMA_VERSION,
        "instance_id": instance_id,
        "ownership_key": ownership_key,
        "timezone": "local",
        "maintenance_cron": validate_cron(
            candidate.get("maintenance_cron", DEFAULT_MAINTENANCE_CRON),
            "maintenance_cron",
        ),
        "created_at": created_at,
        "updated_at": now,
        # WHY (2026-08-17): replacement changes the canonical schedule. A
        # verification timestamp for the prior contents must not survive as a
        # receipt for the replacement.
        "last_reconciled_at": None,
        "last_refreshed_at": None,
        "entries": _validate_entries(candidate["entries"]),
    }


def validate_schedule(raw: Any) -> Dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ScheduleError("schedule must be an object")
    _validate_exact_keys(
        raw,
        allowed=(
            "schema_version",
            "instance_id",
            "ownership_key",
            "timezone",
            "maintenance_cron",
            "created_at",
            "updated_at",
            "last_reconciled_at",
            "last_refreshed_at",
            "entries",
        ),
        required=(
            "schema_version",
            "instance_id",
            "ownership_key",
            "timezone",
            "maintenance_cron",
            "created_at",
            "updated_at",
            "last_reconciled_at",
            "last_refreshed_at",
            "entries",
        ),
        where="schedule",
    )
    if raw["schema_version"] != SCHEMA_VERSION:
        raise ScheduleError(
            f"unsupported schema_version {raw['schema_version']!r}; expected {SCHEMA_VERSION}"
        )
    if raw["timezone"] != "local":
        raise ScheduleError("schedule.timezone must be 'local'")
    if not isinstance(raw["instance_id"], str) or not re.fullmatch(
        r"[0-9a-f]{12}", raw["instance_id"]
    ):
        raise ScheduleError("schedule.instance_id must be 12 lowercase hex characters")
    if not isinstance(raw["ownership_key"], str) or not re.fullmatch(
        r"[0-9a-f]{64}", raw["ownership_key"]
    ):
        raise ScheduleError("schedule.ownership_key must be 64 lowercase hex characters")

    created_at = parse_utc_timestamp(raw["created_at"], "schedule.created_at")
    updated_at = parse_utc_timestamp(raw["updated_at"], "schedule.updated_at")
    if updated_at < created_at:
        raise ScheduleError("schedule.updated_at must not precede created_at")
    for field in ("last_reconciled_at", "last_refreshed_at"):
        if raw[field] is not None:
            receipt = parse_utc_timestamp(raw[field], f"schedule.{field}")
            if receipt < created_at or receipt > updated_at:
                raise ScheduleError(
                    f"schedule.{field} must fall between created_at and updated_at"
                )
    return {
        "schema_version": SCHEMA_VERSION,
        "instance_id": raw["instance_id"],
        "ownership_key": raw["ownership_key"],
        "timezone": "local",
        "maintenance_cron": validate_cron(raw["maintenance_cron"], "maintenance_cron"),
        "created_at": raw["created_at"],
        "updated_at": raw["updated_at"],
        "last_reconciled_at": raw["last_reconciled_at"],
        "last_refreshed_at": raw["last_refreshed_at"],
        "entries": _validate_entries(raw["entries"]),
    }


def load_json_file(path: Path) -> Any:
    try:
        # utf-8-sig accepts ordinary UTF-8 and PowerShell-generated UTF-8 BOM files.
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError as exc:
        raise ScheduleError(f"file does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ScheduleError(
            f"invalid JSON in {path}: line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc


def contained_state_input(workspace: Path, path_text: str, purpose: str) -> Path:
    candidate = Path(path_text).expanduser()
    if not candidate.is_absolute():
        raise ScheduleError(f"{purpose} path must be absolute: {candidate}")
    state_dir = schedule_path(workspace).parent
    reject_reparse_components(workspace, candidate)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(state_dir.resolve(strict=False))
    except ValueError as exc:
        raise ScheduleError(
            f"{purpose} path must stay under {state_dir}: {resolved}"
        ) from exc
    if not resolved.exists() or not resolved.is_file():
        raise ScheduleError(f"{purpose} file does not exist: {resolved}")
    if _is_reparse_or_symlink(candidate):
        raise ScheduleError(f"{purpose} file must not be a symlink/reparse point: {candidate}")
    return candidate


def contained_state_output(workspace: Path, path_text: str, purpose: str) -> Path:
    candidate = Path(path_text).expanduser()
    if not candidate.is_absolute():
        raise ScheduleError(f"{purpose} path must be absolute: {candidate}")
    state_dir = schedule_path(workspace).parent
    reject_reparse_components(workspace, candidate)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(state_dir.resolve(strict=False))
    except ValueError as exc:
        raise ScheduleError(
            f"{purpose} path must stay under {state_dir}: {resolved}"
        ) from exc
    if candidate.exists() and (
        not candidate.is_file() or _is_reparse_or_symlink(candidate)
    ):
        raise ScheduleError(
            f"{purpose} path must be a regular non-reparse file: {candidate}"
        )
    return candidate


def atomic_write_json(workspace: Path, path: Path, data: Any) -> None:
    path = contained_state_output(workspace, str(path), "JSON output")
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    reject_reparse_components(workspace, path)
    temp_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix=f"{path.stem}.",
            suffix=".tmp",
            dir=str(parent),
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(_json_dump(data))
            handle.flush()
            os.fsync(handle.fileno())
        reject_reparse_components(workspace, path)
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink()
            except FileNotFoundError:
                pass


def load_schedule(workspace: Path) -> Dict[str, Any]:
    path = schedule_path(workspace)
    if path.exists() and (not path.is_file() or path.is_symlink()):
        raise ScheduleError(f"schedule path must be a regular non-symlink file: {path}")
    return validate_schedule(load_json_file(path))


def atomic_write_schedule(workspace: Path, schedule: Mapping[str, Any]) -> Path:
    validated = validate_schedule(schedule)
    path = schedule_path(workspace)
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    reject_reparse_components(workspace, path)
    try:
        parent.resolve().relative_to(workspace.resolve())
    except ValueError as exc:
        raise ScheduleError(f"schedule directory escapes workspace: {parent}") from exc

    temp_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            prefix="schedule.",
            suffix=".tmp",
            dir=str(parent),
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(_json_dump(validated))
            handle.flush()
            os.fsync(handle.fileno())
        # Recheck immediately before replacement. Python's cross-platform API
        # cannot make the full path walk and replace one atomic no-follow
        # operation, so this minimizes the local TOCTOU window.
        reject_reparse_components(workspace, path)
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink()
            except FileNotFoundError:
                pass
    return path


def entry_token(schedule: Mapping[str, Any], entry_id: str, label: str) -> str:
    key = bytes.fromhex(schedule["ownership_key"])
    message = f"entry|{entry_id}|{label}".encode("utf-8")
    return hmac.new(key, message, hashlib.sha256).hexdigest()[:8]


def payload_digest(
    entry_id: str, label: str, kind: str, cron: str, base_prompt: str
) -> str:
    payload = json.dumps(
        {
            "entry_id": entry_id,
            "label": label,
            "kind": kind,
            "cron": cron,
            "prompt": base_prompt,
            "recurring": True,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:12]


def marker_signature(
    schedule: Mapping[str, Any], token: str, digest: str
) -> str:
    message = f"fb1|{schedule['instance_id']}|{token}|{digest}".encode("utf-8")
    key = bytes.fromhex(schedule["ownership_key"])
    return hmac.new(key, message, hashlib.sha256).hexdigest()[:20]


def marker(
    schedule: Mapping[str, Any], entry_id: str, label: str, digest: str
) -> str:
    token = entry_token(schedule, entry_id, label)
    signature = marker_signature(schedule, token, digest)
    value = f"[fb1:{schedule['instance_id']}:{token}:{digest}:{signature}]"
    if len(value) > 70:  # Keep the complete marker inside CronList's visible preview.
        raise ScheduleError(f"ownership marker exceeds visible-prefix budget: {len(value)}")
    return value


def build_runtime_task(
    schedule: Mapping[str, Any],
    entry_id: str,
    label: str,
    kind: str,
    cron: str,
    base_prompt: str,
) -> Dict[str, Any]:
    digest = payload_digest(entry_id, label, kind, cron, base_prompt)
    token = entry_token(schedule, entry_id, label)
    prefix = marker(schedule, entry_id, label, digest)
    return {
        "entry_id": entry_id,
        "label": label,
        "kind": kind,
        "cron": cron,
        "prompt": f"{prefix} {base_prompt}",
        "recurring": True,
        "marker_token": token,
        "payload_digest": digest,
    }


def maintenance_task(schedule: Mapping[str, Any]) -> Dict[str, Any]:
    return build_runtime_task(
        schedule,
        MAINTENANCE_ID,
        "maintenance",
        "maintenance",
        schedule["maintenance_cron"],
        "Run the /freestyle-beats skill with argument maintain now.",
    )


def expected_tasks(schedule: Mapping[str, Any]) -> List[Dict[str, Any]]:
    tasks: List[Dict[str, Any]] = []
    for entry in schedule["entries"]:
        if not entry["enabled"]:
            continue
        tasks.append(
            build_runtime_task(
                schedule,
                entry["id"],
                entry["label"],
                "beat",
                entry["cron"],
                entry["prompt"],
            )
        )
    tasks.append(maintenance_task(schedule))
    return tasks


def _normalize_live_task(raw: Any, index: int) -> Dict[str, Any]:
    where = f"live tasks[{index}]"
    if not isinstance(raw, Mapping):
        raise ScheduleError(f"{where} must be an object")
    task_id = raw.get("id")
    if not isinstance(task_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{8}", task_id):
        raise ScheduleError(f"{where}.id must be exactly 8 identifier characters")
    prompt = raw.get("prompt")
    if not isinstance(prompt, str):
        raise ScheduleError(f"{where}.prompt must be a string")
    recurring = raw.get("recurring")
    if not isinstance(recurring, bool):
        raise ScheduleError(f"{where}.recurring must be boolean")
    return {
        "id": task_id,
        "prompt": prompt,
        "recurring": recurring,
    }


def normalize_live_tasks(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, Mapping):
        _validate_exact_keys(raw, allowed=("tasks",), required=("tasks",), where="live data")
        raw = raw["tasks"]
    if not isinstance(raw, list):
        raise ScheduleError("live data must be an array or an object containing tasks[]")
    tasks = [_normalize_live_task(task, index) for index, task in enumerate(raw)]
    ids = [task["id"] for task in tasks]
    if len(ids) != len(set(ids)):
        raise ScheduleError("live data contains duplicate runtime task ids")
    return tasks


def parse_marker(
    prompt: str, schedule: Mapping[str, Any]
) -> Optional[Dict[str, str]]:
    match = MARKER_RE.match(prompt)
    if not match:
        if prompt.startswith("[fb1:"):
            raise ScheduleError("live task begins with a truncated or malformed [fb1:] marker")
        return None
    if match.group("instance") != schedule["instance_id"]:
        return None
    token = match.group("token")
    digest = match.group("digest")
    expected = marker_signature(schedule, token, digest)
    if not hmac.compare_digest(match.group("signature"), expected):
        return None
    return {"token": token, "digest": digest}


def _is_exact(
    live: Mapping[str, Any], parsed: Mapping[str, str], expected: Mapping[str, Any]
) -> bool:
    return (
        parsed["token"] == expected["marker_token"]
        and parsed["digest"] == expected["payload_digest"]
        and live["recurring"] is True
    )


def plan_actions(
    schedule: Mapping[str, Any],
    live_tasks: Sequence[Mapping[str, Any]],
    refresh: bool = False,
) -> Dict[str, Any]:
    expected = {task["entry_id"]: task for task in expected_tasks(schedule)}
    expected_tokens = {task["marker_token"]: task for task in expected.values()}
    managed: Dict[str, List[Dict[str, Any]]] = {}
    foreign_count = 0
    for task in live_tasks:
        parsed = parse_marker(task["prompt"], schedule)
        if parsed is None:
            foreign_count += 1
            continue
        classified = dict(task)
        classified["_marker_digest"] = parsed["digest"]
        managed.setdefault(parsed["token"], []).append(classified)

    deletes: List[Dict[str, Any]] = []
    creates: List[Dict[str, Any]] = []
    keeps: List[Dict[str, Any]] = []

    for token, tasks in sorted(managed.items()):
        if token in expected_tokens:
            continue
        for task in sorted(tasks, key=lambda item: item["id"]):
            deletes.append(
                {
                    "action": "delete",
                    "cron_id": task["id"],
                    "entry_id": f"unknown-token:{token}",
                    "reason": "orphaned package task",
                }
            )

    for entry_id, wanted in sorted(expected.items()):
        token = wanted["marker_token"]
        current = sorted(managed.get(token, []), key=lambda item: item["id"])
        exact = [
            task
            for task in current
            if _is_exact(
                task,
                {"token": token, "digest": task["_marker_digest"]},
                wanted,
            )
        ]
        drift = [task for task in current if task not in exact]

        if refresh:
            creates.append(
                {
                    "action": "create",
                    **wanted,
                    "reason": "pre-expiry refresh",
                    "required_post_create_exact_count": len(exact) + 1,
                }
            )
            for task in current:
                deletes.append(
                    {
                        "action": "delete",
                        "cron_id": task["id"],
                        "entry_id": entry_id,
                        "reason": "pre-expiry refresh",
                    }
                )
            continue

        if exact:
            keeps.append(
                {
                    "action": "keep",
                    "cron_id": exact[0]["id"],
                    "entry_id": entry_id,
                    "reason": "exact canonical match",
                }
            )
            for duplicate in exact[1:]:
                deletes.append(
                    {
                        "action": "delete",
                        "cron_id": duplicate["id"],
                        "entry_id": entry_id,
                        "reason": "exact duplicate",
                    }
                )
        else:
            creates.append(
                {
                    "action": "create",
                    **wanted,
                    "reason": "missing canonical task",
                    "required_post_create_exact_count": 1,
                }
            )
        for task in drift:
            deletes.append(
                {
                    "action": "delete",
                    "cron_id": task["id"],
                    "entry_id": entry_id,
                    "reason": "managed task drift",
                }
            )

    projected_peak = len(live_tasks) + len(creates)
    blocked = projected_peak > CRON_TASK_LIMIT
    return {
        "mode": "refresh" if refresh else "reconcile",
        "ok": not blocked,
        "blocked": blocked,
        "schedule_fingerprint": schedule_fingerprint(schedule),
        "block_reason": (
            f"create-first replacement would peak at {projected_peak} tasks, above "
            f"Claude Code's {CRON_TASK_LIMIT}-task limit"
            if blocked
            else None
        ),
        "expected_task_count": len(expected),
        "foreign_task_count": foreign_count,
        "live_task_count": len(live_tasks),
        "projected_peak_task_count": projected_peak,
        "actions": [] if blocked else creates + deletes,
        "create_actions": [] if blocked else creates,
        "delete_actions": [] if blocked else deletes,
        "kept": keeps,
    }


def verify_live_state(
    schedule: Mapping[str, Any], live_tasks: Sequence[Mapping[str, Any]]
) -> Dict[str, Any]:
    expected = {task["entry_id"]: task for task in expected_tasks(schedule)}
    expected_tokens = {task["marker_token"]: task for task in expected.values()}
    managed: Dict[str, List[Dict[str, Any]]] = {}
    for task in live_tasks:
        parsed = parse_marker(task["prompt"], schedule)
        if parsed is not None:
            classified = dict(task)
            classified["_marker_digest"] = parsed["digest"]
            managed.setdefault(parsed["token"], []).append(classified)

    problems: List[str] = []
    for token in sorted(set(managed) - set(expected_tokens)):
        problems.append(f"orphaned package task token: {token}")
    for entry_id, wanted in sorted(expected.items()):
        token = wanted["marker_token"]
        current = managed.get(token, [])
        exact = [
            task
            for task in current
            if _is_exact(
                task,
                {"token": token, "digest": task["_marker_digest"]},
                wanted,
            )
        ]
        if len(exact) != 1:
            problems.append(
                f"{entry_id}: expected one exact task, found {len(exact)}"
            )
        if len(current) != len(exact):
            problems.append(f"{entry_id}: found {len(current) - len(exact)} drifted task(s)")
    return {
        "ok": not problems,
        "expected_task_count": len(expected),
        "managed_task_count": sum(len(tasks) for tasks in managed.values()),
        "problems": problems,
    }


def verify_predelete(
    schedule: Mapping[str, Any],
    live_tasks: Sequence[Mapping[str, Any]],
    plan: Mapping[str, Any],
) -> Dict[str, Any]:
    fingerprint = schedule_fingerprint(schedule)
    if plan.get("blocked") or not plan.get("ok", True):
        return {
            "ok": False,
            "problems": ["plan is blocked or invalid"],
            "schedule_fingerprint": fingerprint,
        }
    if plan.get("schedule_fingerprint") != fingerprint:
        return {
            "ok": False,
            "problems": ["plan schedule fingerprint does not match current state"],
            "schedule_fingerprint": fingerprint,
        }

    expected = {task["entry_id"]: task for task in expected_tasks(schedule)}
    managed: Dict[str, List[Dict[str, Any]]] = {}
    for task in live_tasks:
        parsed = parse_marker(task["prompt"], schedule)
        if parsed is not None:
            classified = dict(task)
            classified["_marker_digest"] = parsed["digest"]
            managed.setdefault(parsed["token"], []).append(classified)

    problems: List[str] = []
    exact_counts: Dict[str, int] = {}
    for entry_id, wanted in expected.items():
        token = wanted["marker_token"]
        current = managed.get(token, [])
        count = len(
            [
                task
                for task in current
                if _is_exact(
                    task,
                    {"token": token, "digest": task["_marker_digest"]},
                    wanted,
                )
            ]
        )
        exact_counts[entry_id] = count
        if count < 1:
            problems.append(f"{entry_id}: no exact canonical task exists before delete phase")

    creates = plan.get("create_actions")
    if not isinstance(creates, list):
        problems.append("plan create_actions is missing or invalid")
        creates = []
    for index, action in enumerate(creates):
        if not isinstance(action, Mapping):
            problems.append(f"plan create_actions[{index}] is invalid")
            continue
        entry_id = action.get("entry_id")
        required = action.get("required_post_create_exact_count")
        if entry_id not in expected or not isinstance(required, int) or required < 1:
            problems.append(f"plan create_actions[{index}] has invalid verification fields")
            continue
        actual = exact_counts.get(entry_id, 0)
        if actual < required:
            problems.append(
                f"{entry_id}: expected at least {required} exact task(s) after create, found {actual}"
            )
    return {
        "ok": not problems,
        "problems": problems,
        "schedule_fingerprint": fingerprint,
        "exact_counts": exact_counts,
    }


def plan_uninstall(
    schedule: Mapping[str, Any], live_tasks: Sequence[Mapping[str, Any]]
) -> Dict[str, Any]:
    token_to_entry = {
        task["marker_token"]: task["entry_id"] for task in expected_tasks(schedule)
    }
    deletes: List[Dict[str, Any]] = []
    foreign_count = 0
    for task in live_tasks:
        parsed = parse_marker(task["prompt"], schedule)
        if parsed is None:
            foreign_count += 1
            continue
        deletes.append(
            {
                "action": "delete",
                "cron_id": task["id"],
                "entry_id": token_to_entry.get(
                    parsed["token"], f"unknown-token:{parsed['token']}"
                ),
                "reason": "uninstall instance-owned task",
            }
        )
    deletes.sort(key=lambda item: (item["entry_id"], item["cron_id"]))
    return {
        "ok": True,
        "blocked": False,
        "schedule_fingerprint": schedule_fingerprint(schedule),
        "delete_actions": deletes,
        "owned_task_count": len(deletes),
        "foreign_task_count": foreign_count,
    }


def schedule_fingerprint(schedule: Mapping[str, Any]) -> str:
    canonical = json.dumps(
        {
            "schema_version": schedule["schema_version"],
            "instance_id": schedule["instance_id"],
            "timezone": schedule["timezone"],
            "maintenance_cron": schedule["maintenance_cron"],
            "entries": schedule["entries"],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()[:12]


def maintenance_mode(
    schedule: Mapping[str, Any], now: Optional[datetime] = None
) -> Dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ScheduleError("maintenance comparison time must be timezone-aware")
    current = current.astimezone(timezone.utc)
    receipt_text = schedule.get("last_refreshed_at")
    if receipt_text is None:
        return {
            "mode": "refresh",
            "reason": "no successful refresh receipt exists",
            "age_seconds": None,
        }
    refreshed = parse_utc_timestamp(receipt_text, "schedule.last_refreshed_at")
    age = current - refreshed
    if age < timedelta(0):
        raise ScheduleError("last_refreshed_at is in the future")
    return {
        "mode": "refresh" if age >= REFRESH_AFTER else "reconcile",
        "reason": (
            "refresh receipt is at least five days old"
            if age >= REFRESH_AFTER
            else "refresh receipt is less than five days old"
        ),
        "age_seconds": int(age.total_seconds()),
    }


def hook_notice(event: str, raw_stdin: str) -> Dict[str, Any]:
    try:
        payload = json.loads(raw_stdin) if raw_stdin.strip() else {}
        if not isinstance(payload, Mapping):
            raise ScheduleError("hook input must be a JSON object")
        payload_cwd = payload.get("cwd")
        if not isinstance(payload_cwd, str) or not payload_cwd.strip():
            raise ScheduleError("hook input is missing required cwd")
        # WHY (2026-08-17): hook payload and process environment can disagree.
        # A hook must fail closed on its own event data instead of loading a
        # different project's state from CLAUDE_PROJECT_DIR.
        workspace = resolve_workspace(explicit=payload_cwd)
        path = schedule_path(workspace)
        if not path.exists():
            notice = (
                "## Freestyle Beats\n"
                f"No persisted personal schedule exists at `{path}`. Run "
                "`/freestyle-beats setup` to create one before registering beats."
            )
        else:
            schedule = load_schedule(workspace)
            enabled = sum(1 for entry in schedule["entries"] if entry["enabled"])
            source = payload.get("source", "unknown")
            lead = (
                "Context compacted; live cron survival is indeterminate."
                if event == "PostCompact"
                else f"Session event received (source: {source})."
            )
            notice = (
                "## Freestyle Beats\n"
                f"{lead} Persisted personal schedule `{schedule_fingerprint(schedule)}` "
                f"contains {enabled} enabled beat(s) plus maintenance at `{path}`. "
                "Run `/freestyle-beats reconcile` now: load that file, call CronList, "
                "and create/delete only the package-owned differences. Do not derive "
                "a replacement schedule from the goal files."
            )
    except Exception as exc:
        notice = (
            "## Freestyle Beats — ERROR\n"
            f"The persisted schedule could not be loaded: {exc}. Do not create or "
            "delete cron tasks until the state path or file is repaired."
        )

    # WHY (2026-08-17): the registered PostCompact command still emits the
    # SessionStart output event because the observed validator drops a literal
    # PostCompact hookSpecificOutput payload. The registration event remains
    # distinct; only the output schema uses this compatibility value.
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": notice,
        }
    }


def emit_hook_notice(event: str) -> None:
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""
    print(json.dumps(hook_notice(event, raw), ensure_ascii=False))


def _load_candidate(workspace: Path, path_text: str) -> Any:
    if path_text == "-":
        try:
            return json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            raise ScheduleError(
                f"invalid JSON on stdin: line {exc.lineno}, column {exc.colno}: {exc.msg}"
            ) from exc
    return load_json_file(contained_state_input(workspace, path_text, "candidate"))


def _command_create(args: argparse.Namespace, workspace: Path) -> Dict[str, Any]:
    path = schedule_path(workspace)
    previous: Optional[Dict[str, Any]] = None
    if path.exists():
        if not args.replace:
            raise ScheduleError(
                f"schedule already exists: {path}; use --replace for an explicit update"
            )
        previous = load_schedule(workspace)
    schedule = schedule_from_candidate(
        _load_candidate(workspace, args.input), previous=previous
    )
    atomic_write_schedule(workspace, schedule)
    return {
        "ok": True,
        "path": str(path),
        "fingerprint": schedule_fingerprint(schedule),
        "entries": len(schedule["entries"]),
        "replaced": previous is not None,
    }


def _command_show(workspace: Path) -> Dict[str, Any]:
    schedule = load_schedule(workspace)
    visible_schedule = dict(schedule)
    visible_schedule["ownership_key"] = "<redacted>"
    return {
        "path": str(schedule_path(workspace)),
        "fingerprint": schedule_fingerprint(schedule),
        "schedule": visible_schedule,
        "runtime_tasks": expected_tasks(schedule),
    }


def _command_validate(workspace: Path) -> Dict[str, Any]:
    schedule = load_schedule(workspace)
    return {
        "ok": True,
        "path": str(schedule_path(workspace)),
        "fingerprint": schedule_fingerprint(schedule),
        "entries": len(schedule["entries"]),
    }


def _command_maintain(workspace: Path) -> Dict[str, Any]:
    schedule = load_schedule(workspace)
    result = maintenance_mode(schedule)
    result["ok"] = True
    result["schedule_fingerprint"] = schedule_fingerprint(schedule)
    return result


def _command_plan(args: argparse.Namespace, workspace: Path) -> Dict[str, Any]:
    schedule = load_schedule(workspace)
    live = normalize_live_tasks(
        load_json_file(contained_state_input(workspace, args.live, "live cron data"))
    )
    result = plan_actions(schedule, live, refresh=args.refresh)
    if args.output:
        output = contained_state_output(workspace, args.output, "plan output")
        atomic_write_json(workspace, output, result)
        result["plan_path"] = str(output)
    return result


def _command_verify_predelete(
    args: argparse.Namespace, workspace: Path
) -> Dict[str, Any]:
    schedule = load_schedule(workspace)
    live = normalize_live_tasks(
        load_json_file(contained_state_input(workspace, args.live, "post-create cron data"))
    )
    plan = load_json_file(contained_state_input(workspace, args.plan, "reconciliation plan"))
    if not isinstance(plan, Mapping):
        raise ScheduleError("reconciliation plan must be a JSON object")
    return verify_predelete(schedule, live, plan)


def _command_uninstall_plan(args: argparse.Namespace, workspace: Path) -> Dict[str, Any]:
    schedule = load_schedule(workspace)
    live = normalize_live_tasks(
        load_json_file(contained_state_input(workspace, args.live, "live cron data"))
    )
    return plan_uninstall(schedule, live)


def _command_verify(args: argparse.Namespace, workspace: Path) -> Dict[str, Any]:
    schedule = load_schedule(workspace)
    live = normalize_live_tasks(
        load_json_file(contained_state_input(workspace, args.live, "live cron data"))
    )
    result = verify_live_state(schedule, live)
    result["schedule_fingerprint"] = schedule_fingerprint(schedule)
    if result["ok"] and args.record_mode:
        now = utc_now()
        schedule["last_reconciled_at"] = now
        if args.record_mode == "refresh":
            schedule["last_refreshed_at"] = now
        schedule["updated_at"] = now
        atomic_write_schedule(workspace, schedule)
        result["recorded"] = args.record_mode
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--workspace",
        help="absolute Claude project/workspace path (defaults to CLAUDE_PROJECT_DIR)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create", help="validate and atomically persist a schedule")
    create.add_argument("--input", required=True, help="candidate JSON path, or - for stdin")
    create.add_argument("--replace", action="store_true", help="replace existing state explicitly")

    subparsers.add_parser("show", help="print canonical state and tool-ready runtime tasks")
    subparsers.add_parser("validate", help="validate the persisted canonical schedule")
    subparsers.add_parser("maintain", help="choose reconcile or refresh from receipt age")

    plan = subparsers.add_parser("plan", help="compare normalized CronList data with state")
    plan.add_argument("--live", required=True, help="normalized CronList JSON path")
    plan.add_argument("--refresh", action="store_true", help="recreate every managed task")
    plan.add_argument("--output", help="absolute state-directory path for the plan JSON")

    predelete = subparsers.add_parser(
        "verify-predelete", help="verify created replacements before planned deletes"
    )
    predelete.add_argument("--live", required=True, help="post-create CronList JSON path")
    predelete.add_argument("--plan", required=True, help="saved reconciliation plan JSON path")

    uninstall = subparsers.add_parser(
        "uninstall-plan", help="classify this instance's tasks for safe uninstall"
    )
    uninstall.add_argument("--live", required=True, help="complete normalized CronList JSON path")

    verify = subparsers.add_parser("verify", help="verify exact post-action live state")
    verify.add_argument("--live", required=True, help="normalized CronList JSON path")
    verify.add_argument(
        "--record-mode",
        choices=("reconcile", "refresh"),
        help="record successful verification in persisted metadata",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        workspace = resolve_workspace(explicit=args.workspace)
        if args.command == "create":
            result = _command_create(args, workspace)
        elif args.command == "show":
            result = _command_show(workspace)
        elif args.command == "validate":
            result = _command_validate(workspace)
        elif args.command == "maintain":
            result = _command_maintain(workspace)
        elif args.command == "plan":
            result = _command_plan(args, workspace)
        elif args.command == "verify-predelete":
            result = _command_verify_predelete(args, workspace)
        elif args.command == "uninstall-plan":
            result = _command_uninstall_plan(args, workspace)
        elif args.command == "verify":
            result = _command_verify(args, workspace)
        else:  # pragma: no cover - argparse enforces the command set.
            raise ScheduleError(f"unknown command: {args.command}")
        print(_json_dump(result), end="")
        return 0 if result.get("ok", True) else 1
    except ScheduleError as exc:
        print(_json_dump({"ok": False, "error": str(exc)}), end="", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
