# 2026-04-22 smoke drift durable candidate assertions

## 변경 파일
- `e2e/tests/web-smoke.spec.mjs`
- `work/4/22/2026-04-22-smoke-drift-durable-candidate-assertions.md`

## 사용 skill
- `e2e-smoke-triage`: 기존 candidate confirmation Playwright scenario의 drift 지점과 추가 payload assertion 위치를 좁혀 확인했습니다.
- `release-check`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, 남은 리스크를 분리했습니다.
- `finalize-lite`: 구현 종료 전 focused verification과 `/work` closeout 준비 상태를 점검했습니다.
- `work-log-closeout`: 변경 파일, 검증 결과, 남은 리스크를 이 persistent `/work` 기록으로 남겼습니다.

## 변경 이유
- seq 733 handoff는 seq 732에서 막힌 `preexisting_smoke_assertion_drift`를 같은 scenario 안에서 해결하고, seq 729의 `durable_candidate` / `review_queue_items` provenance fields를 Playwright smoke에서 확인하라고 요구했습니다.
- `session_local_candidate.supporting_signal_refs`의 primary basis는 현재 `session_local_memory_signal.correction_signal`인데, smoke test는 과거 `session_local_memory_signal.content_signal`을 기대하고 있었습니다.
- 이전 라운드에서 추가된 `item_type`, `derived_from`, `derived_at`은 service tests로 확인됐지만, browser smoke의 candidate-confirmation path에서는 아직 검증되지 않았습니다.

## 핵심 변경
- 기존 candidate-confirmation scenario 안의 3개 stale assertion을 `session_local_memory_signal.correction_signal`로 맞췄습니다.
- `reviewAcceptButton.click()` 직전 session payload를 다시 조회해 `review_queue_items`가 1개이며 `item_type = durable_candidate`인지 확인합니다.
- 같은 pre-accept queue item에서 `derived_from.record_type = candidate_confirmation_record`와 non-empty `derived_at`를 확인합니다.
- accept 후 source message의 `durable_candidate.derived_at`, `derived_from.record_type`, `derived_from.candidate_id`를 추가로 검증합니다.
- 새 scenario, 새 selector, 새 product behavior, 새 docs contract는 추가하지 않았습니다.

## 검증
- `node --check e2e/tests/web-smoke.spec.mjs` -> 통과
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` -> 통과
- `cd e2e && npx playwright test tests/web-smoke.spec.mjs -g "candidate confirmation" --reporter=line` -> 1 passed, 0 failed
- `git diff --check -- e2e/tests/web-smoke.spec.mjs` -> 통과

## 남은 리스크
- 전체 Playwright suite는 실행하지 않았습니다. 이번 변경은 handoff가 지정한 기존 candidate-confirmation scenario 내부 assertion 보강에 한정했고, isolated scenario가 통과했습니다.
- 제품 동작이나 문서화된 사용자 흐름은 바꾸지 않았기 때문에 README/spec/acceptance 문서는 수정하지 않았습니다.
- 작업 전부터 다른 runtime/docs/tests/report/work 파일들이 dirty 상태였습니다. 이번 라운드는 handoff 범위 파일만 수정했고 기존 변경은 되돌리지 않았습니다.
- commit, push, branch/PR publish, `.pipeline/gemini_request.md`, `.pipeline/operator_request.md` 작성은 수행하지 않았습니다.
