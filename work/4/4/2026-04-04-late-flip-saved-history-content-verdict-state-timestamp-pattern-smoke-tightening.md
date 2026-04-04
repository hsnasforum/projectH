# late-flip saved-history content-verdict-state timestamp-pattern smoke tightening

날짜: 2026-04-04

## 목표

late-flip scenario에서 saved-history `#response-content-verdict-state` assertion 1건(broad partial)을 anchored timestamp-pattern `toHaveText(/^내용 거절 기록됨 · .+$/)`로 강화합���다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 352-353)
  - 기존: `toContainText("내용 거절 기록됨")`
  - 교체: `const lateFlipVerdictStatePattern = /^내용 거절 기록됨 · .+$/;` + `toHaveText(lateFlipVerdictStatePattern)`

## 변경하지 않은 것

- line 395의 rejected-verdict post-reject verdict-state (broad partial)
- line 521-523의 corrected-save saved-history assertions
- cancel stabilization (line 909-911)
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `make e2e-test`: **17 passed (4.2m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## verdict-state timestamp-pattern family 상태

- line 353: late-flip saved-history (timestamp-pattern) ���
- line 521: corrected-save saved-history (timestamp-pattern) ✓
- line 395: rejected-verdict post-reject (아직 broad partial — 별도 슬라이스 대상)
