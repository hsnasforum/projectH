# 2026-05-19 reviewed-memory transition mutation identity lifecycle reload visibility

## 변경 파일

- `e2e/tests/web-smoke.spec.mjs`
- `work/5/19/2026-05-19-reviewed-memory-transition-mutation-identity-lifecycle-reload-visibility.md`
- 기존 dirty context로 함께 검증한 파일
  - `app/static/app.js`
  - `docs/ACCEPTANCE_CRITERIA.md`

## 사용 skill

- `e2e-smoke-triage`: 기존 aggregate-trigger lifecycle Playwright scenario 두 개 안에서 reload 상태별 assertion만 보강하는 최소 검증 범위를 정하기 위해 사용했습니다.
- `work-log-closeout`: handoff #1975 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리하기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1975`가 `mutation canonical_transition_id+aggregate_fingerprint` metadata token이 최초 aggregate card뿐 아니라 hard reload 이후 lifecycle 상태에서도 계속 browser-visible인지 guard하라고 지시했습니다.
- 직전 라운드에서 token 표시 자체와 최초 Playwright assertion은 검증됐지만, 이미 shipped된 emitted/apply-pending/active-effect 및 stop/reverse/conflict reload 상태에는 같은 token assertion이 없었습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `e2e/tests/web-smoke.spec.mjs`에 `expectAggregateTriggerMutationGuard` helper를 추가했습니다.
- 기존 initial aggregate card assertion을 helper 호출로 정리했습니다.
- `same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다` scenario의 emitted record reload, applied-pending reload, active-effect reload 지점에 mutation guard assertion을 추가했습니다.
- `same-session recurrence aggregate는 stop-reverse-conflict lifecycle으로 정리됩니다` scenario의 stopped reload, reversed reload, conflict-checked reload 지점에 mutation guard assertion을 추가했습니다.
- 제품 동작, UI 문구, POST body shape, serializer field, transition validation, 문서는 변경하지 않았습니다.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate는 (emitted-apply-confirm|stop-reverse-conflict) lifecycle" --reporter=line`
  - 통과: `2 passed (35.8s)`.
- `rg -n "mutation canonical_transition_id\\+aggregate_fingerprint|expectAggregateTriggerMutationGuard|transition_mutation_identity_requirement" e2e/tests/web-smoke.spec.mjs app/static/app.js docs/ACCEPTANCE_CRITERIA.md`
  - 통과: Playwright helper와 7개 호출 지점, UI rendering token, 수용 기준 문서 marker를 확인했습니다.
- `git diff --check -- e2e/tests/web-smoke.spec.mjs app/static/app.js docs/ACCEPTANCE_CRITERIA.md work/5/19/2026-05-19-reviewed-memory-transition-mutation-identity-lifecycle-reload-visibility.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 기존 두 aggregate-trigger lifecycle Playwright scenario 안의 reload visibility guard 보강 범위입니다.
- 전체 Playwright suite, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
