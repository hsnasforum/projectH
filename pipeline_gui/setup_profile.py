"""Pure setup-profile helpers for setup entry, runtime resolution, and support policy."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pipeline_runtime.lane_catalog import (
    build_lane_configs,
    physical_lane_order,
)
from pipeline_runtime.role_harness import role_harness_specs
from .platform import path_exists, read_json_path
from storage.json_store_base import utc_now_iso

CURRENT_SETUP_SCHEMA_VERSION = 1
SETUP_AGENT_ORDER = physical_lane_order()
_SETUP_CANONICAL_ARTIFACT_NAMES = ("request.json", "preview.json", "apply.json", "result.json")


def _normalize_line_endings(value: Any) -> Any:
    if isinstance(value, str):
        return value.replace("\r\n", "\n").replace("\r", "\n")
    if isinstance(value, list):
        return [_normalize_line_endings(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize_line_endings(item) for key, item in value.items()}
    return value


def canonical_json_text(payload: dict[str, Any]) -> str:
    normalized = _normalize_line_endings(payload)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def fingerprint_payload(payload: dict[str, Any]) -> str:
    canonical = canonical_json_text(payload)
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _coerce_list(raw_value: Any, *, field_name: str) -> tuple[list[Any], str | None]:
    if raw_value in (None, ""):
        return [], None
    if isinstance(raw_value, list):
        return raw_value, None
    return [], f"{field_name} must be a list"


def _coerce_dict(raw_value: Any, *, field_name: str) -> tuple[dict[str, Any], str | None]:
    if raw_value in (None, ""):
        return {}, None
    if isinstance(raw_value, dict):
        return {str(key): value for key, value in raw_value.items()}, None
    return {}, f"{field_name} must be an object"


def support_policy_for_level(level: str) -> dict[str, bool]:
    if level == "supported":
        return {
            "preview_allowed": True,
            "apply_allowed": True,
            "launch_allowed": True,
            "banner_required": False,
        }
    if level == "experimental":
        return {
            "preview_allowed": True,
            "apply_allowed": True,
            "launch_allowed": True,
            "banner_required": True,
        }
    if level == "blocked":
        return {
            "preview_allowed": True,
            "apply_allowed": False,
            "launch_allowed": False,
            "banner_required": True,
        }
    raise ValueError(f"unsupported support level: {level}")


def _controls_for_profile(
    normalized_payload: dict[str, Any] | None,
    *,
    support_level: str,
) -> dict[str, bool]:
    policy = support_policy_for_level(support_level)
    options = dict((normalized_payload or {}).get("role_options", {}) or {})
    return {
        "preview_allowed": policy["preview_allowed"],
        "apply_allowed": policy["apply_allowed"],
        "launch_allowed": policy["launch_allowed"],
        "banner_required": policy["banner_required"],
        "advisory_enabled": bool(options.get("advisory_enabled")),
        "operator_stop_enabled": bool(options.get("operator_stop_enabled")),
        "session_arbitration_enabled": bool(options.get("session_arbitration_enabled")),
    }


def _ordered_selected_agents(raw_agents: list[Any]) -> tuple[list[str], list[str]]:
    selected: list[str] = []
    unknown: list[str] = []
    seen: set[str] = set()
    for item in raw_agents:
        name = str(item).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        if name in SETUP_AGENT_ORDER:
            selected.append(name)
        else:
            unknown.append(name)
    return selected, unknown


def _coerce_profile_payload(payload: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    selected_raw, selected_error = _coerce_list(payload.get("selected_agents"), field_name="selected_agents")
    if selected_error:
        errors.append(selected_error)
    bindings, bindings_error = _coerce_dict(payload.get("role_bindings"), field_name="role_bindings")
    if bindings_error:
        errors.append(bindings_error)
    options, options_error = _coerce_dict(payload.get("role_options"), field_name="role_options")
    if options_error:
        errors.append(options_error)
    flags, flags_error = _coerce_dict(payload.get("mode_flags"), field_name="mode_flags")
    if flags_error:
        errors.append(flags_error)

    selected_agents, unknown_agents = _ordered_selected_agents(selected_raw)
    if unknown_agents:
        errors.extend(f"selected_agents contains unsupported agent: {name}" for name in unknown_agents)
    advisory_enabled = bool(options.get("advisory_enabled"))
    advisory_value = str(bindings.get("advisory") or "").strip() or None
    if not advisory_enabled:
        advisory_value = None
    return ({
        "schema_version": payload.get("schema_version"),
        "selected_agents": selected_agents,
        "role_bindings": {
            "implement": str(bindings.get("implement") or "").strip() or None,
            "verify": str(bindings.get("verify") or "").strip() or None,
            "advisory": advisory_value,
        },
        "role_options": {
            "advisory_enabled": advisory_enabled,
            "operator_stop_enabled": bool(options.get("operator_stop_enabled")),
            "session_arbitration_enabled": bool(options.get("session_arbitration_enabled")) if advisory_enabled else False,
        },
        "mode_flags": {
            "single_agent_mode": bool(flags.get("single_agent_mode")),
            "self_verify_allowed": bool(flags.get("self_verify_allowed")),
            "self_advisory_allowed": bool(flags.get("self_advisory_allowed")) if advisory_enabled else False,
        },
    }, errors)


def canonical_setup_payload_for_fingerprint(payload: dict[str, Any]) -> dict[str, Any]:
    normalized, _errors = _coerce_profile_payload(payload)
    return {
        "schema_version": normalized.get("schema_version"),
        "selected_agents": list(normalized.get("selected_agents", []) or []),
        "role_bindings": dict(normalized.get("role_bindings", {}) or {}),
        "role_options": dict(normalized.get("role_options", {}) or {}),
        "mode_flags": dict(normalized.get("mode_flags", {}) or {}),
        "executor_override": str(payload.get("executor_override") or "auto"),
    }


def canonical_active_profile_for_fingerprint(payload: dict[str, Any]) -> dict[str, Any]:
    normalized, _errors = _coerce_profile_payload(payload)
    return {
        "schema_version": normalized.get("schema_version"),
        "selected_agents": list(normalized.get("selected_agents", []) or []),
        "role_bindings": dict(normalized.get("role_bindings", {}) or {}),
        "role_options": dict(normalized.get("role_options", {}) or {}),
        "mode_flags": dict(normalized.get("mode_flags", {}) or {}),
    }


def active_profile_fingerprint(payload: dict[str, Any]) -> str:
    return fingerprint_payload(canonical_active_profile_for_fingerprint(payload))


def build_last_applied_record(
    *,
    setup_id: str,
    approved_preview_fingerprint: str,
    active_payload: dict[str, Any],
    restart_required: bool,
    executor: str,
    applied_at: str | None = None,
) -> dict[str, Any]:
    setup_id_text = str(setup_id or "").strip()
    if not setup_id_text:
        raise ValueError("setup_id is required for last_applied record")
    approved_text = str(approved_preview_fingerprint or "").strip()
    if not approved_text:
        raise ValueError("approved_preview_fingerprint is required for last_applied record")
    executor_text = str(executor or "").strip()
    if not executor_text:
        raise ValueError("executor is required for last_applied record")
    resolved = resolve_active_profile(active_payload if isinstance(active_payload, dict) else None)
    if resolved["resolution_state"] != "ready":
        raise ValueError("active payload must resolve before building last_applied record")
    return {
        "setup_id": setup_id_text,
        "approved_preview_fingerprint": approved_text,
        "active_profile_fingerprint": active_profile_fingerprint(active_payload),
        "applied_at": str(applied_at or utc_now_iso()),
        "restart_required": bool(restart_required),
        "executor": executor_text,
    }


def _validate_last_applied_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field_name in (
        "setup_id",
        "approved_preview_fingerprint",
        "active_profile_fingerprint",
        "applied_at",
        "executor",
    ):
        if not str(payload.get(field_name) or "").strip():
            errors.append(f"{field_name} is required")
    if not isinstance(payload.get("restart_required"), bool):
        errors.append("restart_required must be a boolean")
    return errors


def reconcile_last_applied(
    *,
    active_payload: dict[str, Any] | None,
    last_applied_payload: dict[str, Any] | None,
    active_exists: bool | None = None,
    last_applied_exists: bool | None = None,
) -> dict[str, Any]:
    active_present = bool(active_payload) if active_exists is None else bool(active_exists)
    record_present = bool(last_applied_payload) if last_applied_exists is None else bool(last_applied_exists)
    if not record_present:
        return {
            "status": "missing",
            "setup_id": "",
            "executor": "",
            "restart_required": False,
            "recorded_active_profile_fingerprint": "",
            "current_active_profile_fingerprint": "",
            "messages": ["last_applied record is missing."],
        }
    if not isinstance(last_applied_payload, dict):
        return {
            "status": "broken",
            "setup_id": "",
            "executor": "",
            "restart_required": False,
            "recorded_active_profile_fingerprint": "",
            "current_active_profile_fingerprint": "",
            "messages": ["last_applied record is unreadable."],
        }
    record_errors = _validate_last_applied_payload(last_applied_payload)
    if record_errors:
        return {
            "status": "broken",
            "setup_id": str(last_applied_payload.get("setup_id") or ""),
            "executor": str(last_applied_payload.get("executor") or ""),
            "restart_required": bool(last_applied_payload.get("restart_required")),
            "recorded_active_profile_fingerprint": str(last_applied_payload.get("active_profile_fingerprint") or ""),
            "current_active_profile_fingerprint": "",
            "messages": record_errors,
        }
    if not active_present:
        return {
            "status": "mismatch",
            "setup_id": str(last_applied_payload.get("setup_id") or ""),
            "executor": str(last_applied_payload.get("executor") or ""),
            "restart_required": bool(last_applied_payload.get("restart_required")),
            "recorded_active_profile_fingerprint": str(last_applied_payload.get("active_profile_fingerprint") or ""),
            "current_active_profile_fingerprint": "",
            "messages": ["Active profile is missing while last_applied record still exists."],
        }
    resolved = resolve_active_profile(active_payload if isinstance(active_payload, dict) else None)
    if resolved["resolution_state"] != "ready":
        return {
            "status": "broken",
            "setup_id": str(last_applied_payload.get("setup_id") or ""),
            "executor": str(last_applied_payload.get("executor") or ""),
            "restart_required": bool(last_applied_payload.get("restart_required")),
            "recorded_active_profile_fingerprint": str(last_applied_payload.get("active_profile_fingerprint") or ""),
            "current_active_profile_fingerprint": "",
            "messages": ["Active profile cannot be reconciled."] + list(resolved.get("messages") or []),
        }
    current_fingerprint = active_profile_fingerprint(active_payload)
    recorded_fingerprint = str(last_applied_payload.get("active_profile_fingerprint") or "")
    status = "ok" if current_fingerprint == recorded_fingerprint else "mismatch"
    message = (
        "Active profile matches last_applied record."
        if status == "ok"
        else "Active profile does not match last_applied record."
    )
    return {
        "status": status,
        "setup_id": str(last_applied_payload.get("setup_id") or ""),
        "executor": str(last_applied_payload.get("executor") or ""),
        "restart_required": bool(last_applied_payload.get("restart_required")),
        "recorded_active_profile_fingerprint": recorded_fingerprint,
        "current_active_profile_fingerprint": current_fingerprint,
        "messages": [message],
    }


def cleanup_stale_setup_artifacts(
    *,
    setup_dir: Path,
    protected_setup_ids: set[str],
) -> list[Path]:
    removed: list[Path] = []
    if not setup_dir.exists():
        return removed
    protected = {str(item).strip() for item in protected_setup_ids if str(item).strip()}
    for file_name in _SETUP_CANONICAL_ARTIFACT_NAMES:
        path = setup_dir / file_name
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            try:
                path.unlink()
            except FileNotFoundError:
                continue
            except OSError:
                continue
            removed.append(path)
            continue
        if not isinstance(payload, dict):
            continue
        setup_id = str(payload.get("setup_id") or "").strip()
        if setup_id and setup_id in protected:
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            continue
        except OSError:
            continue
        removed.append(path)
    return removed


def validate_profile_payload(payload: dict[str, Any]) -> list[str]:
    normalized, errors = _coerce_profile_payload(payload)
    schema_version = normalized.get("schema_version")
    if not isinstance(schema_version, int):
        return errors + ["schema_version must be an integer"]
    if schema_version != CURRENT_SETUP_SCHEMA_VERSION:
        return errors

    selected = list(normalized.get("selected_agents", []) or [])
    selected_set = set(selected)
    bindings = dict(normalized.get("role_bindings", {}) or {})
    options = dict(normalized.get("role_options", {}) or {})
    flags = dict(normalized.get("mode_flags", {}) or {})

    implement = str(bindings.get("implement") or "")
    verify = str(bindings.get("verify") or "")
    advisory = str(bindings.get("advisory") or "")
    advisory_enabled = bool(options.get("advisory_enabled"))
    self_verify_allowed = bool(flags.get("self_verify_allowed"))
    self_advisory_allowed = bool(flags.get("self_advisory_allowed"))

    validation_errors = list(errors)
    if not selected:
        validation_errors.append("no agents selected")
    if not implement:
        validation_errors.append("implement role is required")
    elif implement not in selected_set:
        validation_errors.append("implement role points to an unselected agent")
    if verify and verify not in selected_set:
        validation_errors.append("verify role points to an unselected agent")
    if advisory_enabled and advisory and advisory not in selected_set:
        validation_errors.append("advisory role points to an unselected agent")
    if implement and verify and implement == verify and not self_verify_allowed:
        validation_errors.append("implement and verify cannot share the same agent without self_verify_allowed")
    if advisory_enabled and advisory and advisory in {implement, verify} and not self_advisory_allowed:
        validation_errors.append("advisory cannot share implement or verify without self_advisory_allowed")
    return validation_errors


def _support_level_for_profile(payload: dict[str, Any]) -> str:
    normalized, _errors = _coerce_profile_payload(payload)
    selected = list(normalized.get("selected_agents", []) or [])
    bindings = dict(normalized.get("role_bindings", {}) or {})
    options = dict(normalized.get("role_options", {}) or {})
    flags = dict(normalized.get("mode_flags", {}) or {})
    implement = str(bindings.get("implement") or "")
    verify = str(bindings.get("verify") or "")
    advisory = str(bindings.get("advisory") or "")
    advisory_enabled = bool(options.get("advisory_enabled"))
    self_verify_allowed = bool(flags.get("self_verify_allowed"))
    selected_count = len(selected)
    implement_verify_distinct = bool(implement and verify and implement != verify)

    if (
        selected_count == 3
        and implement_verify_distinct
        and advisory_enabled
        and bool(advisory)
    ):
        return "supported"
    if selected_count == 2 and implement_verify_distinct and not advisory_enabled:
        return "supported"
    if (
        selected_count == 1
        and implement
        and implement == verify
        and not advisory_enabled
        and self_verify_allowed
    ):
        return "experimental"
    if selected:
        return "experimental"
    return "blocked"


def _prompt_owners_for_runtime_plan(
    *,
    enabled_lanes: list[str],
    role_owners: dict[str, Any],
) -> dict[str, Any]:
    enabled_set = {str(name).strip() for name in enabled_lanes if str(name).strip() in SETUP_AGENT_ORDER}
    prompt_owners: dict[str, Any] = {}
    for role_name in ("implement", "verify", "advisory"):
        owner = str(role_owners.get(role_name) or "").strip()
        prompt_owners[role_name] = owner if owner in enabled_set else None
    return prompt_owners


def resolve_active_profile(payload: dict[str, Any] | None) -> dict[str, Any]:
    if payload is None:
        return {
            "resolution_state": "broken",
            "support_level": "blocked",
            "controls": _controls_for_profile(None, support_level="blocked"),
            "effective_runtime_plan": None,
            "messages": ["Active profile is missing."],
        }

    normalized, coercion_errors = _coerce_profile_payload(payload)
    schema_version = normalized.get("schema_version")
    if not isinstance(schema_version, int):
        return {
            "resolution_state": "broken",
            "support_level": "blocked",
            "controls": _controls_for_profile(normalized, support_level="blocked"),
            "effective_runtime_plan": None,
            "messages": coercion_errors + ["Active profile schema_version is missing or invalid."],
        }
    if schema_version < CURRENT_SETUP_SCHEMA_VERSION:
        return {
            "resolution_state": "needs_migration",
            "support_level": "blocked",
            "controls": _controls_for_profile(normalized, support_level="blocked"),
            "effective_runtime_plan": None,
            "messages": ["Active profile requires migration to the current schema."],
        }
    if schema_version > CURRENT_SETUP_SCHEMA_VERSION:
        return {
            "resolution_state": "broken",
            "support_level": "blocked",
            "controls": _controls_for_profile(normalized, support_level="blocked"),
            "effective_runtime_plan": None,
            "messages": ["Active profile schema_version is newer than this launcher supports."],
        }

    errors = validate_profile_payload(payload)
    if errors:
        return {
            "resolution_state": "broken",
            "support_level": "blocked",
            "controls": _controls_for_profile(normalized, support_level="blocked"),
            "effective_runtime_plan": None,
            "messages": errors,
        }

    support_level = _support_level_for_profile(normalized)
    controls = _controls_for_profile(normalized, support_level=support_level)
    bindings = dict(normalized.get("role_bindings", {}) or {})
    options = dict(normalized.get("role_options", {}) or {})
    enabled_lanes = list(normalized.get("selected_agents", []) or [])
    role_owners = {
        "implement": bindings.get("implement"),
        "verify": bindings.get("verify"),
        "advisory": bindings.get("advisory") if options.get("advisory_enabled") else None,
    }
    prompt_owners = _prompt_owners_for_runtime_plan(
        enabled_lanes=enabled_lanes,
        role_owners=role_owners,
    )
    messages: list[str] = []
    if support_level == "experimental":
        messages.append("Profile is experimental and requires extra operator attention.")
    effective_runtime_plan = {
        "enabled_lanes": enabled_lanes,
        "role_owners": role_owners,
        "prompt_owners": prompt_owners,
        "role_harnesses": role_harness_specs(),
        "controls": dict(controls),
    }
    return {
        "resolution_state": "ready",
        "support_level": support_level,
        "controls": controls,
        "effective_runtime_plan": effective_runtime_plan,
        "messages": messages,
    }


def runtime_adapter_from_resolved(resolved: dict[str, Any]) -> dict[str, Any]:
    controls = dict(resolved.get("controls") or {})
    effective_plan = dict(resolved.get("effective_runtime_plan") or {})
    raw_enabled_lanes = list(effective_plan.get("enabled_lanes") or [])
    enabled_set = {str(name).strip() for name in raw_enabled_lanes if str(name).strip() in SETUP_AGENT_ORDER}
    enabled_lanes = [lane for lane in SETUP_AGENT_ORDER if lane in enabled_set]
    raw_role_owners = dict(effective_plan.get("role_owners") or {})
    raw_prompt_owners = dict(effective_plan.get("prompt_owners") or {})
    role_owners = {
        "implement": str(raw_role_owners.get("implement") or "").strip() or None,
        "verify": str(raw_role_owners.get("verify") or "").strip() or None,
        "advisory": str(raw_role_owners.get("advisory") or "").strip() or None,
    }
    prompt_owners = {
        "implement": str(raw_prompt_owners.get("implement") or "").strip() or role_owners["implement"],
        "verify": str(raw_prompt_owners.get("verify") or "").strip() or role_owners["verify"],
        "advisory": (
            str(raw_prompt_owners.get("advisory") or "").strip()
            or role_owners["advisory"]
        ),
    }
    lane_configs = build_lane_configs(
        enabled_lanes=enabled_lanes,
        role_owners=role_owners,
    )

    return {
        "resolution_state": str(resolved.get("resolution_state") or "broken"),
        "support_level": str(resolved.get("support_level") or "blocked"),
        "controls": controls,
        "messages": [str(item).strip() for item in list(resolved.get("messages") or []) if str(item).strip()],
        "enabled_lanes": enabled_lanes,
        "role_owners": role_owners,
        "prompt_owners": prompt_owners,
        "role_harnesses": list(effective_plan.get("role_harnesses") or role_harness_specs()),
        "lane_configs": lane_configs,
    }


def resolve_active_profile_path(path: Path) -> dict[str, Any]:
    if not path_exists(path):
        return resolve_active_profile(None)
    payload = read_json_path(path)
    if payload is None:
        return {
            "resolution_state": "broken",
            "support_level": "blocked",
            "controls": _controls_for_profile(None, support_level="blocked"),
            "effective_runtime_plan": None,
            "messages": ["Active profile is unreadable."],
        }
    return resolve_active_profile(payload)


def resolve_project_active_profile(project_root: Path) -> dict[str, Any]:
    return resolve_active_profile_path(project_root / ".pipeline" / "config" / "agent_profile.json")


def resolve_project_runtime_adapter(project_root: Path) -> dict[str, Any]:
    return runtime_adapter_from_resolved(resolve_project_active_profile(project_root))


def join_resolver_messages(resolved: dict[str, Any]) -> str:
    messages = [
        str(item).strip()
        for item in list(resolved.get("messages") or [])
        if str(item).strip()
    ]
    return " | ".join(messages)


def display_resolver_messages(
    resolved: dict[str, Any],
    *,
    active_profile_path: str = ".pipeline/config/agent_profile.json",
) -> list[str]:
    messages = [
        str(item).strip()
        for item in list(resolved.get("messages") or [])
        if str(item).strip()
    ]
    if not messages:
        return []
    localized: list[str] = []
    for message in messages:
        if message == "Active profile is missing.":
            localized.append(
                f"active profile이 없습니다 ({active_profile_path}). 설정 탭에서 미리보기 생성 후 적용을 완료해 주세요."
            )
        elif message == "Active profile is unreadable.":
            localized.append(
                f"active profile을 읽을 수 없습니다 ({active_profile_path}). 파일을 정리하거나 설정을 다시 적용해 주세요."
            )
        elif message == "Active profile requires migration to the current schema.":
            localized.append("active profile schema가 오래되었습니다. migration 후 다시 시도해 주세요.")
        elif message == "Active profile schema_version is newer than this launcher supports.":
            localized.append("active profile schema_version이 현재 launcher보다 새롭습니다.")
        else:
            localized.append(message)
    return localized


def join_display_resolver_messages(
    resolved: dict[str, Any],
    *,
    active_profile_path: str = ".pipeline/config/agent_profile.json",
) -> str:
    return " / ".join(
        display_resolver_messages(resolved, active_profile_path=active_profile_path)
    )


def classify_setup_entry(snapshot: dict[str, Any]) -> dict[str, Any]:
    active_exists = bool(snapshot.get("active_exists"))
    active_payload = snapshot.get("active_payload")
    draft_exists = bool(snapshot.get("draft_exists"))
    request_exists = bool(snapshot.get("request_exists"))
    preview_exists = bool(snapshot.get("preview_exists"))
    apply_exists = bool(snapshot.get("apply_exists"))
    result_exists = bool(snapshot.get("result_exists"))
    legacy_profile_exists = bool(snapshot.get("legacy_profile_exists"))
    has_resume_artifacts = draft_exists or request_exists or preview_exists or apply_exists or result_exists

    if active_exists:
        resolved = resolve_active_profile(active_payload if isinstance(active_payload, dict) else None)
        if resolved["resolution_state"] == "needs_migration":
            return {"entry_state": "needs_migration", "messages": list(resolved["messages"])}
        if resolved["resolution_state"] != "ready" or resolved["support_level"] == "blocked":
            return {"entry_state": "broken_active_profile", "messages": list(resolved["messages"])}
        if has_resume_artifacts:
            return {
                "entry_state": "resume_setup",
                "messages": ["Setup draft or in-flight setup artifacts were found."],
            }
        return {"entry_state": "ready_normal", "messages": list(resolved["messages"])}

    if legacy_profile_exists:
        return {
            "entry_state": "needs_migration",
            "messages": ["Legacy profile exists and requires migration before normal startup."],
        }

    if has_resume_artifacts:
        return {
            "entry_state": "resume_setup",
            "messages": ["Setup draft or in-flight setup artifacts were found."],
        }

    return {
        "entry_state": "first_run",
        "messages": ["No active profile, draft, or migration target was found."],
    }
