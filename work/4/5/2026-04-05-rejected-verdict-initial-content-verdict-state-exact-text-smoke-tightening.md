# rejected-verdict initial content-verdict-state exact-text smoke tightening

날짜: 2026-04-05

## 목표

rejected-verdict scenario의 initial `#response-content-verdict-state` assertion 1건을 exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 427)
  - 기존: `toContainText("최신 내용 판정은 원문 저장 승인입니다.")`
  - 교체: `toHaveText("최신 내용 판정은 원문 저장 승인입니다.")`

## 변경하지 않은 것

- line 342의 late-flip initial verdict-state (이미 exact-text)
- line 397의 rejected-verdict rejected-state timestamp-pattern
- line 511, 541의 corrected-save verdict-state
- cancel family, runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.3m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## accepted-as-is verdict-state exact-text family 상태

- line 342: late-flip initial ✓
- line 427: rejected-verdict initial ✓
- line 511, 541: corrected-save (아직 broad partial — 별도 슬라이스 대상)
