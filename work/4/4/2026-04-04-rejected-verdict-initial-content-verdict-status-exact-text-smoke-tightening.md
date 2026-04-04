# rejected-verdict initial content-verdict-status exact-text smoke tightening

날짜: 2026-04-04

## 목표

rejected-verdict scenario에서 initial `#response-content-verdict-status` assertion 2건(partial)을 1건의 exact-text `toHaveText(initialVerdictStatus)`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 377-378)
  - 기존 두 줄:
    - `toContainText("저장 승인 거절과는 별도입니다.")`
    - `toContainText("이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.")`
  - 교체:
    - `const initialVerdictStatus = "저장 승인 거절과는 별도입니다. 이 버튼을 누르면 grounded-brief 원문 응답에 내용 거절을 즉시 기록합니다. 이미 열린 저장 승인 카드는 그대로 유지되며 자동 취소되지 않습니다.";`
    - `await expect(page.locator("#response-content-verdict-status")).toHaveText(initialVerdictStatus);`

## 변경하지 않은 것

- line 395-396의 post-reject status partials
- line 353, 520의 saved-history status partials
- line 379-409의 approval-preview assertions
- `#notice-box`, content-reason assertions
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `rg` 교차 확인: `#response-content-verdict-status` 참조 정합 확인
- `make e2e-test`: **17 passed (3.8m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## 잔여 리스크

- line 395-396의 post-reject verdict status도 아직 partial이지만 별도 슬라이스 대상
