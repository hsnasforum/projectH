# corrected-save-long-history-approval-preview exact-text smoke tightening

날짜: 2026-04-04
슬라이스: corrected-save-long-history-approval-preview exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 corrected-save long-history scenario의 `#approval-preview` assertion 1건을 exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:493` — `toContainText("수정본 A입니다.")`를 `toHaveText(correctedTextA)`로 교체

## 변경 내용

- 기존 line 493의 `toContainText`를 same scenario local constant `correctedTextA = "수정본 A입니다.\n핵심만 남겼습니다."`를 그대로 재사용하는 `toHaveText`로 대체했습니다.
- 런타임 `app/static/app.js:3074`에서 `approval.preview_markdown`을 `textContent`로 직접 렌더링하며, corrected-save path에서는 recorded correction text 전체가 preview에 들어갑니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '#approval-preview|수정본 A입니다|핵심만 남겼습니다' e2e/tests/web-smoke.spec.mjs`: line 493 toHaveText + line 454/461/462 toContainText 확인
- `make e2e-test`: 17 passed (3.4m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. approval-preview exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- line 454/461의 first-bridge `#approval-preview` positive assertions와 line 462의 negative assertion은 아직 `toContainText`로 남아 있습니다.

## 커밋

- `c7ab0da` test: tighten corrected-save long-history approval-preview to exact-text on dedicated element
