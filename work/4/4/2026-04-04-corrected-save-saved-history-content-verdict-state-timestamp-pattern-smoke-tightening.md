# corrected-save saved-history content-verdict-state timestamp-pattern smoke tightening

날짜: 2026-04-04

## 목표

corrected-save scenario에서 saved-history `#response-content-verdict-state` assertion 1건(broad partial)을 anchored timestamp-pattern `toHaveText(/^내용 거절 기록됨 · .+$/)`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 520-521)
  - 기존:
    - `toContainText("내용 거절 기록됨")`
  - 교체:
    - `const correctedSaveVerdictStatePattern = /^내용 거절 기록됨 · .+$/;`
    - `await expect(page.locator("#response-content-verdict-state")).toHaveText(correctedSaveVerdictStatePattern);`

## 근거

- runtime `app/static/app.js:1765-1766`에서 `latestContentVerdictRecordedAt`이 있으면 `내용 거절 기록됨 · {formatWhen(timestamp)}` 형식으로 렌더링
- corrected-save saved-history path는 reject 직후이므로 recorded timestamp가 항상 존재
- regex `^...$`로 전체 텍스트 anchoring → 추가 텍스트나 구조 변경 감지 가능

## 변경하지 않은 것

- line 352의 late-flip `#response-content-verdict-state` (broad partial)
- line 395의 rejected-verdict post-reject `#response-content-verdict-state` (broad partial)
- line 517-519, 522-524의 주변 assertions
- runtime logic, template, docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과
- `rg` 교차 확인: `#response-content-verdict-state` 참조 정합 확인
- `make e2e-test`: **17 passed (4.7m)**

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## 잔여 리스크

- line 352 (late-flip), line 395 (rejected-verdict)의 `#response-content-verdict-state`도 아직 broad partial이지만 별도 슬라이스 대상
