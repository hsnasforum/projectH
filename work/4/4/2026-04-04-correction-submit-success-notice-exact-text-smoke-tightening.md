# correction-submit success notice exact-text smoke tightening

날짜: 2026-04-04
슬라이스: `response-correction-submit success-notice exact-text smoke tightening`
이전 라운드: `work/4/4/2026-04-04-document-summary-response-copy-success-notice-exact-text-smoke-tightening.md`

## 목표

correction-submit success notice assertion 7건을 `toContainText("수정본을 기록했습니다.")`에서 `toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.")`로 교체하여, response-copy / selected-copy family에 이어 correction-submit family의 exact-text smoke coverage를 완성합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — 7개 assertion 변경 (line 442, 490, 526, 561, 696, 724, 740)

## 변경 내용

| 위치 (라인) | before | after |
|---|---|---|
| 442, 490, 526, 561, 696, 724, 740 | `toContainText("수정본을 기록했습니다.")` | `toHaveText("수정본을 기록했습니다. 저장 승인은 별도 흐름으로 유지됩니다.")` |

runtime 고정 문자열 출처: `app/static/app.js:1917` (`submitCorrection()` 내 `renderNotice()` 호출)

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — clean (whitespace 이슈 없음)
- `rg` 확인 — `toContainText("수정본을 기록했습니다")` 잔존 0건, `toHaveText` 7건
- `make e2e-test` — 17 passed (3.0m)
- `python3 -m unittest -v tests.test_web_app` — 생략 (test-only smoke-tightening 라운드, runtime/backend 코드 무변경)

## 커밋

- `7c885d3` — `test: tighten correction-submit success notice assertions to exact text`
- `git push origin HEAD:main` 완료

## 범위 제한 준수

- `app/static/app.js`, `docs/*`, `README.md`, core 로직 수정 없음
- correction-submit 외 notice family(content-reject, confirmation, aggregate, cancel 등)의 `toContainText` assertion은 건드리지 않음
- unrelated dirty worktree cleanup 없음

## 잔존 위험

- 다른 notice family(content-reject, candidate-confirmation, aggregate-trigger, cancel 등)는 여전히 `toContainText`를 사용합니다. 이들은 별도 슬라이스로 tightening할 수 있습니다.

## 다음 슬라이스 후보

- 다른 notice family의 exact-text tightening (content-reject, confirmation, aggregate 등)
- 또는 새로운 quality axis로의 전환 (Codex/operator 판단)
