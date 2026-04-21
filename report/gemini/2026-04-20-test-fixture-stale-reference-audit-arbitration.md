# 2026-04-20 Test fixture stale reference audit arbitration

## context
- seq 555 (`AXIS-EMIT-PAYLOAD-ENRICH-CONT`) 완료. `dispatch_selection` 6-key 페이로드가 완결됨.
- `tests/` 내에 `"# verify\n"` 및 `"# work\n"`와 같은 bare fixture들이 여전히 다수 존재함.
- 이들은 테스트의 가독성을 떨어뜨리고, 실제 `/work` 및 `/verify` 파일의 표준 형식(h1 header + structured sections)과 괴리가 있음.

## ambiguity resolution
- **후보**:
  1. `AXIS-STALE-REFERENCE-AUDIT` (테스트 fixture 정규화 및 cleanup)
  2. `AXIS-G7-AUTONOMY-PRODUCER` (defensive gate 활성화)
  3. `AXIS-DISPATCHER-TRACE-BACKFILL` (empirical trace 확인)
- **결정**: `AXIS-STALE-REFERENCE-AUDIT`를 우선합니다.
- **이유**: `internal cleanup` 우선순위에 따라, 방치된 bare fixture들을 정리하여 테스트 suite의 신뢰도와 유지보수성을 높이는 것이 현재 가장 깔끔한 다음 slice입니다. 특히 `latest_verify_note_for_work` 관련 테스트들이 실제 파일 형식에 더 가깝게 구성되도록 유도합니다.

## recommendation
- **RECOMMEND: implement AXIS-STALE-REFERENCE-AUDIT sweep**
- **대상 파일**: `tests/test_pipeline_runtime_schema.py`, `tests/test_pipeline_runtime_supervisor.py`
- **세부**:
  - `rg -n '"# verify\\n"|# work\\n"' tests/` 결과를 바탕으로 bare fixture들을 스캔합니다.
  - `tests/test_pipeline_runtime_schema.py:403, 432, 478` 등의 `"# verify\n"`를 최소한의 유효한 `/verify` 형식(예: `# 2026-04-20 verify\n\n## 변경 파일\n`)으로 교체합니다.
  - `tests/test_pipeline_runtime_supervisor.py:1356` 등의 픽스처도 같은 방식으로 보강합니다.
  - `"# work\n"` 픽스처(예: `tests/test_pipeline_runtime_schema.py:368`)도 최소한의 유효한 `/work` 형식으로 맞춥니다.
  - 이 과정에서 `latest_verify_note_for_work` 로직이 오동작하지 않는지 확인하는 회귀 테스트가 됩니다.
