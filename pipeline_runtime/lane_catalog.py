from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PhysicalLaneSpec:
    name: str
    pane_index: int
    pane_type: str
    roles: tuple[str, ...]
    support_rank: int
    read_first_doc: str
    token_source: str
    token_source_root: str
    agent_cli: str
    vendor_binary: str
    vendor_args: tuple[str, ...]


_PHYSICAL_LANE_SPECS: tuple[PhysicalLaneSpec, ...] = (
    PhysicalLaneSpec(
        name="Claude",
        pane_index=0,
        pane_type="claude",
        roles=("implement", "advisory"),
        support_rank=2,
        read_first_doc="CLAUDE.md",
        token_source="claude",
        token_source_root="~/.claude/projects",
        agent_cli="claude",
        vendor_binary="claude",
        vendor_args=("--dangerously-skip-permissions",),
    ),
    PhysicalLaneSpec(
        name="Codex",
        pane_index=1,
        pane_type="codex",
        roles=("implement", "verify", "advisory"),
        support_rank=3,
        read_first_doc="AGENTS.md",
        token_source="codex",
        token_source_root="~/.codex/sessions",
        agent_cli="codex",
        vendor_binary="codex",
        vendor_args=("--ask-for-approval", "never", "--disable", "apps"),
    ),
    PhysicalLaneSpec(
        name="Gemini",
        pane_index=2,
        pane_type="gemini",
        roles=("advisory",),
        support_rank=1,
        read_first_doc="GEMINI.md",
        token_source="gemini",
        token_source_root="~/.gemini/tmp",
        agent_cli="gemini",
        vendor_binary="gemini",
        vendor_args=("--yolo",),
    ),
)

_LANE_SPEC_BY_NAME: dict[str, PhysicalLaneSpec] = {
    spec.name: spec for spec in _PHYSICAL_LANE_SPECS
}

_DEFAULT_ROLE_BINDINGS: dict[str, str] = {
    "implement": "Codex",
    "verify": "Codex",
    "advisory": "Claude",
}

_LEGACY_ROLE_BINDINGS: dict[str, str] = {
    "implement": "Claude",
    "verify": "Codex",
    "advisory": "Gemini",
}

_LEGACY_WATCHER_PANE_TARGET_ARG_BY_PANE_TYPE: dict[str, str] = {
    "claude": "--claude-pane-target",
    "codex": "--verify-pane-target",
    "gemini": "--gemini-pane-target",
}

_TOKEN_SOURCE_ROOT_BY_TOKEN_SOURCE: dict[str, str] = {
    "claude": "~/.claude/projects",
    "codex": "~/.codex/sessions",
    "gemini": "~/.gemini/tmp",
}

_VENDOR_ARGS_BY_AGENT_CLI: dict[str, tuple[str, ...]] = {
    "claude": ("--dangerously-skip-permissions",),
    "codex": ("--ask-for-approval", "never", "--disable", "apps"),
    "gemini": ("--yolo",),
}


def _lane_spec_by_name(lane_specs: tuple[PhysicalLaneSpec, ...]) -> dict[str, PhysicalLaneSpec]:
    return {spec.name: spec for spec in lane_specs}


def _clean_str(value: object) -> str:
    return str(value or "").strip()


def _clean_str_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(_clean_str(item) for item in value if _clean_str(item))


def _int_value(value: object, default: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _physical_lane_order_from_specs(lane_specs: tuple[PhysicalLaneSpec, ...]) -> tuple[str, ...]:
    return tuple(spec.name for spec in lane_specs)


def _physical_lane_specs_as_dicts(lane_specs: tuple[PhysicalLaneSpec, ...]) -> list[dict[str, Any]]:
    return [asdict(spec) for spec in lane_specs]


def _spec_from_config_item(
    item: object,
    *,
    fallback_by_name: dict[str, PhysicalLaneSpec],
    fallback_rank: int,
) -> PhysicalLaneSpec | None:
    if not isinstance(item, dict):
        return None
    name = _clean_str(item.get("name"))
    if not name:
        return None
    fallback = fallback_by_name.get(name)
    token_source = (
        _clean_str(item.get("token_source"))
        or (fallback.token_source if fallback is not None else "")
        or name.lower()
    )
    agent_cli = (
        _clean_str(item.get("agent_cli"))
        or (fallback.agent_cli if fallback is not None else "")
        or token_source
    )
    pane_type = (
        _clean_str(item.get("pane_type"))
        or (fallback.pane_type if fallback is not None else "")
        or token_source
    ).lower()
    roles = _clean_str_tuple(item.get("roles")) or (fallback.roles if fallback is not None else ())
    vendor_args = _clean_str_tuple(item.get("vendor_args"))
    if not vendor_args:
        vendor_args = (
            fallback.vendor_args
            if fallback is not None
            else _VENDOR_ARGS_BY_AGENT_CLI.get(agent_cli, ())
        )
    token_source_root = (
        _clean_str(item.get("token_source_root"))
        or (fallback.token_source_root if fallback is not None else "")
        or _TOKEN_SOURCE_ROOT_BY_TOKEN_SOURCE.get(token_source, f"~/.{token_source}/tmp")
    )
    return PhysicalLaneSpec(
        name=name,
        pane_index=_int_value(item.get("pane_index"), fallback.pane_index if fallback is not None else fallback_rank),
        pane_type=pane_type,
        roles=roles,
        support_rank=_int_value(item.get("support_rank"), fallback.support_rank if fallback is not None else fallback_rank),
        read_first_doc=_clean_str(item.get("read_first_doc")) or (fallback.read_first_doc if fallback is not None else "AGENTS.md"),
        token_source=token_source,
        token_source_root=token_source_root,
        agent_cli=agent_cli,
        vendor_binary=_clean_str(item.get("vendor_binary")) or (fallback.vendor_binary if fallback is not None else agent_cli),
        vendor_args=vendor_args,
    )


def load_physical_lane_specs(project_root: Path) -> tuple[PhysicalLaneSpec, ...]:
    path = project_root / ".pipeline" / "config" / "lanes.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _PHYSICAL_LANE_SPECS
    if not isinstance(payload, dict):
        return _PHYSICAL_LANE_SPECS
    raw_lanes = payload.get("lanes")
    if not isinstance(raw_lanes, list):
        return _PHYSICAL_LANE_SPECS
    fallback_by_name = _lane_spec_by_name(_PHYSICAL_LANE_SPECS)
    specs = [
        spec
        for index, item in enumerate(raw_lanes)
        if (
            spec := _spec_from_config_item(
                item,
                fallback_by_name=fallback_by_name,
                fallback_rank=index,
            )
        ) is not None
    ]
    return tuple(specs) if specs else _PHYSICAL_LANE_SPECS


def physical_lane_order() -> tuple[str, ...]:
    return _physical_lane_order_from_specs(_PHYSICAL_LANE_SPECS)


def physical_lane_specs() -> list[dict[str, Any]]:
    return _physical_lane_specs_as_dicts(_PHYSICAL_LANE_SPECS)


def lane_spec(name: str, lane_specs: tuple[PhysicalLaneSpec, ...] | None = None) -> dict[str, Any]:
    spec = _lane_spec_by_name(tuple(lane_specs or _PHYSICAL_LANE_SPECS)).get(str(name or "").strip())
    return asdict(spec) if spec is not None else {}


def lane_name_order_map() -> dict[str, int]:
    return {spec.name: spec.pane_index for spec in _PHYSICAL_LANE_SPECS}


def lane_support_rank_map() -> dict[str, int]:
    return {spec.name: spec.support_rank for spec in _PHYSICAL_LANE_SPECS}


def lane_token_source_map() -> dict[str, str]:
    return {spec.name: spec.token_source_root for spec in _PHYSICAL_LANE_SPECS}


def default_role_bindings() -> dict[str, str]:
    return dict(_DEFAULT_ROLE_BINDINGS)


def legacy_role_bindings() -> dict[str, str]:
    return dict(_LEGACY_ROLE_BINDINGS)


def role_bindings_for_topology(topology: str) -> dict[str, str]:
    topology_name = str(topology or "").strip().lower()
    if topology_name == "legacy":
        return legacy_role_bindings()
    return default_role_bindings()


def default_selected_agent() -> str:
    return default_role_bindings()["implement"]


def read_first_doc_for_owner(owner: str, lane_specs: tuple[PhysicalLaneSpec, ...] | None = None) -> str:
    spec = _lane_spec_by_name(tuple(lane_specs or _PHYSICAL_LANE_SPECS)).get(str(owner or "").strip())
    if spec is not None:
        return spec.read_first_doc
    return "AGENTS.md"


def lane_vendor_command_parts(
    lane_name: str,
    lane_specs: tuple[PhysicalLaneSpec, ...] | None = None,
) -> list[str]:
    spec = _lane_spec_by_name(tuple(lane_specs or _PHYSICAL_LANE_SPECS)).get(str(lane_name or "").strip())
    if spec is None:
        return []
    return [spec.vendor_binary, *spec.vendor_args]


def legacy_watcher_pane_target_arg_for_lane(lane: dict[str, Any]) -> str:
    pane_type = str((lane or {}).get("pane_type") or "").strip().lower()
    return _LEGACY_WATCHER_PANE_TARGET_ARG_BY_PANE_TYPE.get(pane_type, "")


def build_lane_configs(
    *,
    enabled_lanes: list[str] | tuple[str, ...] | set[str] | None,
    role_owners: dict[str, Any] | None,
    lane_specs: tuple[PhysicalLaneSpec, ...] | None = None,
) -> list[dict[str, Any]]:
    specs = tuple(lane_specs or _PHYSICAL_LANE_SPECS)
    spec_names = {spec.name for spec in specs}
    enabled_set = {
        str(name).strip()
        for name in list(enabled_lanes or [])
        if str(name).strip() in spec_names
    }
    owners = dict(role_owners or {})
    roles_by_lane: dict[str, list[str]] = {name: [] for name in _physical_lane_order_from_specs(specs)}
    for role_name, owner in owners.items():
        owner_name = str(owner or "").strip()
        if owner_name in roles_by_lane:
            roles_by_lane[owner_name].append(str(role_name))
    lane_configs: list[dict[str, Any]] = []
    for spec in specs:
        lane_configs.append(
            {
                **asdict(spec),
                "enabled": spec.name in enabled_set,
                "roles": list(roles_by_lane.get(spec.name) or []),
            }
        )
    return lane_configs


def build_agent_profile_payload(
    *,
    selected_agents: list[str] | tuple[str, ...] | None = None,
    role_bindings: dict[str, str | None] | None = None,
    advisory_enabled: bool = True,
    operator_stop_enabled: bool = True,
    session_arbitration_enabled: bool | None = None,
    single_agent_mode: bool | None = None,
    self_verify_allowed: bool = False,
    self_advisory_allowed: bool = False,
    schema_version: int = 1,
) -> dict[str, object]:
    selected = [
        name
        for name in physical_lane_order()
        if name in {
            str(item).strip()
            for item in list(selected_agents or physical_lane_order())
            if str(item).strip()
        }
    ]
    advisory_enabled_value = bool(advisory_enabled)
    bindings = default_role_bindings()
    for key, value in dict(role_bindings or {}).items():
        if key not in bindings:
            continue
        text = str(value or "").strip()
        if text:
            bindings[key] = text
    if not advisory_enabled_value:
        bindings["advisory"] = ""
    if single_agent_mode is None:
        single_agent_mode = len(selected) == 1
    if session_arbitration_enabled is None:
        session_arbitration_enabled = advisory_enabled_value
    return {
        "schema_version": int(schema_version),
        "selected_agents": selected,
        "role_bindings": {
            "implement": bindings["implement"],
            "verify": bindings["verify"],
            "advisory": bindings["advisory"],
        },
        "role_options": {
            "advisory_enabled": advisory_enabled_value,
            "operator_stop_enabled": bool(operator_stop_enabled),
            "session_arbitration_enabled": bool(session_arbitration_enabled) if advisory_enabled_value else False,
        },
        "mode_flags": {
            "single_agent_mode": bool(single_agent_mode),
            "self_verify_allowed": bool(self_verify_allowed),
            "self_advisory_allowed": bool(self_advisory_allowed) if advisory_enabled_value else False,
        },
    }
