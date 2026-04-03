# candidate-review-accept success notice exact-text smoke tightening

날짜: 2026-04-04
슬라이스: `candidate-review-accept success-notice exact-text smoke tightening`
이전 라운드: `work/4/4/2026-04-04-candidate-confirmation-success-notice-exact-text-smoke-tightening.md`

## 목표

candidate-review-accept success notice assertion 1건을 `toContainText`에서 `toHaveText`로 교체하여, candidate flow 안의 review-accept notice exact-text smoke coverage를 완성합니다.

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs` — 1개 assertion 변경 (line 646)

## 변경 내용

| 위치 (라인) | before | after |
|---|---|---|
| 646 | `toContainText("검토 후보를 수락했습니다. 아직 적용되지는 않았습니다.")` | `toHaveText("검토 후보를 수락했습니다. 아직 적용되지는 않았습니다.")` |

runtime 고정 문자열 출처: `app/static/app.js:1969` (`submitCandidateReviewAccept()` 내 `renderNotice()` 호출)

## 검증

- `git diff --check -- e2e/tests/web-smoke.spec.mjs` — clean (whitespace 이슈 없음)
- `rg` 확인 — candidate-review-accept notice의 `toContainText` 잔존 0건, `toHaveText` 1건
- `make e2e-test` — 17 passed (3.2m)
- `python3 -m unittest -v tests.test_web_app` — 생략 (test-only smoke-tightening 라운드, runtime/backend 코드 무변경)

## 커밋

- `2c4e8c2` — `test: tighten candidate-review-accept success notice assertion to exact text`

## 범위 제한 준수

- `app/static/app.js`, `docs/*`, `README.md`, core 로직 수정 없음
- candidate-review-accept 외 notice family(content-reject, aggregate, cancel, 거절 메모 등)의 `toContainText` assertion은 건드리지 않음
- unrelated dirty worktree cleanup 없음

## 잔존 위험

- 다른 notice family(content-reject, 거절 메모, aggregate-trigger, review-apply, cancel 등)는 여전히 `toContainText`를 사용합니다. 이들은 별도 슬라이스로 tightening할 수 있습니다.
- content-reject family는 saved-history 여부에 따라 variant가 갈리고, aggregate/cancel family는 server-provided message 또는 transition id fallback이 섞여 있어 단순 exact-text 교체가 아닌 별도 검토가 필요합니다.
- 거절 메모 family는 2건이 남아 있으며, 고정 문자열 검증 후 tightening 가능합니다.

## 다음 슬라이스 후보

- 거절 메모 family exact-text tightening (2건, 고정 문자열 확인 필요)
- content-reject family exact-text tightening (saved-history variant 분리 필요)
- 또는 새로운 quality axis로의 전환 (Codex/operator 판단)
