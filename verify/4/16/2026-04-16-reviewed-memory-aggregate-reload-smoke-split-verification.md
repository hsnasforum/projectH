# 2026-04-16 reviewed-memory aggregate reload smoke split verification

## 변경 파일
- 없음

## 사용 skill
- `round-handoff`

## 변경 이유
- 최신 `/work`인 `work/4/16/2026-04-16-reviewed-memory-aggregate-reload-smoke-split.md`는 reviewed-memory aggregate reload continuity browser smoke를 helper 기반 2개 lifecycle 시나리오로 분할해 timeout 압박과 flake 위험을 낮췄다고 주장합니다.
- 이번 verification 라운드는 그 핵심 구현, docs 미변경 판단, 그리고 적어 둔 focused rerun 결과가 현재 tree에서도 그대로 truth인지 다시 확인하는 목적입니다.

## 핵심 변경
- `/work`의 핵심 구현 주장은 현재 tree와 일치합니다.
  - `e2e/tests/web-smoke.spec.mjs`에는 `advanceAggregateToActiveEffect(page)` helper가 존재합니다.
  - 같은 파일에는 `same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다`와 `same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다` 두 시나리오가 각각 `testInfo.setTimeout(150_000)`으로 존재합니다.
  - 따라서 overlong reload continuity smoke를 helper + 2개 lifecycle 시나리오로 쪼갰다는 `/work`의 구현 설명 자체는 현재 tree 기준으로 맞습니다.
- 다만 `/work`의 focused rerun 문구는 현재 tree 기준으로는 더 이상 그대로 재현되지 않습니다.
  - `/work`가 적은 `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate" --reporter=line`는 현재 tree에서 2개가 아니라 5개 title을 잡습니다.
  - 실제 rerun 결과도 `2 passed (1.9m)`가 아니라 `5 passed (3.7m)`였습니다.
  - 현재 same-family title에는 split된 두 lifecycle 외에도 `stale candidate retires before apply start`, `active lifecycle survives supporting correction supersession`, `recorded basis label survives supporting correction supersession`가 포함되어 있어 broad `-g` 패턴이 더 이상 split 2건만을 가리키지 않습니다.
- docs 미변경 판단은 현재 contract 관점에서는 유지 가능합니다.
  - 현재 `README.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/MILESTONES.md`, `docs/TASK_BACKLOG.md`는 lifecycle coverage와 shipped contract를 설명하고 있으며, 이번 split 때문에 새로 생긴 docs/implementation mismatch는 확인되지 않았습니다.
  - 다만 현재 tree에는 later same-day sqlite/history-card docs 작업이 이미 섞여 있으므로, `/work`의 "docs 미변경" 문장을 당시 clean snapshot 그대로 재현하는 검수는 아닙니다.
- 따라서 최신 `/work`는 핵심 구현 설명은 truthful하지만, 적어 둔 broad rerun 결과는 current tree 기준으로 stale합니다. closeout 전체를 그대로 current truth로 재사용할 수는 없습니다.

## 검증
- `rg -n "advanceAggregateToActiveEffect|same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다|same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다|setTimeout\\(150_000\\)" e2e/tests/web-smoke.spec.mjs`
  - 결과: helper 1건, split된 두 lifecycle title, 각 150s timeout 존재 확인
- `rg -n "same-session recurrence aggregate|hard page reload continuity|Playwright smoke covers 125 core browser scenarios" README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: current contract docs는 reviewed-memory lifecycle continuity를 설명하고 있으며, 이번 split로 인해 새로 드러난 docs mismatch는 확인되지 않음
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate" --reporter=line`
  - 결과: `5 passed (3.7m)`
- `git diff --check -- e2e/tests/web-smoke.spec.mjs README.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md`
  - 결과: 출력 없음
- full `make e2e-test`, sqlite browser smoke, exact two-title rerun은 미실행
  - 이유: 이번 verification round의 목적은 `/work`가 적어 둔 broad smoke split claim과 그 rerun 문구를 current tree 기준으로 재대조하는 것이며, broad pattern rerun 1회로도 현재 mismatch가 충분히 드러났습니다.

## 남은 리스크
- split 자체는 유지되지만, `same-session recurrence aggregate`라는 broad title prefix는 이제 5개 scenario를 함께 잡으므로 split 2건만을 빠르게 재확인하는 proxy로는 더 이상 안정적이지 않습니다.
- 따라서 이후 same-family browser triage가 이 split 2건만 다시 보고 싶다면 exact title `-g` 두 개를 쓰거나, 공통 prefix를 더 좁게 만드는 bounded test-title 정리가 필요합니다.
- 다만 현재 live automation 관점의 우선 blocker는 이 4/16 round가 아니라, `work/4/17/2026-04-17-sqlite-browser-history-card-noisy-single-source-strong-plus-missing-click-reload-exact-title-parity.md`가 아직 `/verify` 없이 남아 있는 truth-sync 상태입니다.
