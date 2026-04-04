# corrected-save-approval-meta-freeze-explanation scoped-selector smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-corrected-save-approval-meta-freeze-explanation scoped-selector smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 corrected-save first bridge path scenario의 freeze explanation assertion 1건을 `#approval-meta span` scoped exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:451` — `page.locator("#approval-meta").toContainText("요청 시점에 고정되며")`를 `page.locator("#approval-meta span").filter({ hasText: "요청 시점에 고정되며" }).toHaveText("이 미리보기는 저장 요청 시점에 고정되며, 나중에 수정본을 다시 기록해도 자동으로 바뀌지 않습니다.")`로 교체

## 변경 내용

- 기존 line 451의 whole-box `toContainText`를 `#approval-meta span` 범위에서 freeze explanation line만 filter하여 runtime `app/static/app.js:3062`의 full fixed string과 정확히 일치하는 exact-text로 검증하도록 교체했습니다.
- 이전 basis 슬라이스(line 450)와 동일한 `#approval-meta span` + `filter` + `toHaveText` 패턴입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '#approval-meta|이 미리보기는 저장 요청 시점에 고정되며|나중에 수정본을 다시 기록해도 자동으로 바뀌지 않습니다' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 1건 + runtime 1건 확인
- `make e2e-test`: 17 passed (3.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. approval-meta freeze explanation scoped exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- line 452의 reissue explanation과 line 453의 negative assertion, line 492의 post-approval duplicate는 아직 `toContainText`로 남아 있습니다.

## 커밋

- `6a1fe4e` test: tighten corrected-save approval-meta freeze-explanation to scoped exact-text on span element
