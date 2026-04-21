# 2026-04-20 G-axis fifth slice prioritization

## 개요
- seq 450(G2-deferred-A)을 통해 비포커스 STRONG+mixed-trust 슬롯이 요약 문장에 반영됨.
- 현재 포커스 슬롯이 STRONG+mixed-trust인 상태에서 랭크 변화가 없는 경우(steady STRONG), 요약 문장이 포커스 슬롯의 품질 정보를 누락하고 비포커스 요약으로 넘어가는 공백이 남아 있음.
- 이를 해결하기 위한 G2-deferred-B 슬라이스를 선정하여 "Indicator Consumption" 사이클을 완결하고자 함.

## 판단
1. **same-family current-risk reduction (우선순위 1):**
   - 사용자가 특정 슬롯을 재조사(focus)했는데, 그 결과가 여전히 STRONG이지만 소스 신뢰도가 낮음(mixed)을 알려주지 않는 것은 정보 누락임.
   - G2-deferred-B를 통해 포커스 슬롯의 "steady STRONG + mixed trust" 케이스를 위한 전용 문장을 추가함으로써, 사용자가 재조사 결과를 명확히 인지하게 함.

2. **지표 소비 사이클의 완결성:**
   - G2(plurality), G1(trust_tier UI), G2-followup(summary focus-WEAK/focus-improved-STRONG/non-focus WEAK), G2-deferred-A(non-focus STRONG-mixed)가 모두 완료됨.
   - G2-deferred-B는 이 흐름의 마지막 조각으로, 이를 통해 `_build_claim_coverage_progress_summary`가 모든 유의미한 신뢰도 조합을 정직하게 반영하게 됨.

3. **기타 후보 검토:**
   - **G3..G8:** 기능적 대칭성(Symmetry)이 확보된 후 튜닝(G3/G4)이나 테스트 수정(G5/G6)으로 넘어가는 것이 프로젝트 관리 측면에서 가장 깔끔함.
   - **G9 (Naming Cleanup):** seq 450에서 발견된 이름 충돌 문제는 위험도가 낮으며, 현재 기능적 진척보다 우선순위가 떨어짐.

## 권고 (RECOMMEND)
- **G2-deferred-B: focus-slot steady STRONG mixed-trust surfacing**
- 구체적 범위:
  - `core/agent_loop.py::_build_claim_coverage_progress_summary` 수정.
  - 세 개의 포커스 루프(improved, regressed, unresolved)가 끝난 지점(`:4584` 부근)과 비포커스 요약 시작점(`:4586` 부근) 사이에 신규 포커스 가드 추가.
  - `focus_slot`의 현재 상태가 `STRONG`이고 `current_trust_tier_map`에서 `"mixed"`인 경우, 전용 문장 반환: `"재조사했지만 {slot}{focus_particle} 교차 확인 기준은 충족하지만 공식/위키/데이터 소스가 약합니다."`
  - `tests/test_smoke.py`에 steady STRONG + mixed-trust 포커스 슬롯 요약 검증 추가.

## 결론
G2-deferred-B를 구현함으로써 Claim Coverage 지표 고도화의 서버 사이드 요약 반영 작업을 최종 완결하는 것을 추천함.
