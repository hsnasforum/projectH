# late-flip initial content-verdict-state exact-text smoke tightening

날짜: 2026-04-04

## 목표

late-flip scenario의 initial `#response-content-verdict-state` assertion 1건을 exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 342)
  - 기존: `toContainText("최신 내용 판정은 원문 저장 승인입니다.")`
  - 교체: `toHaveText("최신 내용 판정은 원문 저장 승인입니다.")`

## 변경하지 않은 것

- line 352-353의 late-flip rejected-state timestamp-pattern
- line 427의 rejected-verdict initial verdict-state
- line 511, 541의 corrected-save verdict-state assertions
- cancel family, runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.0m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## 잔여 리스크

- line 427 (rejected-verdict), 511, 541 (corrected-save)의 verdict-state assertions는 아직 broad partial이지만 별도 슬라이스 대상
