# corrected-save saved-history content-verdict-state exact-text smoke tightening

날짜: 2026-04-05

## 목표

corrected-save saved-history branch의 `#response-content-verdict-state` assertion 마지막 1건을 exact-text로 강화합니다. 이로써 `response-content-verdict-state` family의 모든 broad partial이 닫혔습니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 544)
  - 기존: `toContainText("최신 내용 판정은 기록된 수정본입니다.")`
  - 교체: `toHaveText("최신 내용 판정은 기록된 수정본입니다.")`

## 변경하지 않은 것

- 주변 assertions (notice-box, response-quick-meta-text, response-content-reason-box)
- search-only family, cancel family
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.3m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test를 생략합니다.

## response-content-verdict-state family 전체 완료 상태

exact-text:
- line 342: late-flip initial ✓
- line 427: rejected-verdict initial ✓
- line 511: corrected-save initial ✓
- line 544: corrected-save saved-history ✓

timestamp-pattern:
- line 353: late-flip saved-history ✓
- line 397: rejected-verdict post-reject ✓
- line 523: corrected-save saved-history rejected ✓

전체 family 닫힘.
