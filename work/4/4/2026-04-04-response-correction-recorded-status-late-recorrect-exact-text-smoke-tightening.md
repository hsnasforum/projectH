# response-correction-recorded-status-late-recorrect exact-text smoke tightening

날짜: 2026-04-04
슬라이스: response-correction-recorded-status-late-recorrect exact-text smoke tightening

## 목표

`e2e/tests/web-smoke.spec.mjs`에서 corrected-save late reject / re-correct scenario의 `#response-correction-status` assertion 1건을 exact-text `toHaveText`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs:533` — `toContainText`를 `toHaveText("저장 요청은 현재 입력창이 아니라 이미 기록된 수정본으로 새 승인 미리보기를 만듭니다. 저장 승인과는 별도입니다.")`로 교체

## 변경 내용

- 기존 line 533의 `toContainText`를 primary-flow(line 444)와 동일한 exact-text `toHaveText`로 대체했습니다.
- 이 지점도 approval card가 열려 있지 않은 same recorded branch라 optional third sentence가 붙지 않습니다.
- 런타임 코드, 템플릿, docs 변경 없음.

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: whitespace 오류 없음
- `rg -n 'response-correction-status|저장 요청은 현재 입력창이 아니라|저장 승인과는 별도입니다' e2e/tests/web-smoke.spec.mjs app/static/app.js`: test 다수 + runtime 다수 확인
- `make e2e-test`: 17 passed (2.7m)
- `python3 -m unittest -v tests.test_web_app`: 생략 — test-only smoke-tightening 라운드로 서버 로직 변경 없음

## 위험 / 미해결

- 없음. recorded correction status exact-text 강화만 수행했으며 런타임 behavior 변경 없음.
- `#response-correction-status`의 unrecorded-change variant(line 460-461)는 아직 `toContainText`로 남아 있습니다.

## 커밋

- `18e6676` test: tighten response-correction-recorded-status-late-recorrect to exact-text on dedicated element
