# corrected-save saved-history content-verdict-status exact-text smoke tightening

날짜: 2026-04-04

## 목표

corrected-save scenario에서 saved-history `#response-content-verdict-status` assertion 1건(partial)을 exact-text `toHaveText(correctedSaveSavedHistoryVerdictStatus)`로 강화합니다. 이로써 `#response-content-verdict-status` family의 모든 assertion이 exact-text로 닫혔습니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 521-522)
  - 기존:
    - `toContainText("이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.")`
  - 교체:
    - `const correctedSaveSavedHistoryVerdictStatus = "이 답변 내용을 거절로 기록했습니다. 저장 승인 거절과는 별도입니다. 아래 수정본 기록이나 저장 요청은 계속 별도 흐름으로 사용할 수 있습니다. 이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.";`
    - `await expect(page.locator("#response-content-verdict-status")).toHaveText(correctedSaveSavedHistoryVerdictStatus);`

## 변경하지 않은 것

- line 517-520, 523의 주변 assertions (`#notice-box`, `#response-quick-meta-text`, `#response-content-verdict-state`, reason-box)
- rejected-verdict scenario (line 378-379, 396-397)
- late-flip scenario (line 353-354)
- approval-preview assertions
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `rg` 교차 확인: `#response-content-verdict-status` 참조 정합 — 모든 4건이 exact-text
- `make e2e-test`: **17 passed (4.0m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## family 완료 상태

`#response-content-verdict-status` exact-text family 전체 닫힘:
- line 354: late-flip saved-history (exact)
- line 379: rejected-verdict initial (exact)
- line 397: rejected-verdict post-reject (exact)
- line 522: corrected-save saved-history (exact)
