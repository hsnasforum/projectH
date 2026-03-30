# 2026-03-28 durable candidate review queue implementation

## 변경 파일
- `app/web.py`
- `app/templates/index.html`
- `tests/test_web_app.py`
- `e2e/tests/web-smoke.spec.mjs`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- `doc-sync`: session serialization, existing shell UI, smoke wording 변경을 current contract에 맞춰 루트 문서까지 같이 맞췄습니다.
- `e2e-smoke-triage`: 기존 candidate-confirmation browser smoke를 최소 확장해서 queue selector와 read-only copy drift만 확인했습니다.
- `release-check`: 구현 후 py_compile, unit/service regression, Playwright smoke, `git diff --check`, grep sync를 실제 실행 결과 기준으로 정리했습니다.
- `work-log-closeout`: 이번 라운드의 변경 파일, 실행한 검증, 남은 리스크를 `/work` 표준 형식으로 정리했습니다.

## 변경 이유
- 직전 closeout `2026-03-28-durable-candidate-projection-implementation.md`에서 이어받은 핵심 리스크는 current `eligible_for_review` `durable_candidate`를 operator가 한 곳에서 읽을 local surface가 없다는 점이었습니다.
- current source-message payload 안에서만 `durable_candidate`가 보이면 inspection boundary가 UI 상으로 닫히지 않고, review layer가 아직 없는 상태에서 source-message detail을 계속 뒤져야 했습니다.
- 이번 라운드는 그 리스크만 좁게 해소하기 위해 current persisted session state를 canonical source로 유지한 채, read-only review queue surface만 additive하게 추가했습니다.

## 핵심 변경
- `app/web.py`에서 current serialized grounded-brief source messages를 순회해 `promotion_eligibility = eligible_for_review`인 current `durable_candidate`만 모으는 top-level `review_queue_items` session projection을 추가했습니다.
- queue item은 `candidate_id`, `candidate_family`, `statement`, `promotion_basis`, `promotion_eligibility`, `artifact_id`, `source_message_id`, `supporting_*`, timestamps만 담는 read-only repackaging으로 유지했고, ordering은 `updated_at` 내림차순 후 `created_at`/id tie-breaker로 고정했습니다.
- `app/templates/index.html`의 기존 세션 영역 안에 compact `검토 후보` section을 추가했습니다. 이 section은 읽기 전용 copy만 보여 주고 button/action을 추가하지 않으며, save/reject/approval surface와 시각적으로 분리됩니다.
- `tests/test_web_app.py`에서 empty session의 `review_queue_items = []`, save support만 있을 때 queue 미포함, explicit confirmation 뒤 queue 포함, later correction 뒤 queue 제거, stale confirmation join 실패 시 queue 미포함을 회귀로 고정했습니다.
- `e2e/tests/web-smoke.spec.mjs`의 existing candidate-confirmation 시나리오를 최소 확장해 queue section의 visible/readonly/hidden lifecycle을 확인했고, README 및 루트 docs는 current shipped read-only review queue surface와 future review actions boundary에 맞게 동기화했습니다.

## 검증
- `python3 -m py_compile app/web.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_web_app`
- `python3 -m py_compile app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py`
- `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `Ran 160 tests in 1.738s`
  - `OK`
- `make e2e-test`
  - `11 passed (1.9m)`
- `git diff --check`
- `rg -n "durable_candidate|review_queue|eligible_for_review|candidate_confirmation_record|session_local_candidate|historical_save_identity_signal|superseded_reject_signal" app/templates/index.html app/web.py storage/session_store.py core/agent_loop.py tests/test_smoke.py tests/test_web_app.py e2e/tests/web-smoke.spec.mjs README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md`

## 남은 리스크
- 직전 closeout에서 남았던 “eligible current `durable_candidate`를 읽을 local surface 부재” 리스크는 이번 라운드에서 해소했습니다.
- 하지만 queue는 아직 inspection only입니다. `accept` / `edit` / `reject` / `defer`, rollback, reviewed-memory store, user-level memory는 여전히 없습니다.
- repeated-signal promotion은 여전히 막혀 있습니다. `candidate_family` alone으로는 merge/reopen을 열 수 없고, truthful recurrence key도 아직 없습니다.
- current `durable_candidate.candidate_id`를 source-message candidate id로 계속 재사용하고 있어서, later durable-scope id mint boundary는 여전히 open question입니다.
