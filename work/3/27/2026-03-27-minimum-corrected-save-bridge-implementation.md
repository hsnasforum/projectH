## 변경 파일
- `app/templates/index.html`
- `app/web.py`
- `core/agent_loop.py`
- `core/approval.py`
- `storage/session_store.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`

## 사용 skill
- `frontend-skill`
- `approval-flow-audit`
- `security-gate`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 직전 closeout에서 남은 리스크는 corrected-save bridge action이 아직 구현되지 않아, recorded `corrected_text`를 approval-gated save로 올리는 최소 truthful path가 비어 있다는 점이었습니다.
- 이번 라운드에서는 current original-draft save path를 유지한 채, response card correction area에서 시작하는 최소 corrected-save bridge action만 additive하게 구현해야 했습니다.
- 특히 unsaved editor state를 approval snapshot으로 올리면 안 되고, older pending approval를 auto-rebase 하지 않는다는 계약을 실제 코드와 trace에 반영할 필요가 있었습니다.

## 핵심 변경
- correction area에 `이 수정본으로 저장 요청` action을 추가하고, recorded `corrected_text`가 있을 때만 동작하도록 분리했습니다.
- bridge action은 textarea의 현재 값이 아니라 source message에 이미 기록된 `corrected_text`만 읽어서 fresh approval를 생성하도록 구현했습니다.
- 새 approval는 same `artifact_id`, same `source_message_id`, `save_content_source = corrected_text`를 유지하고, request-time `corrected_text`로 `note_text` / `preview_markdown`을 고정합니다.
- 이후 correction을 다시 제출해도 기존 pending corrected-save approval snapshot은 바뀌지 않도록 immutable approval contract를 유지했습니다.
- corrected-save approval execution은 저장 결과를 source message에 다시 `accepted_as_is`로 덮지 않고, 기존 `corrected_outcome.outcome = corrected`를 유지한 채 optional `approval_id` / `saved_note_path`만 보강하도록 정리했습니다.
- current original-draft save path의 `save_content_source = original_draft`, explicit `source_message_id`, approval / write trace shape는 그대로 유지했습니다.
- README와 product/spec/architecture/acceptance/milestone/backlog/next-steps 문서를 현재 shipped truth에 맞춰 동기화했습니다.

## 검증
- 실행:
  - `python3 -m py_compile app/web.py core/agent_loop.py core/approval.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check`
  - `rg -n "save_content_source|corrected_text|source_message_id|approval_id|preview_markdown|pending_approvals|correction" app/templates/index.html app/web.py core/agent_loop.py core/approval.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
- 미실행:
  - `python3 -m unittest -v`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 “recorded correction을 save target으로 올리는 explicit bridge path 부재” 리스크는 해소했습니다.
- 이번 라운드에서 “unsaved editor state가 approval snapshot으로 섞일 위험”과 “pending approval auto-rebase 해석” 리스크도 first slice 기준으로 해소했습니다.
- 여전히 남은 리스크는 corrected-save bridge action을 correction area에 항상 disabled 상태로 보여줄지, recorded correction이 생긴 뒤에만 노출할지를 아직 확정하지 않았다는 점입니다.
- 또한 source message의 최신 `corrected_text`와 이미 승인되어 저장된 immutable corrected-save snapshot이 달라질 수 있으므로, 이후 slice에서 approval card copy나 saved-history wording을 더 명확히 다듬을 여지는 남아 있습니다.
