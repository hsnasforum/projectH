# 2026-04-20 Observability payload enrichment continuation arbitration

## context
- seq 552 (`AXIS-EMIT-PAYLOAD-ENRICH`) 완료. `dispatch_selection` 이벤트에 `date_key` (work-side) 한 키가 성공적으로 추가됨.
- `_build_artifacts`의 다른 유용한 메타데이터(`mtime`, verify-side `date_key`)는 아직 이벤트 페이로드에 노출되지 않음.
- G7-family는 이미 포화(saturated)되었으므로, 현재 시작된 observability 보강 축을 완결하는 것이 가장 coherent한 다음 단계임.

## ambiguity resolution
- **후보**:
  1. `AXIS-EMIT-PAYLOAD-ENRICH-CONT` (observability 완결)
  2. `AXIS-G7-AUTONOMY-PRODUCER` (defensive gate 활성화)
  3. `AXIS-STALE-REFERENCE-AUDIT` (cleanup)
- **결정**: `AXIS-EMIT-PAYLOAD-ENRICH-CONT`를 우선합니다.
- **이유**: `same-family current-risk reduction` 및 coherence 원칙에 따라, 시작한 observability enrichment 작업을 마무리하여 `dispatch_selection` 이벤트가 downstream consumer에게 필요한 모든 시각(mtime)과 식별자(date_key)를 온전하게 제공하도록 합니다. 이는 brittle parsing을 완전히 제거하고, 향후 verify-lane에서의 자동화된 monotonic check 등을 위한 견고한 토대가 됩니다.

## recommendation
- **RECOMMEND: implement AXIS-EMIT-PAYLOAD-ENRICH-CONT**
- **대상 파일**: `pipeline_runtime/supervisor.py`, `tests/test_pipeline_runtime_supervisor.py`
- **세부**:
  - `pipeline_runtime/supervisor.py:_build_artifacts`에서 `dispatch_selection` 이벤트 페이로드를 3-key에서 6-key로 확장합니다.
  - 추가 키: `latest_work_mtime`, `latest_verify_date_key`, `latest_verify_mtime`.
  - `latest_verify_date_key`는 `verify_rel`이 `"—"`면 `""`, 아니면 `Path(verify_rel).name[:10]`으로 산출합니다.
  - mtime 값들은 `work_mtime`, `verify_mtime`을 그대로 사용합니다.
  - `tests/test_pipeline_runtime_supervisor.py`에서 seq 533 sibling equality(`:335-342`)와 seq 543 monotonic test(`:388-393` additive loop)를 새 6-key 페이로드 형계에 맞춰 갱신합니다.
