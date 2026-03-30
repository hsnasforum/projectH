## 변경 파일
- `core/approval.py`
- `core/agent_loop.py`
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
- `work/3/27/2026-03-27-grounded-brief-artifact-linkage-implementation.md`

## 사용 skill
- `approval-flow-audit`
- `security-gate`
- `doc-sync`
- `release-check`
- `work-log-closeout`

## 변경 이유
- 이전 closeout에서 이어받은 리스크:
  - 첫 memory trace slice가 문서로만 고정되어 있고 실제 `artifact_id` linkage는 아직 구현되지 않았음
  - approval / write / feedback trace가 같은 grounded-brief anchor를 공유하지 않았음
  - additive optional field 중심 구현과 현재 UI 유지가 필요했음
- 이번 라운드에서 해소한 리스크:
  - grounded-brief assistant message에 stable `artifact_id`, `artifact_kind`를 실제로 추가함
  - pending approval, approval outcome, write-note, feedback log detail까지 같은 `artifact_id`를 연결함
  - response/session serialization과 focused regression을 함께 맞춰 현재 계약을 깨지 않도록 고정함
- 여전히 남은 리스크:
  - legacy session / pending approval에는 `artifact_id` backfill이 없음
  - separate artifact store, corrected outcome store, review queue, user-level memory는 아직 없음
  - approval-backed save tuning과 이후 memory slice 순서는 계속 후속 설계가 필요함

## 핵심 변경
- `core/agent_loop.py`
  - grounded-brief summary/search/file response에 `artifact_id`, `artifact_kind = grounded_brief`를 부여함
  - save approval 생성 시 같은 `artifact_id`를 pending approval과 approval payload로 전달함
  - `approval_granted`, `approval_reissued`, `approval_rejected`, `write_note`, `agent_response` task-log detail에 `artifact_id`를 남김
  - reissue 시 approval id만 바뀌고 artifact anchor는 유지되도록 처리함
- `core/approval.py`
  - `ApprovalRequest`에 optional `artifact_id`를 추가하고 public/session record로 직렬화되게 함
- `app/web.py`
  - response payload와 approval payload에 artifact fields를 노출함
  - feedback 제출은 계속 `message_id`를 입력받되 `response_feedback_recorded` log detail에 resolved `artifact_id`를 직접 남기도록 함
- 테스트
  - `tests/test_smoke.py`, `tests/test_web_app.py`에 message / approval / pending approval / task-log / feedback linkage 회귀를 추가함
- 문서
  - current contract에는 additive trace anchor만 구현되었다는 점을 반영하고, corrected outcome / review queue / user-level memory는 계속 later stage로 분리함

## 검증
- 실행함:
  - `python3 -m py_compile core/approval.py core/agent_loop.py app/web.py storage/session_store.py storage/task_log.py tests/test_smoke.py tests/test_web_app.py`
  - `python3 -m unittest -v tests.test_smoke tests.test_web_app`
  - `git diff --check -- core/approval.py core/agent_loop.py app/web.py tests/test_smoke.py tests/test_web_app.py README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md work/3/27/2026-03-27-grounded-brief-artifact-linkage-implementation.md`
  - `rg -n 'artifact_id|artifact_kind|response_feedback_recorded|review queue|user-level memory|corrected outcome' README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/MILESTONES.md docs/TASK_BACKLOG.md docs/NEXT_STEPS.md core/approval.py core/agent_loop.py app/web.py tests/test_smoke.py tests/test_web_app.py work/3/27/2026-03-27-grounded-brief-artifact-linkage-implementation.md`

## 남은 리스크
- 이전 closeout에서 이어받은 리스크 중 `artifact_id linkage 부재`는 해소했습니다.
- 이번 라운드에서 해소하지 않은 리스크:
  - legacy trace backfill 여부
  - corrected outcome persistence의 최소 구조
  - review queue / user-level memory 이전에 필요한 snapshot normalization 범위
- 다음 slice 후보:
  - current assistant message를 기준으로 한 normalized original-response snapshot contract
  - `artifact_id`와 `message_id`를 재사용하는 corrected outcome linkage
