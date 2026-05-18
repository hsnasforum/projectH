# 2026-05-08 M122 Axis 1 multi-source agreement

## 변경 파일

- `core/agent_loop.py`
- `core/web_claims.py`
- `tests/test_smoke.py`
- `work/5/8/2026-05-08-m122-axis1-multiSource-agreement.md`

## 사용 skill

- `investigation-quality-audit`: entity-card 웹 조사 source agreement 점수와 claim coverage STRONG 판정 변경의 영향 범위, 불확실성 표면화, 회귀 테스트 축을 점검했다.
- `security-gate`: 변경이 외부 web investigation 경로에 닿지만 읽기 전용/permission-gated/logged 경계를 바꾸지 않는지 확인했다.
- `work-log-closeout`: 구현 라운드 종료 기록의 필수 섹션, 실제 검증, 남은 리스크 정리에 사용했다.

## 변경 이유

- entity-card 웹 조사에서 단일 저신뢰 peer나 비신뢰 source support가 다중 소스 합의처럼 작동해 source selection 또는 STRONG coverage를 과하게 끌어올리는 경로를 줄이기 위해 변경했다.
- 핵심 기준은 trusted peer 또는 trusted supporter가 없는 label/source 합의가 단독으로 강한 검증 상태에 기여하지 않게 하는 것이다.

## 핵심 변경

- `AgentLoop._entity_source_fact_agreement_score()`에서 `trust_score_by_index`가 없거나 trust score 4 이상 peer가 없는 label은 agreement score에 기여하지 않도록 했다.
- agreement score의 다중 peer 보너스와 label 폭 보너스는 trust score 4 이상 peer가 있는 label/peer만 기준으로 계산하게 했다.
- `summarize_slot_coverage()`의 STRONG 조건을 `trusted_source_count >= 2`로 단순화해 raw `support_count`가 비신뢰 source를 포함해도 STRONG을 만들지 못하게 했다.
- `tests/test_smoke.py`에 trusted 1개 + untrusted 2개는 WEAK, trusted 2개 합의는 STRONG, trusted 2개 합의와 competing trusted claim은 CONFLICT인 회귀 테스트를 추가했다.
- `tests/test_smoke.py`에 low-trust peer label agreement가 `_entity_source_fact_agreement_score()`에 기여하지 않는 회귀 테스트를 추가했다.

## 검증

- `python3 -m py_compile core/agent_loop.py core/web_claims.py`
  - PASS.
- `python3 -m unittest -v tests.test_smoke.SmokeTest.test_summarize_slot_coverage_mixed_trust_requires_two_trusted_supporters tests.test_smoke.SmokeTest.test_entity_source_fact_agreement_score_requires_trusted_peer`
  - PASS: 신규 회귀 테스트 2개 통과. 첫 테스트 안에서 handoff의 케이스 A/B/C를 직접 확인했다.
- `python3 -m unittest -v tests.test_smoke`
  - PASS: 152개 테스트 통과.
- `git diff --check -- core/agent_loop.py core/web_claims.py tests/test_smoke.py`
  - PASS: 출력 없음.

## 남은 리스크

- entity-card source selection에서 trust score 4 미만 peer 합의가 더 이상 agreement score에 기여하지 않으므로, 일부 저신뢰 source가 이전보다 덜 선택될 수 있다. 이는 이번 M122 목표인 단일 저신뢰 합의 억제와 일치한다.
- latest-update, retry/reload, UI 렌더링, 저장 record schema, 승인 흐름은 수정하지 않았다.
- web investigation은 계속 read-only, permission-gated, locally logged 경계 안에 있으며 외부 fetch/search 동작 자체는 바꾸지 않았다.
- handoff 범위상 product docs와 frontend/E2E는 수정하지 않았다. 사용자-visible label이나 UI 구조 변경이 아니라 내부 ranking/coverage 판정 변경으로 판단했다.
