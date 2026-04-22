# 2026-04-21 richer reason labels

## 변경 파일
- `core/contracts.py`
- `storage/session_store.py`
- `app/serializers.py`
- `app/handlers/feedback.py`
- `core/agent_loop.py`
- `tests/test_contracts.py`
- `tests/test_web_app.py`
- `tests/test_smoke.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `work/4/21/2026-04-21-richer-reason-labels.md`

## 사용 skill
- `approval-flow-audit`: corrected-save reissue의 `approval_reason_record` 라벨을 바꾸면서 승인/재발행 경계와 pending approval 감사성을 확인했습니다.
- `security-gate`: 승인 기반 쓰기 흐름의 payload/log 필드만 추가되고, 승인 전 쓰기/overwrite/default write 경계가 바뀌지 않았는지 점검했습니다.
- `doc-sync`: approval/correction payload 계약 변경을 README와 product/spec/architecture/acceptance/backlog/NEXT_STEPS 문서에 맞췄습니다.
- `release-check`: 실제 실행한 py_compile, unittest, diff check 결과와 남은 미실행 범위를 분리했습니다.
- `finalize-lite`: 구현 라운드 종료 전 focused verification, doc sync, `/work` closeout 준비 상태를 확인했습니다.
- `work-log-closeout`: 변경 파일, 검증 결과, 남은 리스크를 이 persistent `/work` 기록으로 남겼습니다.

## 변경 이유
- seq 725 handoff의 목표는 현재 shipped surface가 이미 구분하는 correction/reissue 원인을 더 명확한 reason label로 남기는 것이었습니다.
- 기존에는 correction submit이 `corrected_outcome.outcome = corrected`만 남겼고, corrected-save approval을 재발행해도 일반 `path_change`와 같은 `approval_reissue` 라벨만 남았습니다.
- 이번 변경은 새 UI, 새 approval flow, 새 store 없이 기존 explicit correction submit과 corrected-save reissue 경로에만 라벨을 추가합니다.

## 핵심 변경
- `core/contracts.py`에 `CorrectedOutcomeReasonLabel.EXPLICIT_CORRECTION_SUBMITTED`와 `ALLOWED_CORRECTED_OUTCOME_REASON_LABELS`를 추가하고, `approval_reissue` 허용 라벨에 `corrected_text_reissue`를 추가했습니다.
- `storage/session_store.py`가 corrected outcome의 optional `reason_label`을 정규화하고, explicit correction submit에는 `explicit_correction_submitted`를 기록합니다.
- corrected-save approval 실행 시 기존 corrected outcome을 보존하면서 `reason_label = explicit_correction_submitted`도 유지합니다.
- `core/agent_loop.py`는 reissue 대상 approval의 `save_content_source`가 `corrected_text`이면 `approval_reason_record.reason_label = corrected_text_reissue`를 사용하고, 일반 original-draft reissue는 기존 `path_change`를 유지합니다.
- serializer와 task-log mirror가 `corrected_outcome.reason_label`을 노출하도록 했습니다.
- content-level reject의 `content_reason_record` 라벨 확장은 하지 않았습니다. 현재 truthful surface는 기존 `explicit_content_rejection`과 optional `reason_note`뿐이라 새 content label을 만들 근거가 없습니다.

## 검증
- `python3 -m py_compile core/contracts.py storage/session_store.py app/serializers.py app/handlers/feedback.py core/agent_loop.py tests/test_contracts.py tests/test_web_app.py tests/test_smoke.py` → 통과
- `python3 -m unittest tests.test_contracts` → 47 tests OK
- `python3 -m unittest tests.test_web_app.WebAppServiceTest.test_submit_correction_updates_grounded_brief_source_message_and_logs tests.test_web_app.WebAppServiceTest.test_handle_chat_corrected_save_bridge_creates_immutable_approval_snapshot tests.test_web_app.WebAppServiceTest.test_handle_chat_corrected_save_reissue_uses_scoped_reason_label tests.test_web_app.WebAppServiceTest.test_handle_chat_can_reissue_pending_approval_with_new_path` → 4 tests OK
- `python3 -m unittest tests.test_smoke.SmokeTest.test_correction_updates_grounded_brief_source_message tests.test_smoke.SmokeTest.test_corrected_save_bridge_uses_recorded_snapshot_and_preserves_corrected_outcome tests.test_smoke.SmokeTest.test_corrected_save_reissue_uses_corrected_text_reason_label tests.test_smoke.SmokeTest.test_pending_approval_can_be_reissued_with_new_path` → 실패, 첫 테스트 이름 지정 착오(`SmokeTest`에 해당 이름 없음)
- `python3 -m unittest tests.test_smoke.SmokeTest.test_session_store_records_corrected_text_on_grounded_brief_source_message tests.test_smoke.SmokeTest.test_corrected_save_bridge_uses_recorded_snapshot_and_preserves_corrected_outcome tests.test_smoke.SmokeTest.test_corrected_save_reissue_uses_corrected_text_reason_label tests.test_smoke.SmokeTest.test_pending_approval_can_be_reissued_with_new_path` → 4 tests OK
- `git diff --check -- core/contracts.py storage/session_store.py app/serializers.py app/handlers/feedback.py core/agent_loop.py tests/test_contracts.py tests/test_web_app.py tests/test_smoke.py README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md work/4/21/2026-04-21-richer-reason-labels.md` → 통과

## 남은 리스크
- 브라우저 UI나 새 approval surface는 변경하지 않았으므로 Playwright는 실행하지 않았습니다.
- richer content/reject taxonomy는 아직 UI가 구체 라벨을 truthfully 수집하지 않으므로 intentionally skipped 상태입니다.
- 현재 작업 전부터 `.pipeline/README.md`, pipeline runtime/watch 관련 파일, 이전 `/work` 및 `report/gemini` 파일이 dirty/untracked 상태였습니다. 이번 라운드는 해당 파일들을 수정하지 않았습니다.
- commit, push, branch/PR publish, `.pipeline/gemini_request.md`, `.pipeline/operator_request.md` 작성은 수행하지 않았습니다.
