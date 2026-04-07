# candidate-confirmation success notice exact-text smoke tightening

날짜: 2026-04-04
슬라이스: `candidate-confirmation success-notice exact-text smoke tightening`
이전 라운드: `work/4/4/2026-04-04-correction-submit-success-notice-exact-text-smoke-tightening.md`

## 목표

candidate-confirmation success notice assertion 2건을 `toContainText`에서 `toHaveText`로 교체하여, correction-submit family에 이어 candidate-confirmation family의 exact-text smoke coverage를 완성합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — 2개 assertion 변경 (line 630, 728)

## 변경 내용

| 위치 (라인) | before | after |
|---|---|---|
| 630, 728 | `toContainText("현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다.")` | `toHaveText("현재 수정 방향을 나중에도 다시 써도 된다는 확인을 기록했습니다. 저장 승인과는 별도입니다.")` |

runtime 고정 문자열 출처: `app/static/app.js:1941` (`submitCandidateConfirmation()` 내 `renderNotice()` 호출)

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — clean (whitespace 이슈 없음)
- `rg` 확인 — candidate-confirmation notice의 `toContainText` 잔존 0건, `toHaveText` 2건
- `make e2e-test` — 17 passed (3.1m)
- `python3 -m unittest -v tests.test_web_app` — 생략 (test-only smoke-tightening 라운드, runtime/backend 코드 무변경)

## 커밋

- `c3e7b36` — `test: tighten candidate-confirmation success notice assertions to exact text`
- `git push origin HEAD:main` 완료

## 범위 제한 준수

- `app/static/app.js`, `docs/*`, `README.md`, core 로직 수정 없음
- candidate-confirmation 외 notice family(content-reject, aggregate, cancel 등)의 `toContainText` assertion은 건드리지 않음
- unrelated dirty worktree cleanup 없음

## 잔존 위험

- 다른 notice family(content-reject, aggregate-trigger, review-apply, cancel 등)는 여전히 `toContainText`를 사용합니다. 이들은 별도 슬라이스로 tightening할 수 있습니다.
- content-reject family는 saved-history 여부에 따라 variant가 갈리고, aggregate/cancel family는 server-provided message 또는 transition id fallback이 섞여 있어 단순 exact-text 교체가 아닌 별도 검토가 필요합니다.

## 다음 슬라이스 후보

- content-reject family exact-text tightening (saved-history variant 분리 필요)
- 또는 새로운 quality axis로의 전환 (Codex/operator 판단)
