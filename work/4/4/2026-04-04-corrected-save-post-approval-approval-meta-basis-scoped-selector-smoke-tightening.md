# corrected-save-post-approval-approval-meta-basis scoped-selector smoke tightening

날짜: 2026-04-04
슬라이스: corrected-save-post-approval-approval-meta-basis scoped-selector smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 post-approval path의 approval-meta basis assertion 1건을 `#approval-meta span` scoped exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:492` — `page.locator("#approval-meta").toContainText("저장 기준: 기록된 수정본 스냅샷")`를 `page.locator("#approval-meta span").filter({ hasText: "저장 기준:" }).toHaveText("저장 기준: 기록된 수정본 스냅샷")`로 교체

## 변경 내용

- 기존 line 492의 whole-box `toContainText`를 first bridge path의 line 450과 동일한 `#approval-meta span` scoped exact-text 패턴으로 교체했습니다.
- `저장 기준: 기록된 수정본 스냅샷` basis line이 이제 두 지점(line 450 first-bridge, line 492 post-approval) 모두 scoped exact-text로 검증됩니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '#approval-meta|저장 기준: 기록된 수정본 스냅샷' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 2건(line 450, 492) + runtime 1건 확인
- `make e2e-test`: 17 passed (3.4m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. post-approval approval-meta basis scoped exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- line 453의 negative assertion(`not.toContainText("저장 기준: 원래 grounded brief 초안")`)은 negative guard이므로 scoped tightening 대상이 아닙니다.

## 커밋

- `568ebc1` test: tighten corrected-save post-approval approval-meta basis to scoped exact-text on span element
