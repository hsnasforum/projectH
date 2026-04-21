# 2026-04-20 G5-unskip-DEGRADED_WATCHER_ONLY arbitration

## 요약
- `DEGRADED` 패밀리의 다음 단계로 `test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous` (:1257) 해제를 권고합니다.
- 이 테스트는 `watcher.alive == True`이지만 `watcher.pid`가 부재한 "watcher-only alive" 상태를 다루며, 기대하는 `degraded_reason`이 기존에 해제된 `:1012`와 동일한 `"supervisor_missing_recent_ambiguous"`입니다.
- 따라서 새로운 탑레벨 분기를 추가하는 대신, 기존의 `DEGRADED` 분기(:141)의 조건을 확장하여 두 케이스를 통합 처리하는 방식이 가장 효율적입니다.

## 권고 사항: G5-unskip-DEGRADED_WATCHER_ONLY (기존 분기 확장)

### 1. normalize_runtime_status 조건 확장
- `pipeline_gui/backend.py:141` 부근의 `DEGRADED` 분기 조건을 아래와 같이 수정합니다.

```python
        if (
            supervisor_missing
            and runtime_state == "RUNNING"
            and snapshot_age is not None
            and snapshot_age <= SNAPSHOT_STALE_THRESHOLD
            and (
                (not watcher.get("alive") and any(str(lane.get("state") or "") != "OFF" for lane in lanes))
                or (watcher.get("alive") and not watcher.get("pid"))
            )
        ):
            status["runtime_state"] = "DEGRADED"
            status["degraded_reason"] = "supervisor_missing_recent_ambiguous"
            status["degraded_reasons"] = ["supervisor_missing_recent_ambiguous"]
            return status
```

### 2. 판정 로직 근거 (Collision Check)
- **`:1012` (기존 통과):** `watcher` 부재 (falsy) + 활성 lane 존재 -> 첫 번째 서브 조건 `(not watcher.get("alive") and any(...))`에 의해 `DEGRADED` 유지.
- **`:1257` (신규 해제):** `watcher.alive == True` + `watcher.pid == None` -> 두 번째 서브 조건 `(watcher.get("alive") and not watcher.get("pid"))`에 의해 `DEGRADED`로 진입.
- **`:865` (counterpart):** `watcher.alive == True` + `watcher.pid == 4242` -> 두 서브 조건 모두 `False`이므로 `DEGRADED`를 건너뛰고 기존처럼 `BROKEN`으로 진행 (정상).
- **`:1062` (aged):** `snapshot_age > 15.0`이므로 진입 불가. 기존처럼 `BROKEN` 유지 (정상).

### 3. 테스트 해제
- `tests/test_pipeline_gui_backend.py:1257` (`test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous`)의 `@unittest.skip` 데코레이터를 제거합니다.
- `:1195` (undated)는 `degraded_reason`이 다르므로 이번 슬라이스에서는 skip 상태를 유지합니다.

## 기대 효과 및 리스크
- **효과:** 분기 폭발(branch explosion)을 방지하면서 동일한 semantic을 가진 두 `DEGRADED` 시나리오를 통합 관리할 수 있습니다.
- **리스크:** `watcher.get("pid")`가 빈 문자열(`""`)인 경우도 `not`에 의해 처리되므로, fixture의 다양성에 안전하게 대응할 수 있습니다.
