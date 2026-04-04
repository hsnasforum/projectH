# rejected-verdict post-reject content-verdict-state timestamp-pattern smoke tightening

날짜: 2026-04-04

## 목표

rejected-verdict post-reject branch의 `#response-content-verdict-state` assertion 1건을 anchored timestamp-pattern으로 강화합니다. 이로써 rejected-state timestamp-pattern family가 전체 닫혔습니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 396-397)
  - 기존: `toContainText("내용 거절 기록됨")`
  - 교체: `const postRejectVerdictStatePattern = /^내용 거절 기록됨 · .+$/;` + `toHaveText(postRejectVerdictStatePattern)`

## 변경하지 않은 것

- line 352-355의 late-flip saved-history assertions
- line 521-523의 corrected-save saved-history assertions
- approval-preview, restored state assertions
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (3.9m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## verdict-state timestamp-pattern family 완료 상태

- line 353: late-flip saved-history ✓
- line 397: rejected-verdict post-reject ✓
- line 522: corrected-save saved-history ✓
- 전체 rejected-state timestamp-pattern family 닫힘
