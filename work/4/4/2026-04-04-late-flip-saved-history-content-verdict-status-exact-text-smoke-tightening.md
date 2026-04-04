# late-flip saved-history content-verdict-status exact-text smoke tightening

날짜: 2026-04-04

## 목표

late-flip scenario에서 saved-history `#response-content-verdict-status` assertion 1건(partial)을 exact-text `toHaveText(lateFlipSavedHistoryVerdictStatus)`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 353-354)
  - 기존:
    - `toContainText("이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.")`
  - 교체:
    - `const lateFlipSavedHistoryVerdictStatus = "이 답변 내용을 거절로 기록했습니다. 저장 승인 거절과는 별도입니다. 아래 수정본 기록이나 저장 요청은 계속 별도 흐름으로 사용할 수 있습니다. 이미 저장된 노트와 경로는 그대로 남고, 이번 내용 거절은 최신 판정만 바꿉니다.";`
    - `await expect(page.locator("#response-content-verdict-status")).toHaveText(lateFlipSavedHistoryVerdictStatus);`

## 변경하지 않은 것

- line 521의 corrected-save saved-history status partial
- rejected-verdict scenario line 378-379/396-397
- approval-preview assertions
- `#notice-box`, content-reason assertions
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `rg` 교차 확인: `#response-content-verdict-status` 참조 정합 확인
- `make e2e-test`: **17 passed (4.0m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## 잔여 리스크

- line 521의 corrected-save saved-history verdict status는 아직 partial이지만 별도 슬라이스 대상
