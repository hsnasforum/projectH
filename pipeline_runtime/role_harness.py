from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class RoleHarnessSpec:
    role: str
    path: str
    purpose: str


_ROLE_HARNESS_SPECS: tuple[RoleHarnessSpec, ...] = (
    RoleHarnessSpec(
        role="implement",
        path=".pipeline/harness/implement.md",
        purpose="bounded implementation and work closeout protocol",
    ),
    RoleHarnessSpec(
        role="verify",
        path=".pipeline/harness/verify.md",
        purpose="verification, handoff, and next-control protocol",
    ),
    RoleHarnessSpec(
        role="advisory",
        path=".pipeline/harness/advisory.md",
        purpose="bounded arbitration and recommendation protocol",
    ),
    RoleHarnessSpec(
        role="council",
        path=".pipeline/harness/council.md",
        purpose="multi-role convergence protocol for blocked or ambiguous rounds",
    ),
)

_ROLE_HARNESS_BY_ROLE = {spec.role: spec for spec in _ROLE_HARNESS_SPECS}


def role_harness_path(role: str) -> str:
    spec = _ROLE_HARNESS_BY_ROLE.get(str(role or "").strip().lower())
    return spec.path if spec is not None else ""


def role_harness_specs() -> list[dict[str, str]]:
    return [asdict(spec) for spec in _ROLE_HARNESS_SPECS]


def role_harness_map() -> dict[str, str]:
    return {spec.role: spec.path for spec in _ROLE_HARNESS_SPECS}
