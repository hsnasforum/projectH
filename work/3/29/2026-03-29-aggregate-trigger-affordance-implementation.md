## 변경 파일
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
- `plandoc/2026-03-29-reviewed-memory-apply-trigger-source-contract.md`

## 사용 skill
- `mvp-scope`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 existing shell에 aggregate-level reviewed-memory trigger surface가 없어 `review_queue_items` 기반 source-message review와 future aggregate-level transition initiation boundary가 UX상 섞여 보인다는 점이었습니다.
- 이번 라운드의 목표는 실제 `future_reviewed_memory_apply` 실행이 아니라, current blocked truth를 깨지 않으면서 one separate aggregate-level blocked-but-visible trigger affordance를 existing shell에 정직하게 드러내는 것이었습니다.

## 핵심 변경
- existing shell session stack에 `검토 후보` 바로 아래 one separate aggregate-level `검토 메모 적용 후보` section을 추가했습니다.
- 새 section은 current `session.recurrence_aggregate_candidates`만 소비하며, aggregate가 없으면 숨기고 aggregate가 있으면 card list를 렌더링합니다.
- 각 aggregate card는 aggregate identity summary, recurrence count, last seen, current `reviewed_memory_capability_status.capability_outcome`, current `reviewed_memory_transition_audit_contract.audit_stage`, planning target label, blocked helper copy를 보여 줍니다.
- 각 aggregate card에는 `검토 메모 적용 시작` action을 노출하되 current truth에 맞게 disabled 상태로만 렌더링합니다.
- blocked affordance는 note input, `canonical_transition_id`, `emitted_at`, `reviewed_memory_transition_record`, reviewed-memory apply result를 열지 않도록 유지했습니다.
- `review_queue_items` / `검토 후보` / `candidate_review_record` semantics는 그대로 유지했고, `검토 수락`과 `검토 메모 적용 시작`이 서로 다른 surface에 남도록 분리했습니다.
- focused regression을 추가해 aggregate section hidden/render 조건, disabled action 노출, helper copy, queue separation, current `reviewed_memory_transition_record` absence를 확인했습니다.
- README와 root docs, plandoc를 현재 shipped blocked affordance 상태와 12-scenario browser smoke 기준으로 동기화했습니다.

## 검증
- 실행: `python3 -m py_compile app/web.py tests/test_smoke.py tests/test_web_app.py`
- 실행: `python3 -m unittest -v tests.test_smoke tests.test_web_app`
- 실행: `make e2e-test`
- 실행: `git diff --check`
- 실행: `rg -n "검토 메모 적용 시작|recurrence_aggregate_candidates|reviewed_memory_transition_record|reviewed_memory_transition_audit_contract|review_queue_items" app/templates/index.html app/web.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md plandoc/2026-03-29-reviewed-memory-apply-trigger-source-contract.md`

## 남은 리스크
- 이번 라운드에서 해소한 리스크:
  - existing shell 안에서 aggregate-level transition initiation boundary가 아예 보이지 않아 `review_queue_items`와 future reviewed-memory trigger source가 혼동되던 UX 리스크를 줄였습니다.
- 여전히 남은 리스크:
  - current repo에는 아직 truthful `unblocked_all_required` path가 없어 disabled affordance 이상으로 넓힐 수 없습니다.
  - `operator_reason_or_note`, `canonical_transition_id`, `emitted_at`, emitted `reviewed_memory_transition_record`, reviewed-memory apply result는 아직 닫혀 있습니다.
  - `task_log` mirror, repeated-signal promotion, cross-session counting, user-level memory는 여전히 later scope입니다.
