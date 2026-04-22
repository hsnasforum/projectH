from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class PhysicalLaneSpec:
    name: str
    pane_index: int
    pane_type: str
    support_rank: int
    read_first_doc: str
    token_source_root: str
    vendor_binary: str
    vendor_args: tuple[str, ...]


_PHYSICAL_LANE_SPECS: tuple[PhysicalLaneSpec, ...] = (
    PhysicalLaneSpec(
        name="Claude",
        pane_index=0,
        pane_type="claude",
        support_rank=2,
        read_first_doc="CLAUDE.md",
        token_source_root="~/.claude/projects",
        vendor_binary="claude",
        vendor_args=("--dangerously-skip-permissions",),
    ),
    PhysicalLaneSpec(
        name="Codex",
        pane_index=1,
        pane_type="codex",
        support_rank=3,
        read_first_doc="AGENTS.md",
        token_source_root="~/.codex/sessions",
        vendor_binary="codex",
        vendor_args=("--ask-for-approval", "never", "--disable", "apps"),
    ),
    PhysicalLaneSpec(
        name="Gemini",
        pane_index=2,
        pane_type="gemini",
        support_rank=1,
        read_first_doc="GEMINI.md",
        token_source_root="~/.gemini/tmp",
        vendor_binary="gemini",
        vendor_args=("--yolo",),
    ),
)

_LANE_SPEC_BY_NAME: dict[str, PhysicalLaneSpec] = {
    spec.name: spec for spec in _PHYSICAL_LANE_SPECS
}

_DEFAULT_ROLE_BINDINGS: dict[str, str] = {
    "implement": "Codex",
    "verify": "Claude",
    "advisory": "Gemini",
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


def physical_lane_order() -> tuple[str, ...]:
    return tuple(spec.name for spec in _PHYSICAL_LANE_SPECS)


def physical_lane_specs() -> list[dict[str, Any]]:
    return [asdict(spec) for spec in _PHYSICAL_LANE_SPECS]


def lane_spec(name: str) -> dict[str, Any]:
    spec = _LANE_SPEC_BY_NAME.get(str(name or "").strip())
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


def read_first_doc_for_owner(owner: str) -> str:
    spec = _LANE_SPEC_BY_NAME.get(str(owner or "").strip())
    if spec is not None:
        return spec.read_first_doc
    return "AGENTS.md"


def lane_vendor_command_parts(lane_name: str) -> list[str]:
    spec = _LANE_SPEC_BY_NAME.get(str(lane_name or "").strip())
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
) -> list[dict[str, Any]]:
    enabled_set = {
        str(name).strip()
        for name in list(enabled_lanes or [])
        if str(name).strip() in _LANE_SPEC_BY_NAME
    }
    owners = dict(role_owners or {})
    roles_by_lane: dict[str, list[str]] = {name: [] for name in physical_lane_order()}
    for role_name, owner in owners.items():
        owner_name = str(owner or "").strip()
        if owner_name in roles_by_lane:
            roles_by_lane[owner_name].append(str(role_name))
    lane_configs: list[dict[str, Any]] = []
    for spec in _PHYSICAL_LANE_SPECS:
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
