# 2026-04-20 Gemini Advisory: Milestone 4 Strong-tied-with-Strong tie-break (Option E1) 추천

## 상황 분석
- seq 423을 통해 재조사 쿼리 전체 상한(overall cap)이 4에서 5로 상향 조정되었습니다.
- 이제 Milestone 4의 마지막 후보군인 Option E(강력/약함/미해결 분리 정밀화)만 남았습니다.
- Option E 하위의 세 가지 후보(E1/E2/E3) 중 가장 시스템의 결정론적(deterministic) 정확도를 높이고 품질을 개선할 수 있는 것은 **E1 (Strong-tied-with-Strong tie-break)**입니다.

## 추천 결정
- **RECOMMEND: implement Option E1 (Milestone 4 Strong-tied-with-Strong tie-break)**
- **정확한 슬라이스:**
  - **정렬 키 변경 (Target behavior):** `_claim_sort_key`에서 `len(value)`(긴 값 우선) 대신 `-len(value)`(짧은 값 우선)을 사용하고, `source_url`을 최종 결정론적 타이브레이커로 추가.
  - **대상 파일 및 위치:**
    1. `core/web_claims.py:61`: `_claim_sort_key` 함수 수정.
    2. `core/agent_loop.py:4141`: `_entity_claim_sort_key` 미러 함수 수정 (항상 master와 동일하게 유지).
- **이유:**
  1. **사용자 가시적 개선 (Priority 2):** 엔티티 카드의 "개발", "장르"와 같은 슬롯은 서술형 문장보다 짧고 명확한 키워드(예: "펄어비스" vs "펄어비스는 한국의 게임 개발사이다")가 더 적합합니다. 짧은 값을 우선시함으로써 카드 정보의 가독성을 높입니다.
  2. **결정론적 정확도 향상 (New Quality Axis):** 동일한 지지 수와 우선순위를 가진 여러 클레임이 존재할 때, 입력 순서에 의존하지 않고 `source_url` 문자열 정렬을 통해 항상 동일한 `primary_claim`이 선택되도록 보장합니다.
  3. **Milestone 4 정밀화:** seq 420에서 `AUXILIARY`, `COMMUNITY`, `PORTAL`이 동일한 가중치(1)로 묶이면서 하위 티어에서의 타이브레이크 발생 확률이 높아졌습니다. 이에 대한 정밀한 처리가 현 시점에서 가장 효과적인 품질 개선입니다.

## 구현 상세
- **변경 내용:**
  ```python
  # (수정 전)
  return (record.support_count, priority, int(record.confidence * 1000), len(record.value), record.value)
  # (수정 후)
  return (record.support_count, priority, int(record.confidence * 1000), -len(record.value), record.value, record.source_url)
  ```
- **회귀 테스트:** `tests/test_smoke.py`에 `test_claims_sort_key_prefers_shorter_value_when_other_keys_tie` 추가. 동일한 support_count와 priority를 가진 두 클레임 중 글자 수가 적은 쪽이 primary로 선택되는지 확인.

## 검증 계획
- `python3 -m unittest tests.test_smoke -k claims`
- `python3 -m py_compile core/web_claims.py core/agent_loop.py tests/test_smoke.py`
- `git diff --check`
- (브라우저 가시적 문구 변경이 없으므로 Playwright는 제외)
