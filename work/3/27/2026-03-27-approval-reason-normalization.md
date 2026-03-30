# 2026-03-27 approval-reason-normalization

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
- `work/3/27/2026-03-27-approval-reason-normalization.md`

## 사용 skill
- `approval-flow-audit`: approval payload, pending approval, reject/reissue flow invariants를 다시 확인했습니다.
- `security-gate`: approval-based write safety와 local audit boundary가 유지되는지 점검했습니다.
- `doc-sync`: approval/session/task-log contract 변경을 문서에 맞췄습니다.
- `release-check`: 실제 실행한 검증만 남기고 미실행 검증을 분리했습니다.
- `work-log-closeout`: 오늘 closeout 형식과 남은 리스크를 표준 섹션으로 정리했습니다.

## 변경 이유
- 이전 closeout에서 이어받은 리스크:
  - grounded-brief anchor, original-response snapshot, `accepted_as_is` corrected outcome까지는 구현됐지만 approval reject / reissue reason은 아직 비어 있었습니다.
  - approval friction trace가 content outcome과 섞일 위험이 남아 있었습니다.
  - response/session/task-log 중 어디에 approval-linked reason을 canonical하게 둘지 코드로 고정되지 않았습니다.
- 이번 라운드에서 해소한 리스크:
  - reject / reissue 전용 `approval_reason_record` 최소 contract를 실제 코드에 추가했습니다.
  - original grounded-brief message의 `corrected_outcome`과 approval friction trace를 분리했습니다.
  - response, session, pending approval, task-log에서 같은 `artifact_id`, `source_message_id`, `approval_id`를 따라 reason linkage를 복원할 수 있게 했습니다.
- 여전히 남은 리스크:
  - 현재 UI에는 reject / reissue 세부 이유를 입력하는 surface가 없어 richer label을 truthfully 수집할 수 없습니다.
  - `corrected` / `rejected` content outcome은 여전히 구현되지 않았고, approval rejection과 content rejection을 연결하지 않습니다.
  - separate artifact store, review queue, user-level memory는 계속 future work입니다.

## 핵심 변경
- `core/approval.py`
  - `approval_reason_record` normalization helper를 추가했습니다.
  - 현재 truthful minimum label set을 `approval_reject -> explicit_rejection`, `approval_reissue -> path_change`로 고정했습니다.
  - `ApprovalRequest`가 optional `approval_reason_record`를 직렬화하도록 확장했습니다.
- `core/agent_loop.py`
  - reject / reissue 시 original grounded-brief source message를 찾아 `source_message_id`를 채운 `approval_reason_record`를 생성합니다.
  - reissue는 새 approval object와 response payload에 같은 reason record를 붙이고, reject는 approval-linked system response에만 남깁니다.
  - `approval_rejected`, `approval_reissued`, `agent_response` task-log detail에 같은 reason record를 남깁니다.
- `storage/session_store.py`
  - message와 pending approval에 `approval_reason_record`를 additive optional field로 normalize합니다.
  - same-artifact grounded-brief source message lookup helper를 추가해 `source_message_id` linkage를 재사용합니다.
  - legacy session / approval load가 깨지지 않도록 optional field 중심으로 유지했습니다.
- `app/web.py`
  - response/session/pending approval serialization에 `approval_reason_record`를 추가했습니다.
  - current UI panel은 그대로 두고 API/session payload만 확장했습니다.
- 테스트와 문서
  - reject / reissue reason record가 response, session, pending approval, task-log에 모두 남는 focused regression을 추가했습니다.
  - root docs를 현재 구현 truth에 맞게 동기화했습니다.

## 검증
- 실행함:
  - `python3 -m py_compile core/approval.py core/agent_loop.py app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check`
  - `rg -n "reason_scope|reason_label|reason_note|approval_reject|approval_reissue" core/approval.py core/agent_loop.py app/web.py storage/session_store.py tests/test_smoke.py tests/test_web_app.py docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md README.md`
- 미실행:
  - `python3 -m unittest -v`
  - `make e2e-test`

## 남은 리스크
- 이전 closeout에서 이어받은 `approval reject / reissue reason normalization 부재`는 해소했습니다.
- 이번 라운드에서 해소하지 않은 리스크:
  - richer reject / reissue label을 위한 explicit user-input surface 부재
  - `corrected` / `rejected` content outcome과 corrected text persistence 부재
  - review queue, reviewed scope, rollback trace, user-level memory 부재
- 다음 slice 후보:
  - `corrected` / `rejected` content outcome을 truthfully 기록할 수 있는 UI/flow 계약 먼저 고정
  - reject / reissue reason을 richer label로 넓히기 전에 explicit input surface가 필요한지 설계
  - eval fixture에서 approval friction count를 현재 minimum labels 기준으로 어떻게 집계할지 정리
