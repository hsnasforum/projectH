# 2026-04-20 Gemini Advisory: Milestone 4 Reinvestigation Trigger Threshold (Option D) 추천

## 상황 분석
- seq 420을 통해 Milestone 4의 Source Role Weighting(축 분리) 작업이 완료되었습니다.
- 이제 Milestone 4의 다음 후보인 Reinvestigation Trigger Threshold(D)와 Separation Polish(E) 중 하나를 선택해야 합니다.
- 시스템의 핵심 품질 지표인 "재조사 정확도 및 범위"를 개선하기 위해, 오랫동안 백로그에 머물러 있던 재조사 쿼리 상한(cap) 조정을 추천합니다.

## 추천 결정
- **RECOMMEND: implement Option D (Milestone 4 Reinvestigation Trigger Threshold)**
- **정확한 슬라이스:**
  - `core/agent_loop.py:3863`: 전체 재조사 쿼리 생성 상한을 `4`에서 `5`로 상향 조정.
  - (`if len(second_pass_queries) >= 4:` → `if len(second_pass_queries) >= 5:`)
- **이유:**
  1. **품질 개선 (Priority 3):** 현재 `CORE_ENTITY_SLOTS`는 5개(개발, 서비스/배급, 장르/성격, 상태, 이용 형태)이나, 재조사 쿼리는 4개로 제한되어 있어 모든 슬롯이 누락(MISSING)되거나 약한(WEAK) 상태일 때 최소 하나의 슬롯은 항상 재조사에서 소외되는 구조적 한계가 있습니다. 이를 5로 확장하여 모든 코어 슬롯에 대해 최소 1개의 재조사 기회를 부여합니다.
  2. **가장 명확한 슬라이스:** 단일 상수의 수치 조정이므로 모호함이 없으며, 기존 유닛 테스트 구조 내에서 즉시 검증 가능합니다.
  3. **우선순위 규칙 준수:** D와 E가 모두 pinnable할 경우, 백로그에 더 오래 머물렀던 D를 우선한다는 규칙을 적용했습니다.

## 구현 상세
- **대상 파일:** `core/agent_loop.py`
- **변경 지점:** `_build_entity_second_pass_queries` 함수 내의 종료 조건 (`:3863`).
- **회귀 테스트:** `tests/test_smoke.py`에 `test_coverage_reinvestigation_overall_cap_is_now_5` 추가. 5개 이상의 슬롯이 WEAK/MISSING 상태일 때 실제로 5개의 유니크한 쿼리가 생성되는지 확인.

## 검증 계획
- `python3 -m unittest tests.test_smoke -k reinvestigation`
- `python3 -m py_compile core/agent_loop.py tests/test_smoke.py`
- `git diff --check`
- (브라우저 가시적 변경이 없으므로 Playwright는 제외)
