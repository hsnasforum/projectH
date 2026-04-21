# 2026-04-20 G5-unskip-DEGRADED collision arbitration

## 요약
- `test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous` (:1012, DEGRADED 기대)와 `test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken` (:1062, BROKEN 기대) 사이의 실증적 충돌이 확인되었습니다.
- 두 테스트는 `supervisor_missing`, `runtime_state == "RUNNING"`, `watcher.alive` 부재/False, 활성 lane 존재라는 공통 신호를 공유합니다.
- 유일한 차별점은 `updated_at` 기준의 스냅샷 연령(10.0s vs 20.0s)뿐이며, 비-연령 기반의 narrow guard 시도는 실패(regression)로 끝났습니다.
- 이에 따라 `G5-unskip-DEGRADED_WITH_AGE-MACHINERY` 슬라이스를 통해 연령 기반 판정 로직을 도입할 것을 권고합니다.

## 권고 사항: G5-unskip-DEGRADED_WITH_AGE-MACHINERY 도입

### 1. 인프라 및 상수 도입
- `pipeline_gui/backend.py` 상단 임포트 수정:
  ```python
  from pipeline_runtime.schema import parse_iso_utc, read_jsonl_tail
  ```
- 상수 정의 (예: `DEFAULT_TOKEN_SINCE_DAYS` 근처):
  ```python
  SNAPSHOT_STALE_THRESHOLD = 15.0
  ```

### 2. normalize_runtime_status 로직 수정
- `supervisor_missing` 판정 후, `updated_at`을 파싱하여 `snapshot_age`를 계산합니다.
- `if supervisor_missing and runtime_state == "RUNNING":` (:136) 직전에 아래 `DEGRADED` 분기를 삽입합니다.

```python
        # snapshot_age computation (handle parse errors as fall-through)
        updated_at_str = str(status.get("updated_at") or "").strip()
        snapshot_age = None
        if updated_at_str:
            try:
                snapshot_age = time.time() - parse_iso_utc(updated_at_str)
            except (ValueError, TypeError, OverflowError):
                pass

        if (
            supervisor_missing
            and runtime_state == "RUNNING"
            and not watcher.get("alive")
            and any(str(lane.get("state") or "") != "OFF" for lane in lanes)
            and snapshot_age is not None
            and snapshot_age <= SNAPSHOT_STALE_THRESHOLD
        ):
            status["runtime_state"] = "DEGRADED"
            status["degraded_reason"] = "supervisor_missing_recent_ambiguous"
            status["degraded_reasons"] = ["supervisor_missing_recent_ambiguous"]
            # No lane rewrite; preserve current READY/WORKING states
            return status
```

### 3. 테스트 해제
- `tests/test_pipeline_gui_backend.py:1012` (`test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous`)의 `@unittest.skip` 데코레이터를 제거합니다.
- 다른 2개 DEGRADED 셀 (:1195, :1257)은 이 슬라이스에서 다루지 않으므로 skip 상태를 유지합니다.

## 기대 효과 및 리스크
- **효과:** 연령 기반의 명확한 임계치(15.0s)를 통해 최근 스냅샷과 노후된 스냅샷을 구분하고, `DEGRADED` 상태의 정확도를 높입니다.
- **리스크:** `parse_iso_utc`의 예외 처리를 누락할 경우 런타임 오류가 발생할 수 있으나, `try-except` 블록을 통해 안전하게 fall-through 하도록 설계했습니다.
