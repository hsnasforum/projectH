# 2026-04-22 verify close chain snapshot

## 변경 파일
- `verify_fsm.py`
- `watcher_core.py`
- `pipeline_runtime/supervisor.py`
- `tests/test_verify_fsm.py`
- `work/4/22/2026-04-22-verify-close-chain-snapshot.md`

## 사용 skill
- `security-gate`: verify close chain과 `.pipeline` control slot read 경로를 바꾸는 작업이라 local-first runtime control, audit/status, stop-slot 경계를 확인했습니다.
- `finalize-lite`: 구현 종료 전 요구 검증 통과 여부, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 중간 실패와 최종 통과 결과를 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 747의 `verify_close_chain_snapshot` handoff를 완료하기 위해서입니다.
- verify FSM의 round-close 판단에서 control-side 변경 감지를 파일 signature 비교가 아니라 `PipelineControlSnapshot`의 active `control_seq` 비교로 먼저 판단하게 하여 launcher/watcher control-state drift를 줄이기 위해서입니다.

## 핵심 변경
- `verify_fsm.py`의 `StateMachine`에 optional `pipeline_dir`를 추가하고, `read_pipeline_control_snapshot()` 기반으로 active control seq를 읽는 helper를 추가했습니다.
- verify dispatch 시 snapshot active seq가 있으면 `job.dispatch_control_seq`를 갱신하고, snapshot이 비어 있으면 기존 prompt-context seq를 보존하도록 했습니다.
- `_handle_verify_running()`은 `pipeline_dir`가 있을 때 control-side close 판단을 `current_seq != job.dispatch_control_seq`로 수행하고, `pipeline_dir`가 없으면 기존 `compute_multi_file_sig()` fallback을 유지합니다.
- `watcher_core.py`의 `StateMachine(...)` 생성자에 `pipeline_dir=self.pipeline_dir`를 연결했습니다.
- `pipeline_runtime/supervisor.py`의 `_reconcile_receipts()`는 `active_control_snapshot_from_status()`로 control seq/file을 읽고, `receipt_written` event payload에도 해당 control 정보를 함께 남기게 했습니다.
- `tests/test_verify_fsm.py`를 추가해 snapshot seq 변경, 같은 seq 유지, `pipeline_dir=None` fallback을 검증했습니다.

## 검증
- `python3 -m py_compile verify_fsm.py pipeline_runtime/supervisor.py watcher_core.py pipeline_runtime/schema.py` 통과
- `python3 -m unittest tests.test_verify_fsm` 통과 (`3 tests`)
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_watcher_core` 1차 실행은 watcher 기존 prompt-context seq를 snapshot `-1`로 덮어써 4개 실패했습니다. 이후 snapshot seq가 없을 때 기존 `dispatch_control_seq`를 보존하도록 수정했습니다.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_watcher_core` 최종 통과 (`321 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 slice는 `verify_fsm.py`, `watcher_core.py`, `pipeline_runtime/supervisor.py`, `tests/test_verify_fsm.py` 범위로 제한했습니다. `lane_surface.py`, `pipeline_gui/`, `app/`, `core/`, `storage/`는 건드리지 않았습니다.
- `feedback_baseline_sig`, `verify_feedback_baseline_sig`, `compute_multi_file_sig()`는 삭제하지 않았고, `pipeline_dir=None` 호출자를 위한 fallback으로 유지했습니다.
- `watcher_core._build_verify_feedback_sigs()`는 verify-side signature를 얻기 위해 기존 builder 형태를 유지합니다. control-side close 판단은 `pipeline_dir`가 있을 때 `dispatch_control_seq` 비교 결과만 사용합니다.
- 최종 status에는 이번 라운드 이전부터 존재하던 `pipeline_gui/backend.py`, `pipeline_runtime/schema.py`, `tests/test_pipeline_runtime_schema.py`, `verify/4/22/2026-04-22-role-harness-pipeline-automation-handoff-verification.md`, `report/gemini/2026-04-22-axis2-or-resume.md`, `report/gemini/2026-04-22-post-cleanup-next-slice.md`, `verify/4/22/2026-04-22-post-cleanup-launcher-automation-realignment.md`, `work/4/22/2026-04-22-active-control-snapshot.md`, `work/4/22/2026-04-22-pipeline-control-shared-snapshot.md`, `work/4/22/2026-04-22-runtime-legacy-control-cleanup-closeout.md`가 별도 dirty 또는 untracked 항목으로 남아 있습니다. 이번 handoff에서는 해당 파일들을 되돌리거나 정리하지 않았습니다.
