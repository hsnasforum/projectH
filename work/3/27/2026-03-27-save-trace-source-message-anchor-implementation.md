# 2026-03-27 save-trace-source-message-anchor-implementation

## 변경 파일
- `core/approval.py`
- `core/agent_loop.py`
- `storage/session_store.py`
- `app/web.py`
- `tests/test_smoke.py`
- `tests/test_web_app.py`
- `README.md`
- `docs/PRODUCT_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/ACCEPTANCE_CRITERIA.md`
- `docs/MILESTONES.md`
- `docs/TASK_BACKLOG.md`
- `docs/NEXT_STEPS.md`
- `work/3/27/2026-03-27-save-trace-source-message-anchor-implementation.md`

## 사용 skill
- `approval-flow-audit`: approval object, pending approval, approval outcome, write trace에 같은 anchor가 이어지는지 기준을 잡았습니다.
- `security-gate`: 승인 기반 저장, 로컬 세션 저장, 로컬 task-log가 기존 approval-safe 경계를 유지하는지 확인했습니다.
- `doc-sync`: approval/save trace contract 변경을 root docs와 README에 같은 current truth로 맞췄습니다.
- `release-check`: 실제 실행한 py_compile, focused unittest, grep, diff 결과만 남겼습니다.
- `work-log-closeout`: 오늘자 closeout을 표준 섹션으로 정리했습니다.

## 변경 이유
- 직전 closeout에서 이어받은 핵심 리스크는 current save approval / write trace가 `save_content_source`는 이미 갖고 있지만, original grounded-brief source message를 직접 가리키는 explicit `source_message_id` anchor는 아직 없다는 점이었습니다.
- 이 상태로 future corrected-save path를 추가하면, same `artifact_id`를 쓰더라도 어떤 source message 위의 correction/save trace인지 approval/write surface만으로 읽기가 애매해질 수 있었습니다.
- 이번 라운드에서는 corrected-save bridge action을 구현하지 않고도, current original-draft save path에 동일한 `source_message_id` contract를 먼저 심어 future trace 확장 시 shape가 다시 흔들리지 않게 해야 했습니다.

## 핵심 변경
- `ApprovalRequest`에 optional `source_message_id`를 추가하고, approval object / pending approval serialization / public approval payload에 같은 field를 노출하도록 정규화했습니다.
- current save approval를 만드는 grounded-brief response에서는 source message ID를 먼저 발급하고, 같은 값을 response message, approval payload, pending approval, `approval_requested` log detail에 같이 실었습니다.
- current save execution / reissue / reject path는 approval object에 실린 same `source_message_id`를 그대로 재사용하도록 맞췄습니다.
- `approval_granted`, `approval_reissued`, `approval_rejected`, `write_note`, `agent_response` detail과 save-related assistant message / response payload에 같은 `source_message_id`를 남겼습니다.
- legacy pending save approval load에서는 top-level `source_message_id`가 없어도, same `artifact_id`를 가진 grounded-brief source message가 있으면 `artifact_id -> source_message_id` backfill이 유지되도록 했습니다.
- current semantics는 그대로 유지했습니다:
  - `save_content_source = original_draft` only
  - current save path는 corrected text를 쓰지 않음
  - corrected-save bridge action / immutable corrected-save snapshot은 여전히 future work

## 검증
- 실행:
  - `python3 -m py_compile core/approval.py core/agent_loop.py app/web.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `rg -n "source_message_id|save_content_source|approval_granted|write_note" core/approval.py core/agent_loop.py app/web.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
  - `git diff --check`
- 미실행:
  - `python3 -m unittest -v`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 남아 있던 “current save path가 future corrected-save trace와 다른 anchor contract를 쓰게 될 수 있음” 리스크는 이번 라운드에서 줄였습니다.
- 이번 라운드에서 해소한 것은 current original-draft save approval / write trace가 explicit `source_message_id`를 approval object, response payload, session payload, task-log detail에서 일관되게 공유하도록 만든 점입니다.
- 여전히 남은 리스크는 future corrected-save bridge action이 아직 없다는 점입니다. 다음 슬라이스에서는:
  - 어떤 explicit action이 recorded `corrected_text`를 새 approval preview로 올리는지
  - `save_content_source = corrected_text`일 때 immutable approval snapshot을 어떻게 고정하는지
  - current original-draft path와 future corrected-save path를 UI copy와 audit trace에서 어떻게 더 분리할지를 구현해야 합니다.
