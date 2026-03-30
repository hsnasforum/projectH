## 변경 파일
- `core/agent_loop.py`
- `work/3/27/2026-03-27-original-draft-save-helper-refactor.md`

## 사용 skill
- `approval-flow-audit`
- `security-gate`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 이어받은 리스크는 current original-draft save path가 search summary, uploaded file summary, direct file summary, pending approval execute에 중복되어 future corrected-save bridge action이 들어올 때 trace 분기가 더 늘어날 수 있다는 점이었습니다.
- 이번 라운드에서는 shipped behavior를 바꾸지 않고, approval request 조립과 save execution trace 조립만 helper로 추출해 later corrected-save bridge action이 reuse할 내부 기반을 먼저 만들었습니다.

## 핵심 변경
- `_request_save_note_approval(...)`를 추가해 current original-draft save approval request path의 공통 조립을 한곳으로 모았습니다.
  - `_build_save_note_approval(...)`
  - pending approval 저장
  - `approval_requested` task-log detail 조립
- `_execute_save_note_write(...)`를 추가해 current save execution 공통 로직을 한곳으로 모았습니다.
  - `write_note` 실행
  - `write_note` task-log detail 조립
  - approval execute path에서만 optional `accepted_as_is` source-message 기록
- `_build_grounded_brief_source_response_fields(...)`를 추가해 grounded-brief source response에 반복되던 `artifact_id` / `artifact_kind` / `message_id` / `source_message_id` / save metadata 조립을 줄였습니다.
- search summary, uploaded file summary, direct file summary의 original-draft save request/direct save call-site와 `_execute_pending_approval(...)`가 위 helper를 재사용하도록 정리했습니다.
- 이번 라운드에서 해소한 리스크는 current original-draft save path의 중복 trace assembly가 future corrected-save 확장 전에 한 번 더 정리되지 않은 상태였다는 점입니다.

## 검증
- 실행:
  - `python3 -m py_compile core/agent_loop.py core/approval.py app/web.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check`
  - `rg -n "save_content_source|source_message_id|approval_requested|approval_granted|write_note|corrected_outcome" core/agent_loop.py core/approval.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py`
- 미실행:
  - `python3 -m unittest -v`
  - `make e2e-test`

## 남은 리스크
- corrected-save bridge action과 immutable corrected snapshot save path는 아직 구현되지 않았습니다. 다음 슬라이스에서는 이번 helper를 기반으로 `save_content_source=corrected_text` 경로를 별도 explicit action으로 연결해야 합니다.
- current helper는 current original-draft save semantics를 기준으로만 묶었습니다. corrected-save path가 추가되면 bridge action에서 어떤 snapshot body를 approval preview에 고정할지 별도 helper 경계를 다시 확인해야 합니다.
- 테스트 파일 자체는 바꾸지 않았고, 기존 focused regression으로 behavior 보존을 확인했습니다. 이후 corrected-save path를 추가할 때는 helper reuse를 직접 검증하는 focused regression을 더 얹는 편이 안전합니다.
