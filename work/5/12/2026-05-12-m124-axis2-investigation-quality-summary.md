# 2026-05-12 M124 Axis 2 investigation quality summary

## 변경 파일

- `core/web_claims.py`
- `core/agent_loop.py`
- `tests/test_smoke.py`
- `work/5/12/2026-05-12-m124-axis2-investigation-quality-summary.md`

## 사용 skill

- `investigation-quality-audit`: entity-card 조사 품질 관찰 필드가 기존 claim coverage 불확실성, 출처 ranking, reload 흐름을 바꾸지 않는지 범위를 점검했습니다.
- `work-log-closeout`: 지정된 `/work` closeout 형식으로 변경 파일, 검증, 남은 리스크를 기록했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md` CONTROL_SEQ 1605의 M124 Axis 2 지시를 실행했습니다.
- entity-card 웹 조사 응답에서 슬롯별 status 카운트를 `AgentResponse.investigation_quality_summary`로 확인할 수 있게 하기 위한 변경입니다.

## 핵심 변경

- `core/web_claims.py`에 `compute_investigation_quality_summary()`를 추가해 `STRONG`, `WEAK`, `CONFLICT`, `UNRESOLVED`, `MISSING` 상태별 슬롯 수를 계산하도록 했습니다.
- `core/agent_loop.py`의 `AgentResponse`에 `investigation_quality_summary` 선택 필드를 추가했습니다.
- entity-card primary 웹 조사 응답 경로에서만 `entity_core_coverage` 기반 `investigation_quality_summary`를 계산해 `AgentResponse`에 연결했습니다.
- `tests/test_smoke.py`에 status 혼합 케이스와 all-STRONG 케이스 회귀 테스트 2개를 추가했습니다.
- 기존 `claim_coverage`, `claim_coverage_progress_summary`, source ranking, retry/reload 저장 로직은 변경하지 않았습니다.

## 검증

- PASS: `python3 -m py_compile core/web_claims.py core/agent_loop.py`
- PASS: `python3 -m unittest -v tests.test_smoke.SmokeTest.test_m124_compute_investigation_quality_summary_counts_correctly tests.test_smoke.SmokeTest.test_m124_compute_investigation_quality_summary_all_strong`
- PASS: `python3 -m unittest -v tests.test_smoke` (166 tests)
- PASS: `git diff --check -- core/web_claims.py core/agent_loop.py tests/test_smoke.py`

## 남은 리스크

- 이번 slice는 backend `AgentResponse` 필드와 helper/test 추가로 한정했습니다. serializer, storage schema, frontend, docs는 handoff 금지 범위라 수정하지 않았습니다.
- Browser/E2E는 실행하지 않았습니다. UI 계약 변경 없이 smoke unittest로 helper와 기존 web investigation 회귀를 확인했습니다.
- M124 Axis 2 publish bundle은 아직 미수행 상태이며 operator 결정 이후 별도 follow-up 대상입니다.
