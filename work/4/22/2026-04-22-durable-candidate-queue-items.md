# 2026-04-22 durable candidate queue items

## 변경 파일
- `app/serializers.py`
- `app/static/app.js`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`
- `work/4/22/2026-04-22-durable-candidate-queue-items.md`

## 사용 skill
- `doc-sync`: `durable_candidate`와 `review_queue_items`의 실제 serialized shape를 README/spec/architecture/acceptance/backlog 문서에 맞췄습니다.
- `release-check`: 실행한 검증, 미실행 범위, 문서 동기화 상태, 남은 리스크를 분리했습니다.
- `finalize-lite`: 구현 종료 전 focused verification과 `/work` closeout 준비 상태를 점검했습니다.
- `work-log-closeout`: 변경 파일, 검증 결과, 남은 리스크를 이 persistent `/work` 기록으로 남겼습니다.

## 변경 이유
- seq 729 handoff는 기존 `candidate_confirmation_record` anchor에서 read-only `durable_candidate` projection을 만들고, 기존 `review_queue_items`에 같은 후보가 보이도록 요구했습니다.
- 기존 구현은 `durable_candidate` projection과 queue row를 이미 노출하고 있었지만, direct anchor field, `derived_from`, `derived_at`, queue discriminator가 명시적으로 고정되지 않았습니다.
- 이번 변경은 새 store, 새 endpoint, 새 approval flow, 새 UI action vocabulary 없이 기존 session payload와 review queue serializer만 보강합니다.

## 핵심 변경
- `durable_candidate`에 direct `artifact_id`, `source_message_id`, `derived_from`, `derived_at`를 추가했습니다.
- `derived_from`은 `record_type = candidate_confirmation_record`, anchor id, `candidate_id`, `candidate_updated_at`, `confirmation_label`, `recorded_at`만 담는 read-only provenance object로 고정했습니다.
- `review_queue_items` row에 `item_type = durable_candidate`, `candidate_scope`, `derived_from`, `derived_at`를 추가해 session-local 후보와 구분할 수 있게 했습니다.
- 브라우저 review queue meta는 기존 queue UI 안에서만 `유형 durable_candidate`를 표시합니다. 새 버튼, 새 review action, 새 approval surface는 추가하지 않았습니다.
- 문서는 durable projection이 현재 session payload에서만 계산되며 reviewed-memory/user-level promotion이나 cross-session promotion을 추가하지 않는다고 맞췄습니다.

## 검증
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support tests.test_web_app.WebAppServiceTest.test_durable_candidate_requires_exact_current_candidate_confirmation_join tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_records_source_message_trace_and_removes_pending_queue_item` -> 3 tests OK
- `python3 -m py_compile app/serializers.py app/static/app.js tests/test_web_app.py` -> 실패. `app/static/app.js`를 Python compile 대상에 잘못 포함해 `IndentationError: unexpected indent (app.js, line 1)`가 났습니다.
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_candidate_confirmation_records_candidate_linked_trace_and_stays_separate_from_save_support tests.test_web_app.WebAppServiceTest.test_durable_candidate_requires_exact_current_candidate_confirmation_join tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_accept_records_source_message_trace_and_removes_pending_queue_item tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_reject_records_and_removes_queue_item tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_defer_records_and_removes_queue_item` -> 5 tests OK
- `python3 -m py_compile app/serializers.py tests/test_web_app.py` -> 통과
- `python3 -m unittest tests.test_smoke.SmokeTest.test_recurrence_aggregate_candidates_helper_requires_exact_identity_and_distinct_anchors` -> 1 test OK
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_reject_records_and_removes_queue_item_with_sqlite_backend tests.test_web_app.WebAppServiceTest.test_submit_candidate_review_defer_records_and_removes_queue_item_with_sqlite_backend` -> 2 tests OK
- `node --check app/static/app.js` -> 통과
- `git diff --check -- app/serializers.py app/static/app.js tests/test_web_app.py README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md` -> 통과

## 남은 리스크
- 전체 `tests.test_web_app`와 Playwright smoke는 실행하지 않았습니다. 이번 slice는 serializer projection, existing review queue payload, 작은 queue meta label에 한정해 focused unittest와 `node --check`로 확인했습니다.
- `durable_candidate.statement`는 현재 persisted confirmation record 단독이 아니라 기존 matching `session_local_candidate`와 confirmation anchor의 exact join에서 계산됩니다. 이번 변경은 그 join의 provenance를 `derived_from`으로 명시했으며 새 durable store를 추가하지 않았습니다.
- 작업 전부터 다른 pipeline/runtime/docs/report/work 파일들이 dirty 상태였습니다. 이번 라운드는 handoff 범위 파일만 수정했고 기존 변경은 되돌리지 않았습니다.
- commit, push, branch/PR publish, `.pipeline/gemini_request.md`, `.pipeline/operator_request.md` 작성은 수행하지 않았습니다.
