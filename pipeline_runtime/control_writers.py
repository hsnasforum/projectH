from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .operator_autonomy import (
    SUPPORTED_DECISION_CLASSES,
    SUPPORTED_OPERATOR_POLICIES,
    SUPPORTED_REASON_CODES,
    normalize_decision_class,
    normalize_operator_policy,
    normalize_reason_code,
)
from .schema import atomic_write_text

SUPPORTED_ESCALATION_CLASSES = frozenset({"codex_triage", "verify_triage"})


def _require_text(field_name: str, value: object) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    return text


def _normalize_repo_note_path(field_name: str, value: object) -> str:
    text = _require_text(field_name, value).replace("\\", "/")
    if text.startswith("/"):
        raise ValueError(f"{field_name} must be repo-relative")
    return text


def validate_operator_request_headers(
    *,
    control_seq: object,
    reason_code: object,
    operator_policy: object,
    decision_class: object,
    decision_required: object,
    based_on_work: object,
    based_on_verify: object,
    extra_headers: Mapping[str, object] | None = None,
) -> dict[str, object]:
    try:
        normalized_control_seq = int(control_seq)
    except (TypeError, ValueError) as exc:
        raise ValueError("control_seq must be a positive integer") from exc
    if normalized_control_seq <= 0:
        raise ValueError("control_seq must be a positive integer")

    normalized_reason_code = normalize_reason_code(reason_code)
    if normalized_reason_code not in SUPPORTED_REASON_CODES:
        raise ValueError(f"unsupported reason_code: {reason_code}")

    normalized_operator_policy = normalize_operator_policy(operator_policy)
    if normalized_operator_policy not in SUPPORTED_OPERATOR_POLICIES:
        raise ValueError(f"unsupported operator_policy: {operator_policy}")

    normalized_decision_class = normalize_decision_class(decision_class)
    if not normalized_decision_class:
        raise ValueError("decision_class is required")
    if normalized_decision_class not in SUPPORTED_DECISION_CLASSES:
        raise ValueError(f"unsupported decision_class: {decision_class}")

    validated_extra_headers: dict[str, str] = {}
    reserved = {
        "STATUS",
        "CONTROL_SEQ",
        "REASON_CODE",
        "OPERATOR_POLICY",
        "DECISION_CLASS",
        "DECISION_REQUIRED",
        "BASED_ON_WORK",
        "BASED_ON_VERIFY",
    }
    for raw_key, raw_value in dict(extra_headers or {}).items():
        key = str(raw_key or "").strip().upper()
        if not key:
            raise ValueError("extra_headers keys must be non-empty")
        if key in reserved:
            raise ValueError(f"extra_headers cannot override {key}")
        validated_extra_headers[key] = _require_text(key, raw_value)

    return {
        "control_seq": normalized_control_seq,
        "reason_code": normalized_reason_code,
        "operator_policy": normalized_operator_policy,
        "decision_class": normalized_decision_class,
        "decision_required": _require_text("decision_required", decision_required),
        "based_on_work": _normalize_repo_note_path("based_on_work", based_on_work),
        "based_on_verify": _normalize_repo_note_path("based_on_verify", based_on_verify),
        "extra_headers": validated_extra_headers,
    }


def render_operator_request(
    *,
    control_seq: object,
    reason_code: object,
    operator_policy: object,
    decision_class: object,
    decision_required: object,
    based_on_work: object,
    based_on_verify: object,
    body: object,
    extra_headers: Mapping[str, object] | None = None,
) -> str:
    validated = validate_operator_request_headers(
        control_seq=control_seq,
        reason_code=reason_code,
        operator_policy=operator_policy,
        decision_class=decision_class,
        decision_required=decision_required,
        based_on_work=based_on_work,
        based_on_verify=based_on_verify,
        extra_headers=extra_headers,
    )
    lines = [
        "STATUS: needs_operator",
        f"CONTROL_SEQ: {validated['control_seq']}",
        f"REASON_CODE: {validated['reason_code']}",
        f"OPERATOR_POLICY: {validated['operator_policy']}",
        f"DECISION_CLASS: {validated['decision_class']}",
        f"DECISION_REQUIRED: {validated['decision_required']}",
        f"BASED_ON_WORK: {validated['based_on_work']}",
        f"BASED_ON_VERIFY: {validated['based_on_verify']}",
    ]
    for key, value in dict(validated["extra_headers"]).items():
        lines.append(f"{key}: {value}")
    body_text = str(body or "").strip("\n")
    if body_text:
        lines.extend(["", body_text])
    return "\n".join(lines).rstrip() + "\n"


def write_operator_request(
    path: Path,
    *,
    control_seq: object,
    reason_code: object,
    operator_policy: object,
    decision_class: object,
    decision_required: object,
    based_on_work: object,
    based_on_verify: object,
    body: object,
    extra_headers: Mapping[str, object] | None = None,
) -> str:
    text = render_operator_request(
        control_seq=control_seq,
        reason_code=reason_code,
        operator_policy=operator_policy,
        decision_class=decision_class,
        decision_required=decision_required,
        based_on_work=based_on_work,
        based_on_verify=based_on_verify,
        body=body,
        extra_headers=extra_headers,
    )
    atomic_write_text(path, text)
    return text


def validate_implement_blocked_fields(
    *,
    block_reason: object,
    block_reason_code: object,
    request: object,
    escalation_class: object | None = None,
    handoff: object,
    handoff_sha: object,
    block_id: object,
) -> dict[str, str]:
    normalized_reason_code = normalize_reason_code(block_reason_code)
    if normalized_reason_code not in SUPPORTED_REASON_CODES:
        raise ValueError(f"unsupported block_reason_code: {block_reason_code}")

    normalized_request = normalize_reason_code(request)
    if normalized_request not in SUPPORTED_ESCALATION_CLASSES:
        raise ValueError(f"unsupported request: {request}")

    normalized_escalation = normalize_reason_code(escalation_class or normalized_request)
    if normalized_escalation not in SUPPORTED_ESCALATION_CLASSES:
        raise ValueError(f"unsupported escalation_class: {escalation_class}")
    if normalized_escalation != normalized_request:
        raise ValueError("escalation_class must match request")

    return {
        "block_reason": _require_text("block_reason", block_reason),
        "block_reason_code": normalized_reason_code,
        "request": normalized_request,
        "escalation_class": normalized_escalation,
        "handoff": _require_text("handoff", handoff),
        "handoff_sha": _require_text("handoff_sha", handoff_sha),
        "block_id": _require_text("block_id", block_id),
    }


def render_implement_blocked(
    *,
    block_reason: object,
    block_reason_code: object,
    request: object,
    escalation_class: object | None = None,
    handoff: object,
    handoff_sha: object,
    block_id: object,
) -> str:
    validated = validate_implement_blocked_fields(
        block_reason=block_reason,
        block_reason_code=block_reason_code,
        request=request,
        escalation_class=escalation_class,
        handoff=handoff,
        handoff_sha=handoff_sha,
        block_id=block_id,
    )
    lines = [
        "STATUS: implement_blocked",
        f"BLOCK_REASON: {validated['block_reason']}",
        f"BLOCK_REASON_CODE: {validated['block_reason_code']}",
        f"REQUEST: {validated['request']}",
        f"ESCALATION_CLASS: {validated['escalation_class']}",
        f"HANDOFF: {validated['handoff']}",
        f"HANDOFF_SHA: {validated['handoff_sha']}",
        f"BLOCK_ID: {validated['block_id']}",
    ]
    return "\n".join(lines) + "\n"


def validate_operator_candidate_status(status: Mapping[str, Any]) -> None:
    control = dict(status.get("control") or {})
    autonomy = dict(status.get("autonomy") or {})
    active_control_file = str(control.get("active_control_file") or "").replace("\\", "/")
    active_control_status = str(control.get("active_control_status") or "").strip()
    autonomy_mode = str(autonomy.get("mode") or "").strip()
    reason_code = str(autonomy.get("reason_code") or "").strip()
    operator_policy = str(autonomy.get("operator_policy") or "").strip()
    classification_source = str(autonomy.get("classification_source") or "").strip()
    decision_class = str(autonomy.get("decision_class") or "").strip()

    is_operator_candidate = bool(
        active_control_file.endswith("operator_request.md")
        or active_control_status == "needs_operator"
        or autonomy_mode in {"pending_operator", "needs_operator"}
        or reason_code
        or operator_policy
    )
    if not is_operator_candidate:
        return
    if classification_source not in {"operator_policy", "reason_code"}:
        raise ValueError(
            "operator candidate status must resolve from structured metadata "
            f"(got {classification_source or 'missing'})"
        )
    normalized_reason_code = normalize_reason_code(reason_code)
    if normalized_reason_code and normalized_reason_code not in SUPPORTED_REASON_CODES:
        raise ValueError(f"unsupported reason_code: {reason_code}")
    normalized_operator_policy = normalize_operator_policy(operator_policy)
    if (
        normalized_operator_policy
        and normalized_operator_policy not in SUPPORTED_OPERATOR_POLICIES
    ):
        raise ValueError(f"unsupported operator_policy: {operator_policy}")
    normalized_decision_class = normalize_decision_class(decision_class)
    if (
        normalized_decision_class
        and normalized_decision_class not in SUPPORTED_DECISION_CLASSES
    ):
        raise ValueError(f"unsupported decision_class: {decision_class}")
