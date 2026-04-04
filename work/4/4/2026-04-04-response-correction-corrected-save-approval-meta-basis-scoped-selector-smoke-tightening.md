# response-correction-corrected-save-approval-meta-basis scoped-selector smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-corrected-save-approval-meta-basis scoped-selector smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 corrected-save first bridge path scenario의 `저장 기준: 기록된 수정본 스냅샷` assertion 1건을 `#approval-meta span` scoped exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:450` — `page.locator("#approval-meta").toContainText`를 `page.locator("#approval-meta span").filter({ hasText: "저장 기준:" }).toHaveText("저장 기준: 기록된 수정본 스냅샷")`로 교체

## 변경 내용

- 기존 line 450의 whole-box `toContainText`를 `#approval-meta span` 범위에서 `저장 기준:` line만 filter하여 exact-text로 검증하도록 교체했습니다.
- 런타임 `app/static/app.js:3072`에서 각 meta line을 `<span>` 단위로 렌더링하므로, filter + toHaveText로 해당 span의 전체 텍스트를 정확히 검증합니다.
- response-correction family가 닫힌 뒤 새로운 approval-meta quality axis로 전환한 첫 슬라이스입니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '#approval-meta|저장 기준: 기록된 수정본 스냅샷' e2e/tests/web-smoke.spec.mjs app/templates/index.html app/static/app.js`: test 2건 + runtime 다수 확인
- `make e2e-test`: 17 passed (3.4m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. approval-meta basis scoped exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- line 451-453의 approval-meta explanation assertions와 line 492의 post-approval duplicate는 아직 `toContainText`로 남아 있습니다.

## 커밋

- `b383112` test: tighten corrected-save approval-meta basis to scoped exact-text on span element
