# 2026-04-20 Dispatcher trace empirical backfill arbitration

## context
- seq 570 (`AXIS-AUTONOMY-KEY-STABILITY-LOCK`) 완료. `dispatch_selection` 페이로드와 `classify_operator_candidate` 산출물의 형계(shape) 및 불변성(invariant)이 테스트 레이어에서 모두 잠겼습니다.
- G7 family 및 observability enrichment 축은 테스트 관점에서 포화(saturated) 상태입니다.
- 이제 다음 성숙도 단계로, 테스트 레이어의 잠금이 실제 런타임 `events.jsonl` 출력으로 정확히 이어지는지 실증적으로(empirically) 확인할 시점입니다.

## ambiguity resolution
- **후보**:
  1. `AXIS-DISPATCHER-TRACE-BACKFILL` (실제 trace 실증 확인)
  2. `AXIS-G4` (role_confidence community 갭 분석)
  3. `AXIS-G5-DEGRADED-BASELINE` (문서 동기화)
- **결정**: `AXIS-DISPATCHER-TRACE-BACKFILL`를 우선합니다.
- **이유**: `same-family current-risk reduction` 및 `recursive improvement` 원칙에 따라, 최근 여러 라운드에 걸쳐 강화된 observability 구조가 실제 운영 환경에서도 진실하게(truthful) 작동함을 보장합니다. 이는 seq 542 typo incident에서 시작된 recursive 개선 사이클을 완결하는 실질적인 최종 단계입니다.

## recommendation
- **RECOMMEND: implement AXIS-DISPATCHER-TRACE-BACKFILL**
- **대상**: verify-lane (코드 수정 없음, 검증 지침 하달)
- **세부 지침**:
  - **검증 시점**: 다음 real dispatcher cycle이 완료되고, 현재 실행 중인 `.pipeline/runs/<run_id>/events.jsonl` 파일에 `dispatch_selection` 유형의 이벤트가 2개 이상 기록된 직후 실행합니다.
  - **검증 파일**: `verify/4/20/2026-04-20-dispatcher-trace-backfill-verification.md`
  - **검증 항목 (grep/jq 사용)**:
    1. **Monotonicity**: `date_key` 값이 이벤트 순서에 따라 단조 비감소(monotonic non-decreasing)하는지 확인.
    2. **Consistency**: `payload["date_key"] == Path(payload["latest_work"]).name[:10]` 관계가 유지되는지 확인.
    3. **Sentinel**: `latest_verify`가 `"—"`일 때 `latest_verify_date_key`가 `""`, `latest_verify_mtime`이 `0.0`인지 확인.
    4. **Stability**: 페이로드의 키 순서와 개수(6개)가 seq 567 lock과 일치하는지 확인.
    5. **Autonomy**: `control_changed` 등 autonomy 관련 이벤트가 발생했다면, `decision_class`가 `SUPPORTED_DECISION_CLASSES` 내에 있거나 빈 문자열인지 확인.
