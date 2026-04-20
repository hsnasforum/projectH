# 2026-04-20 Gemini Advisory: Milestone 4 Source Role Weighting (Option C) 추천

## 상황 분석
- seq 417을 통해 `CONFLICT` 체인의 E2E 검증이 Playwright 시나리오로 고정되었습니다. 이로써 `CONFLICT` 관련 표면(surface)은 모두 포화(saturated) 상태가 되었습니다.
- 이제 Milestone 4의 다음 단계로 새로운 품질 축(quality axis)으로의 전환이 필요합니다.
- 후보군(C/D/E) 중 가장 우선순위가 높고 명확하게 정의 가능한 것은 **Source Role Weighting (C)**입니다. 특히 현재 `COMMUNITY`, `PORTAL`, `BLOG`가 모두 가중치 `0`으로 묶여 있는 "0-tier"를 분리하는 작업이 오랫동안 제기된 과제입니다.

## 추천 결정
- **RECOMMEND: implement Option C (Milestone 4 Source Role Weighting)**
- **정확한 슬라이스(Permutation):**
  - `SourceRole.PORTAL`: 0 → 1
  - `SourceRole.COMMUNITY`: 0 → 1
  - `SourceRole.BLOG`: 0 (유지)
  - (참고: `SourceRole.AUXILIARY`는 1로 유지되어 PORTAL/COMMUNITY와 같은 티어가 됩니다.)
- **이유:**
  1. **가장 명확한 Milestone 4 후보:** 0/0/0 티어의 결합도는 시스템의 초기 설계부터 존재했던 "soft edge"이며, 이를 분리함으로써 개인 블로그(BLOG)를 커뮤니티(COMMUNITY)나 포털(PORTAL)보다 낮은 우선순위로 배치하는 사용자 가시적 개선을 이룰 수 있습니다.
  2. **수치적 경계의 명확성:** 상위 티어(NEWS: 2, DESCRIPTIVE: 3 등)를 건드리지 않고 하위 0/1 영역에서만 이동하므로 기존 시스템의 안정성을 해치지 않습니다.
  3. **검증의 용이성:** `summarize_slot_coverage`의 가중치 기반 Tie-break를 확인하는 유닛 테스트만으로도 충분히 검증 가능합니다.

## 구현 상세
- **대상 파일:**
  1. `core/web_claims.py`: `_ROLE_PRIORITY` 맵 수정.
  2. `core/agent_loop.py`: 두 곳의 하드코딩된 미러 맵(`_ROLE_PRIORITY`와 동일하게) 수정.
  3. `tests/test_smoke.py`: 새로운 회귀 테스트 추가.
- **회귀 테스트 요건:**
  - `SourceRole.PORTAL`과 `SourceRole.BLOG` 출처의 클레임이 같은 support_count를 가질 때, `PORTAL`이 primary_claim으로 선택되는지 확인.
  - `SourceRole.COMMUNITY`와 `SourceRole.BLOG` 사이에서도 동일한 우선순위 확인.
  - `SourceRole.PORTAL`과 `SourceRole.AUXILIARY`는 동일 티어(1)로 유지됨을 확인.

## 검증 계획
- `python3 -m unittest tests.test_smoke -k claims`
- `python3 -m py_compile core/web_claims.py core/agent_loop.py tests/test_smoke.py`
- `git diff --check`
- (브라우저 가시적 문구 변경이 없으므로 Playwright는 제외)
