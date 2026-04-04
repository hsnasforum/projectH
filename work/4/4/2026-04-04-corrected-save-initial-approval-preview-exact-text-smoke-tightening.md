# corrected-save initial approval-preview exact-text smoke tightening

날짜: 2026-04-04

## 목표

corrected-save first bridge scenario에서 initial `#approval-preview` assertion 1건을 partial `toContainText`에서 exact-text `toHaveText(correctedTextA)`로 강화합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` (line 454)
  - `toContainText("수정본 A입니다.")` → `toHaveText(correctedTextA)`
  - expected value는 same scenario local constant `correctedTextA = "수정본 A입니다.\n핵심만 남겼습니다."`를 재사용

## 변경하지 않은 것

- line 461, 462의 stale preview assertions
- line 450-453, 493의 `#approval-meta`/preview assertions
- `#notice-box`, `response-correction-state/status` assertions
- runtime logic (`app/static/app.js`), template (`app/templates/index.html`), docs

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs`: 통과 (whitespace 에러 없음)
- `rg` 교차 확인: `#approval-preview` 참조가 spec/template/app.js 간 정합 확인
- `make e2e-test`: 16 passed, 1 failed
  - 이번 슬라이스 대상 test #9 (`corrected-save first bridge path`): **passed**
  - 기존 실패 test #7 (line 327, `원문 저장 후 늦게 내용 거절`): `fs.existsSync(lateFlipNotePath)` 파일 생성 문제로 이번 변경과 무관한 pre-existing failure

## python3 -m unittest 생략 사유

test-only smoke assertion tightening 라운드이며, runtime logic / template / core에 변경이 없으므로 unit test 실행을 생략합니다.

## 잔여 리스크

- test #7 (line 327) pre-existing failure는 별도 슬라이스에서 조사가 필요합니다.
- line 462의 negative partial check (`not.toContainText("수정본 B입니다.")`)는 line 461의 exact-text assertion이 이미 충분히 커버하므로 우선순위 낮음.
