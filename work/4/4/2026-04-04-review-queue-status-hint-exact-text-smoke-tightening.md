# review-queue-status-hint exact-text smoke tightening

날짜: 2026-04-04
슬라이스: review-queue-status-hint exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 first visible review queue rendering의 status hint assertion을 box-level `toContainText`에서 dedicated `#review-queue-status` element exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:637` — `page.locator("#review-queue-status")` 기준 `toHaveText("현재 후보는 검토 수락만 기록할 수 있습니다. 아직 적용, 편집, 거절은 열지 않았습니다.")` 1건으로 교체

## 변경 내용

- 기존 line 637의 `await expect(reviewQueueBox).toContainText("현재 후보는 ...")`를 `await expect(page.locator("#review-queue-status")).toHaveText("현재 후보는 ...")`로 교체했습니다.
- `#review-queue-status` element는 템플릿 `app/templates/index.html:25`에서 dedicated `span.sidebar-hint`로 제공되며, 런타임 `app/static/app.js:2436`에서 동일 문자열로 설정됩니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'review-queue-status|현재 후보는 검토 수락만 기록할 수 있습니다' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`: test 1건 + template 1건 + runtime 2건 확인
- `make e2e-test`: 17 passed (2.4m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. review queue status hint exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- review queue item 내부의 statement/basis/status assertions(line 638-640)는 아직 box-level `toContainText`로 남아 있습니다.

## 커밋

- `4db1973` test: tighten review-queue-status-hint to exact-text on dedicated element
