from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .operator_autonomy import (
    PR_MERGE_GATE_REASON,
    normalize_reason_code,
    referenced_operator_pr_numbers,
)

_HEAD_SHA_RE = re.compile(
    r"(?im)^\s*(?:[-*]\s*)?(?:HEAD|HEAD_SHA)\s*:\s*`?([0-9a-f]{7,40})\b"
)
_PR_MERGE_COMPLETED = "completed"
_PR_MERGE_HEAD_MISMATCH = "head_mismatch"
_PR_MERGE_PENDING = "pending"


@dataclass(frozen=True)
class PrMergeGateResolution:
    completed_pr_numbers: tuple[int, ...] = ()
    head_mismatch_pr_numbers: tuple[int, ...] = ()


class PrMergeStatusCache:
    """Small TTL cache for checking whether referenced GitHub PRs are merged."""

    def __init__(
        self,
        *,
        success_ttl_sec: float = 300.0,
        miss_ttl_sec: float = 15.0,
        timeout_sec: float = 4.0,
    ) -> None:
        self.success_ttl_sec = success_ttl_sec
        self.miss_ttl_sec = miss_ttl_sec
        self.timeout_sec = timeout_sec
        self._cache: dict[tuple[int, str], tuple[float, str]] = {}

    def completed_pr_numbers(
        self,
        repo_root: Path,
        control_text: object,
        control_meta: Mapping[str, Any] | None = None,
        *,
        now_ts: float | None = None,
    ) -> list[int]:
        return list(
            self.control_resolution(
                repo_root,
                control_text,
                control_meta,
                now_ts=now_ts,
            ).completed_pr_numbers
        )

    def control_resolution(
        self,
        repo_root: Path,
        control_text: object,
        control_meta: Mapping[str, Any] | None = None,
        *,
        now_ts: float | None = None,
    ) -> PrMergeGateResolution:
        meta = {str(key).strip().lower(): value for key, value in dict(control_meta or {}).items()}
        if normalize_reason_code(meta.get("reason_code")) != PR_MERGE_GATE_REASON:
            return PrMergeGateResolution()

        now = time.time() if now_ts is None else now_ts
        expected_head_sha = _expected_head_sha(control_text, meta)
        completed: list[int] = []
        mismatched: list[int] = []
        for number in referenced_operator_pr_numbers(control_text, meta):
            cache_key = (number, expected_head_sha)
            cached = self._cache.get(cache_key)
            if cached is not None:
                checked_at, state = cached
                ttl = self.success_ttl_sec if state in {_PR_MERGE_COMPLETED, _PR_MERGE_HEAD_MISMATCH} else self.miss_ttl_sec
                if now - checked_at < ttl:
                    if state == _PR_MERGE_COMPLETED:
                        completed.append(number)
                    elif state == _PR_MERGE_HEAD_MISMATCH:
                        mismatched.append(number)
                    continue
            state = self._probe_pr_merge_state(
                repo_root,
                number,
                expected_head_sha=expected_head_sha,
            )
            self._cache[cache_key] = (now, state)
            if state == _PR_MERGE_COMPLETED:
                completed.append(number)
            elif state == _PR_MERGE_HEAD_MISMATCH:
                mismatched.append(number)
        return PrMergeGateResolution(
            completed_pr_numbers=tuple(completed),
            head_mismatch_pr_numbers=tuple(mismatched),
        )

    def _probe_pr_merge_state(
        self,
        repo_root: Path,
        number: int,
        *,
        expected_head_sha: str = "",
    ) -> str:
        if shutil.which("gh") is None:
            return _PR_MERGE_PENDING
        try:
            result = subprocess.run(
                ["gh", "pr", "view", str(number), "--json", "state,mergedAt,headRefOid"],
                cwd=str(repo_root),
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout_sec,
            )
        except (OSError, subprocess.TimeoutExpired):
            return _PR_MERGE_PENDING
        if result.returncode != 0:
            return _PR_MERGE_PENDING
        try:
            payload = json.loads(result.stdout or "{}")
        except json.JSONDecodeError:
            return _PR_MERGE_PENDING
        state = str(payload.get("state") or "").strip().upper()
        merged_at = str(payload.get("mergedAt") or "").strip()
        head_ref_oid = str(payload.get("headRefOid") or "").strip().lower()
        merged = state == "MERGED" or bool(merged_at)
        if not merged:
            return _PR_MERGE_PENDING
        if expected_head_sha and not _sha_matches(head_ref_oid, expected_head_sha):
            return _PR_MERGE_HEAD_MISMATCH
        return _PR_MERGE_COMPLETED


def _expected_head_sha(
    control_text: object,
    control_meta: Mapping[str, Any] | None = None,
) -> str:
    meta = {str(key).strip().lower(): value for key, value in dict(control_meta or {}).items()}
    for key in ("head_sha", "head", "head_ref_oid"):
        value = str(meta.get(key) or "").strip().strip("`").lower()
        if re.fullmatch(r"[0-9a-f]{7,40}", value):
            return value
    match = _HEAD_SHA_RE.search(str(control_text or ""))
    if not match:
        return ""
    return str(match.group(1) or "").strip().lower()


def _sha_matches(actual_head_sha: str, expected_head_sha: str) -> bool:
    actual = str(actual_head_sha or "").strip().lower()
    expected = str(expected_head_sha or "").strip().lower()
    if not actual or not expected:
        return True
    return actual.startswith(expected) or expected.startswith(actual)
