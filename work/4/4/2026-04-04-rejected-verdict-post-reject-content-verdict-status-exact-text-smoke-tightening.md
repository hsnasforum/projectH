# rejected-verdict post-reject content-verdict-status exact-text smoke tightening

날짜: 2026-04-04

## 목표

rejected-verdict scenario에서 post-reject `#response-content-verdict-status` assertion 2건(partial)을 1건의 exact-text `toHaveText(postRejectVerdictStatus)`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 395-396)
  - 기존 두 줄:
    - `toContainText("이 답변 내용을 거절로 기록했습니다.")`
    - `toContainText("이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.")`
  - 교체:
    - `const postRejectVerdictStatus = "이 답변 내용을 거절로 기록했습니다. 저장 승인 거절과는 별도입니다. 아래 수정본 기록이나 저장 요청은 계속 별도 흐름으로 사용할 수 있습니다. 이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.";`
    - `await expect(page.locator("#response-content-verdict-status")).toHaveText(postRejectVerdictStatus);`

## 변경하지 않은 것

- line 353, 520의 saved-history status partials
- line 377-378의 initial status exact check
- line 379-409의 approval-preview assertions
- `#notice-box`, content-reason assertions
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `rg` 교차 확인: `#response-content-verdict-status` 참조 정합 확인
- `make e2e-test`: **17 passed (3.6m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## 잔여 리스크

- line 353, 520의 saved-history verdict status는 아직 partial이지만 별도 슬라이스 대상 (saved-history branch 조건 포함)
