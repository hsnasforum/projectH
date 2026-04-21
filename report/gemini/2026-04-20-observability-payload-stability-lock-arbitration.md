# 2026-04-20 Observability payload stability lock arbitration

## context
- seq 564 (`AXIS-G7-AUTONOMY-PRODUCER-EXTEND`) 완료. reachable `visible_mode` 4종에 대해 canonical `decision_class` 기본값이 완비됨.
- seq 552/555를 통해 `dispatch_selection` 이벤트 페이로드가 6-key 형계로 확장됨.
- 현재 G7 및 EMIT-PAYLOAD 축은 기능적으로 포화(saturated) 상태이며, 이제 이 형계를 테스트 레이어에서 명시적으로 잠가(lock) 향후의 의도치 않은 변형을 방지할 시점임.

## ambiguity resolution
- **후보**:
  1. `AXIS-EMIT-KEY-STABILITY-LOCK` (6-key 페이로드 형계 및 순서 고정)
  2. `AXIS-AUTONOMY-KEY-STABILITY-LOCK` (분류기 반환 키셋 및 기본값 불변 고정)
  3. `AXIS-DISPATCHER-TRACE-BACKFILL` (실제 trace 확인 예약)
- **결정**: `AXIS-EMIT-KEY-STABILITY-LOCK`를 우선합니다.
- **이유**: `same-family current-risk reduction` 원칙에 따라, 최근 여러 라운드에 걸쳐 확장된 observability 페이로드를 가장 먼저 보호합니다. `dispatch_selection` 이벤트의 키 순서와 개수를 명시적으로 확인하는 테스트를 추가함으로써, downstream consumer(handoff 파싱 로직 등)가 기대하는 인터페이스의 안정성을 보장합니다. 이는 최근의 "recursive improvement" 흐름을 "stability lock"으로 마무리하는 논리적인 단계입니다.

## recommendation
- **RECOMMEND: implement AXIS-EMIT-KEY-STABILITY-LOCK**
- **대상 파일**: `tests/test_pipeline_runtime_supervisor.py`
- **세부**:
  - `tests/test_pipeline_runtime_supervisor.py`에 `test_dispatch_selection_payload_key_stability` 메서드를 추가합니다.
  - 이 테스트는 `_build_artifacts()` 호출 후 생성된 `dispatch_selection` 이벤트의 페이로드를 읽어 다음을 검증합니다:
    1. 키의 총 개수가 정확히 6개인지 확인.
    2. `list(payload)`를 통해 키의 순서가 `['latest_work', 'latest_verify', 'date_key', 'latest_work_mtime', 'latest_verify_date_key', 'latest_verify_mtime']`와 정확히 일치하는지 확인.
  - 기존 99개 테스트의 green baseline을 유지하며 총 100개 테스트를 목표로 합니다.
