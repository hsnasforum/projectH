# review-queue-accept-button-recurrence-scenario exact-text smoke tightening

날짜: 2026-04-04
슬라이스: review-queue-accept-button-recurrence-scenario exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 transition record emission 뒤 recurrence scenario의 review queue accept button assertion을 box-level `toContainText`에서 dedicated `[data-testid="review-queue-accept"]` element exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:764` — `reviewQueueBox.getByTestId("review-queue-accept")` 기준 `toHaveText("검토 수락")` 1건으로 교체

## 변경 내용

- 기존 line 764의 `await expect(reviewQueueBox).toContainText("검토 수락")`를 `await expect(reviewQueueBox.getByTestId("review-queue-accept")).toHaveText("검토 수락")`로 교체했습니다.
- first visible review queue scenario(line 641-643)와 동일한 testid/exact-text 패턴을 recurrence scenario에 확장한 것입니다.
- 런타임 `app/static/app.js:2502-2503`에서 accept button에 `검토 수락` textContent와 `data-testid="review-queue-accept"`가 직접 설정됩니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '검토 수락|review-queue-accept|review-queue-box' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 다수 + runtime 다수 확인
- `make e2e-test`: 17 passed (2.4m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. review queue accept button exact-text 강화만 수행했으며 런타임 behavior 변경 없음.

## 커밋

- `f6192aa` test: tighten review-queue-accept-button in recurrence scenario to exact-text on dedicated element
