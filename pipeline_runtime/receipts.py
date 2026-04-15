from __future__ import annotations

from pathlib import Path
from typing import Any

from .schema import atomic_write_json, read_json, sha256_file

_MANIFEST_REQUIRED_FIELDS = {
    "schema_version",
    "job_id",
    "round",
    "role",
    "artifact_hash",
    "created_at",
}


def receipt_id(job_id: str, round_number: int) -> str:
    return f"{job_id}-r{round_number}"


def receipt_path(receipts_dir: Path, job_id: str, round_number: int) -> Path:
    return receipts_dir / f"{receipt_id(job_id, round_number)}.json"


def validate_manifest(job_state: dict[str, Any]) -> tuple[bool, str]:
    manifest_value = str(job_state.get("verify_manifest_path") or "").strip()
    if not manifest_value:
        return False, "missing_manifest_path"
    manifest_path = Path(manifest_value)
    if not manifest_path.exists():
        return False, "missing_manifest_file"
    manifest = read_json(manifest_path)
    if not manifest:
        return False, "invalid_manifest_json"
    missing = sorted(_MANIFEST_REQUIRED_FIELDS.difference(manifest.keys()))
    if missing:
        return False, f"missing_manifest_fields:{','.join(missing)}"
    if str(manifest.get("job_id") or "") != str(job_state.get("job_id") or ""):
        return False, "job_id_mismatch"
    if int(manifest.get("round") or -1) != int(job_state.get("round") or -1):
        return False, "round_mismatch"
    if str(manifest.get("role") or "") not in {"verify", "slot_verify"}:
        return False, "role_mismatch"
    if str(manifest.get("artifact_hash") or "") != str(job_state.get("artifact_hash") or ""):
        return False, "artifact_hash_mismatch"
    return True, ""


def build_receipt(
    *,
    run_id: str,
    job_state: dict[str, Any],
    verify_artifact_path: Path,
    control_seq: int,
    target_lane: str,
    closed_at: str,
    emitted_by: str = "supervisor",
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "receipt_id": receipt_id(str(job_state.get("job_id") or ""), int(job_state.get("round") or 0)),
        "run_id": run_id,
        "job_id": str(job_state.get("job_id") or ""),
        "round": int(job_state.get("round") or 0),
        "target_lane": target_lane,
        "artifact_path": str(verify_artifact_path),
        "artifact_hash": sha256_file(verify_artifact_path),
        "verify_manifest_path": str(job_state.get("verify_manifest_path") or ""),
        "verify_result": str(job_state.get("verify_result") or "accepted"),
        "control_seq": control_seq,
        "closed_at": closed_at,
        "emitted_by": emitted_by,
    }


def write_receipt(receipts_dir: Path, receipt: dict[str, Any]) -> Path:
    path = receipt_path(receipts_dir, str(receipt.get("job_id") or ""), int(receipt.get("round") or 0))
    atomic_write_json(path, receipt)
    return path
