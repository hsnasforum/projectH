# 2026-04-22 pipeline control shared snapshot

## 변경 파일
- `pipeline_runtime/schema.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `pipeline_gui/backend.py`
- `tests/test_pipeline_runtime_schema.py`
- `work/4/22/2026-04-22-pipeline-control-shared-snapshot.md`

## 사용 skill
- `security-gate`: `.pipeline` control slot과 runtime status/control JSON 경로를 바꾸는 작업이라 local-first, audit/status, stop-slot 경계를 확인했습니다.
- `finalize-lite`: 구현 종료 전에 요구 검증, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크만 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 742의 `pipeline_launcher_shared_state_parsing` handoff를 완료하기 위해서입니다.
- watcher, supervisor, GUI backend가 role-based pipeline control slot의 active/stale 판단을 각자 재구성하지 않고 `pipeline_runtime.schema`의 공용 parsing/snapshot 표면을 쓰도록 하여 control-state drift를 줄이기 위해서입니다.

## 핵심 변경
- `pipeline_runtime/schema.py`에 `PipelineControlSnapshot`, `pipeline_control_snapshot_from_slots()`, `read_pipeline_control_snapshot()`을 추가해 `parse_control_slots()` 결과에서 active/stale snapshot과 원본 entry를 함께 제공하도록 했습니다.
- `watcher_core.py`의 control signal 탐색을 공용 `read_pipeline_control_snapshot()` 기반으로 바꾸고, watcher 내부의 별도 최신 control 비교 로직을 제거했습니다.
- `pipeline_runtime/supervisor.py`는 `pipeline_control_snapshot_from_slots()`를 통해 active control block을 만들도록 조정해 status/read 경로가 같은 snapshot helper를 거치게 했습니다.
- `pipeline_gui/backend.py`의 non-Windows control slot parser를 runtime 공용 `parse_control_slots()`로 연결했습니다. 기존 Windows/WSL subprocess parser는 그대로 유지했습니다.
- `tests/test_pipeline_runtime_schema.py`에 active/stale pipeline control snapshot 생성과 empty slots 허용 테스트를 추가했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/supervisor.py watcher_core.py watcher_prompt_assembly.py pipeline_gui/backend.py` 통과
- `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_supervisor tests.test_watcher_core` 통과 (`365 tests`)
- `python3 -m unittest tests.test_pipeline_gui_backend` 통과 (`48 tests`)
- `git diff --check` 통과

## 남은 리스크
- Windows/WSL GUI backend branch는 기존 command-adapter parser를 유지했습니다. 이번 slice는 non-Windows runtime parser 공유까지로 제한했습니다.
- status/control JSON의 기존 `active_control_*` key shape는 유지했습니다. schema version bump나 별도 사용자 문서 변경은 필요하다고 판단하지 않았습니다.
- 최종 status에는 `verify/4/22/2026-04-22-role-harness-pipeline-automation-handoff-verification.md`, `report/gemini/2026-04-22-axis2-or-resume.md`, `report/gemini/2026-04-22-post-cleanup-next-slice.md`, `verify/4/22/2026-04-22-post-cleanup-launcher-automation-realignment.md`, `work/4/22/2026-04-22-active-control-snapshot.md`, `work/4/22/2026-04-22-runtime-legacy-control-cleanup-closeout.md`가 별도 dirty 또는 untracked 항목으로 남아 있습니다. 이번 handoff에서는 해당 파일들을 수정하지 않았습니다.
