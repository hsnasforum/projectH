# corrected-save-approval-meta-new-save-explanation scoped-selector smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-corrected-save-approval-meta-new-save-explanation scoped-selector smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 corrected-save first bridge path scenario의 new-save explanation assertion 1건을 `#approval-meta span` scoped exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:452` — `page.locator("#approval-meta").toContainText("새 저장 요청을 다시 만들어야 합니다.")`를 `page.locator("#approval-meta span").filter({ hasText: "새 저장 요청을 다시 만들어야 합니다" }).toHaveText("더 새 수정본을 저장하려면 응답 카드에서 새 저장 요청을 다시 만들어야 합니다.")`로 교체

## 변경 내용

- 기존 line 452의 whole-box `toContainText`를 `#approval-meta span` 범위에서 new-save explanation line만 filter하여 runtime `app/static/app.js:3063`의 full fixed string과 정확히 일치하는 exact-text로 검증하도록 교체했습니다.
- corrected-save approval-meta의 3개 positive assertion(basis, freeze, new-save)이 이제 모두 `#approval-meta span` scoped exact-text로 검증됩니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '#approval-meta|더 새 수정본을 저장하려면|새 저장 요청을 다시 만들어야 합니다' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 1건 + runtime 1건 확인
- `make e2e-test`: 17 passed (3.6m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. approval-meta new-save explanation scoped exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- line 453의 negative assertion(`not.toContainText`)과 line 492의 post-approval duplicate는 아직 `toContainText`로 남아 있습니다.

## 커밋

- `b7e58b2` test: tighten corrected-save approval-meta new-save-explanation to scoped exact-text on span element
