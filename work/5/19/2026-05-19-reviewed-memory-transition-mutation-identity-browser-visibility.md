# 2026-05-19 reviewed-memory transition mutation identity browser visibility

## 변경 파일

- `app/static/app.js`
- `e2e/tests/web-smoke.spec.mjs`
- `docs/ACCEPTANCE_CRITERIA.md`
- `work/5/19/2026-05-19-reviewed-memory-transition-mutation-identity-browser-visibility.md`

## 사용 skill

- `e2e-smoke-triage`: browser-visible metadata 변경과 기존 aggregate-trigger Playwright scenario의 최소 검증 범위를 정하기 위해 사용했습니다.
- `doc-sync`: 새 UI-visible metadata truth가 현재 수용 기준 문서에만 좁게 반영되도록 확인했습니다.
- `work-log-closeout`: handoff #1974 구현 결과, 실제 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 정리하기 위해 사용했습니다.

## 변경 이유

- `.pipeline/implement_handoff.md#1974`가 `/api/session` payload에 이미 검증된 `transition_mutation_identity_requirement = canonical_transition_id_and_aggregate_fingerprint_required`를 로컬 웹 쉘의 aggregate trigger card에서도 operator-visible metadata로 드러내라고 지시했습니다.
- 기존 aggregate card는 `capability ...`와 `audit ...` metadata만 보여 새 mutation guard가 브라우저-visible surface에는 직접 드러나지 않았습니다.
- publication backlog는 계속 held 상태이며 commit, push, branch/PR publication, PR creation/reuse/update, merge, release는 수행하지 않았습니다.

## 핵심 변경

- `app/static/app.js`의 `renderAggregateTriggerSection` metadata 배열에 `mutation canonical_transition_id+aggregate_fingerprint` token을 추가했습니다.
- token은 `reviewed_memory_transition_audit_contract.transition_mutation_identity_requirement`가 `canonical_transition_id_and_aggregate_fingerprint_required`일 때 표시됩니다.
- 기존 `capability ...`, `audit ...`, 계획 타깃, action enablement, POST body shape, transition mutation validation은 변경하지 않았습니다.
- `e2e/tests/web-smoke.spec.mjs`의 `same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다` scenario가 aggregate card metadata에서 새 mutation token을 확인하도록 보강했습니다.
- `docs/ACCEPTANCE_CRITERIA.md`에 aggregate-card metadata가 `mutation canonical_transition_id+aggregate_fingerprint`를 표시한다는 수용 기준을 한 줄 추가했습니다.

## 검증

- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "same-session recurrence aggregate는 emitted-apply-confirm lifecycle으로 활성화됩니다" --reporter=line`
  - 통과: `1 passed (29.4s)`.
- `rg -n "transition_mutation_identity_requirement|canonical_transition_id_and_aggregate_fingerprint_required|mutation canonical_transition_id\\+aggregate_fingerprint" app/static/app.js e2e/tests/web-smoke.spec.mjs docs/ACCEPTANCE_CRITERIA.md`
  - 통과: UI rendering, Playwright assertion, 수용 기준 문서에서 marker와 visible token을 확인했습니다.
- `git diff --check -- app/static/app.js e2e/tests/web-smoke.spec.mjs docs/ACCEPTANCE_CRITERIA.md work/5/19/2026-05-19-reviewed-memory-transition-mutation-identity-browser-visibility.md .pipeline/implement_handoff.md`
  - 통과: 출력 없음.

## 남은 리스크

- 이번 라운드는 aggregate trigger card의 browser-visible metadata guard와 isolated Playwright scenario 보강 범위입니다.
- 전체 Playwright suite, `make e2e-test`, controller startup, runtime live start/stop/restart, tmux control, long soak는 실행하지 않았습니다.
- release-ready, publication-ready, full-smoke-pass, merge-ready 상태를 주장하지 않습니다.
- `.pipeline/advisory_request.md`와 `.pipeline/operator_request.md`는 작성하지 않았고, 다음 slice도 선택하지 않았습니다.
