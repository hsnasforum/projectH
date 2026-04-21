# 2026-04-20 G5-unskip-DEGRADED_UNDATED arbitration

## 요약
- `DEGRADED` 패밀리의 마지막 미해결 테스트인 `test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded` (:1194) 해제를 권고합니다.
- 이 테스트는 `updated_at`이 부재한(undated) 스냅샷에서도 활성 surface(`watcher.alive == True` 및 `lanes[0].state == "READY"`)가 있다면 `DEGRADED`로 판정할 것을 요구합니다.
- 기존의 `DEGRADED` 분기를 다시 한 번 확장하여 `snapshot_age is None`인 경우를 포함하고, 본문에서 `degraded_reason`을 조건부로 스위칭하는 방식이 branch 개수 증가를 막는 가장 깔끔한 경로입니다.
- 이 슬라이스를 마지막으로 G5 패밀리가 완결되며, 이후에는 복잡해진 5개 분기를 정리하는 **G12 refactor**를 우선순위로 권장합니다.

## 권고 사항: G5-unskip-DEGRADED_UNDATED (기존 분기 및 본문 확장)

### 1. normalize_runtime_status 로직 수정
- `pipeline_gui/backend.py:141` 부근의 `DEGRADED` 분기 guard와 body를 아래와 같이 수정합니다.

```python
        if (
            supervisor_missing
            and runtime_state == "RUNNING"
            and (snapshot_age is None or snapshot_age <= SNAPSHOT_STALE_THRESHOLD)
            and (
                (
                    not watcher.get("alive")
                    and any(str(lane.get("state") or "") != "OFF" for lane in lanes)
                )
                or (
                    watcher.get("alive")
                    and not watcher.get("pid")
                )
            )
        ):
            reason = (
                "supervisor_missing_snapshot_undated"
                if snapshot_age is None
                else "supervisor_missing_recent_ambiguous"
            )
            status["runtime_state"] = "DEGRADED"
            status["degraded_reason"] = reason
            status["degraded_reasons"] = [reason]
            return status
```

### 2. 판정 로직 근거 (Collision Check)
- **`:1194` (신규 해제):** `snapshot_age is None` (undated) + `watcher.alive == True` + `not watcher.pid` -> `DEGRADED` 진입, `reason`은 `undated`용 리터럴로 설정됨 (정상).
- **`:1012`, `:1257` (기존 unskip):** `snapshot_age <= 15.0` -> `DEGRADED` 진입, `reason`은 기존처럼 `recent_ambiguous`로 설정됨 (정상).
- **`:1062` (aged):** `snapshot_age > 15.0`이므로 `snapshot_age is None`도 아니고 threshold 이하도 아님 -> 진입 불가, `BROKEN` 유지 (정상).

### 3. 테스트 해제
- `tests/test_pipeline_gui_backend.py:1194` (`test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded`)의 `@unittest.skip` 데코레이터를 제거합니다.

## 기대 효과 및 차기 슬라이스 제안
- **효과:** `DEGRADED` 패밀리의 모든 테스트(3개)가 unskip되어 green으로 유지됩니다.
- **차기 권고 (G12):** `normalize_runtime_status` 내의 분기 로직(STOPPING, BROKEN, DEGRADED, RUNNING→BROKEN, Quiescent)이 중복 코드와 복잡한 가드로 가득 찼습니다. 다음 라운드에서는 이들을 `_apply_shutdown_shape`와 같은 공유 헬퍼로 리팩토링하여 유지보수성을 확보할 것을 강력히 권고합니다.
