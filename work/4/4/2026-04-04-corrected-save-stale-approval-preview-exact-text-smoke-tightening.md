# corrected-save-stale-approval-preview exact-text smoke tightening

날짜: 2026-04-04
슬라이스: corrected-save-stale-approval-preview exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 first bridge scenario의 stale `#approval-preview` assertion 1건을 exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:461` — `toContainText("수정본 A입니다.")`를 `toHaveText(correctedTextA)`로 교체

## 변경 내용

- 기존 line 461의 `toContainText`를 same scenario local constant `correctedTextA`를 재사용하는 `toHaveText`로 대체했습니다.
- user가 `correctedTextB`를 입력한 뒤에도 preview가 old snapshot `correctedTextA` 전체를 유지하는 stale-preview 불변성을 exact-text로 강하게 검증합니다.
- line 462의 negative assertion(`not.toContainText("수정본 B입니다.")`)은 이제 line 461의 exact positive check에 의해 더 강하게 함의되지만 defensive guard로 유지합니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n '#approval-preview|수정본 A입니다|핵심만 남겼습니다' e2e/tests/web-smoke.spec.mjs`: line 461/493 toHaveText + line 454 toContainText 확인
- `make e2e-test`: 17 passed (4.3m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. stale approval-preview exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- line 454의 initial first-bridge `#approval-preview` positive assertion은 아직 `toContainText`로 남아 있습니다.

## 커밋

- `7895e86` test: tighten corrected-save stale approval-preview to exact-text on dedicated element
