# 2026-04-16 reviewed-memory aggregate reload smoke split verification

## 변경 파일
- `verify/4/16/2026-04-16-reviewed-memory-aggregate-reload-smoke-split-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-reviewed-memory-aggregate-reload-smoke-split.md`는 기존 `same-session recurrence aggregate` browser smoke를 helper 1개와 lifecycle 기준 2개 시나리오로 분할해 single-scenario timeout pressure를 낮췄다고 주장합니다.
- 이번 verification 라운드는 그 주장이 현재 tree와 일치하는지 다시 확인하고, 이 변경에 필요한 가장 좁은 재실행인 isolated Playwright rerun과 관련 `diff --check`만 다시 돌리는 것이 목적입니다.
- 재실행 결과 latest `/work`는 truthful하게 닫혔지만, 다음 구현 슬라이스는 same-family current-risk reduction과 axis switch 사이 우선순위가 아직 낮은 확신 상태라 seq 203은 새 implement handoff 대신 Gemini arbitration으로 여는 편이 맞습니다.

## 핵심 변경
- 최신 `/work`의 정적 구현 주장은 현재 tree와 일치합니다.
  - `e2e/tests/web-smoke.spec.mjs`에는 `advanceAggregateToActiveEffect(page)` helper가 추가되어 있고, 반환값으로 `{ sessionId, canonicalTransitionId }`를 넘깁니다.
  - 기존 단일 long scenario는 `same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다`와 `same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다` 두 시나리오로 분할되어 있으며, 각각 `testInfo.setTimeout(150_000)`을 사용합니다.
- 최신 `/work`의 docs 미변경 주장도 현재 docs wording 기준으로 맞습니다.
  - root docs는 raw `test(...)` 개수 대신 document-level coverage inventory 또는 하나의 same-session aggregate path contract를 설명하고 있습니다.
  - 따라서 이번 변경처럼 기존 aggregate path를 두 Playwright scenario로 재조직한 것만으로는 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`의 shipped contract wording을 다시 바꿔야 할 직접 근거가 없습니다.
- 재실행 결과는 `/work`의 핵심 검증 주장과 일치합니다.
  - `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate" --reporter=line` 재실행 결과 `2 passed (1.9m)`였습니다.
  - `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`는 clean입니다.
- 다만 다음 한 슬라이스는 현재 tree만으로는 바로 고르기 어렵습니다.
  - reviewed-memory aggregate family는 now-shipped lifecycle과 six-point reload continuity를 truthful하게 닫았고, 이번 라운드는 oversized smoke를 분할해 timeout pressure까지 낮췄습니다.
  - 남은 후보는 same-family supersession/staleness clarity, aggregate/review-queue coexistence parity, 또는 다른 shipped `app.web` axis 전환 등으로 갈리며, 이 단계에서는 Gemini arbitration이 implement handoff보다 정직합니다.

## 검증
- `git diff -- e2e/tests/web-smoke.spec.mjs`
  - 결과: helper 추가, 기존 long aggregate smoke의 two-scenario split, `canonicalTransitionId` 재사용 diff 확인
- `rg -n "125 core browser scenarios|same-session recurrence aggregate" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`
  - 결과: root docs가 raw test count가 아니라 coverage inventory / aggregate path contract를 설명하는지 재확인
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate" --reporter=line`
  - 결과: `2 passed (1.9m)`
- full Playwright suite 미실행
  - 이유: production code와 shared browser helper는 바뀌지 않았고, 이번 라운드는 existing aggregate smoke 조직만 재구성한 test-only slice라 isolated rerun이 가장 좁은 truthful check입니다.

## 남은 리스크
- split으로 single-scenario timeout pressure는 `240_000ms`에서 `150_000ms`로 낮아졌지만, isolated rerun 총시간은 여전히 `1.9m`이며 second-half scenario는 active-effect setup replay를 포함합니다.
- reviewed-memory family 안에서 다음 current-risk reduction을 계속 고를지, 아니면 다른 shipped `app.web` 축으로 전환할지는 현재 notes/code만으로 우열이 분명하지 않습니다.
- 따라서 seq 203은 `.pipeline/gemini_request.md`의 `STATUS: request_open`으로 닫고, Gemini recommendation 이후 exact implement slice를 다시 좁히는 편이 맞습니다.
