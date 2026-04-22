# 2026-04-22 active round control seq selection

## 변경 파일
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/turn_arbitration.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `work/4/22/2026-04-22-active-round-control-seq-selection.md`

## 사용 skill
- `security-gate`: runtime control slot, active round surface, audit-facing status 선택 경로를 바꾸는 작업이라 local-first control boundary와 stop-slot 불변 조건을 확인했습니다.
- `finalize-lite`: 구현 종료 전 handoff 지정 검증, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 좁게 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크를 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- `.pipeline/implement_handoff.md` CONTROL_SEQ 753의 `active_round_selection_snapshot` handoff를 완료하기 위해서입니다.
- 같은 run 안에 여러 verify job state가 남았을 때 `RuntimeSupervisor._build_active_round()`가 현재 active control seq와 맞는 job을 먼저 선택해, launcher/controller/pipeline GUI의 `active_round` surface가 stale 최신 timestamp job에 끌려가지 않도록 하기 위해서입니다.

## 핵심 변경
- `RuntimeSupervisor._build_active_round(...)`에 `active_control` 인자를 추가하고, 기존 `active_control_snapshot_from_status()` helper로 읽은 현재 `active_control_seq`를 selection ranking의 첫 번째 기준으로 반영했습니다.
- active control seq가 없거나 유효하지 않으면 기존 liveness bucket, `updated_at`, `last_activity_at`, `job_id` tie-break 순서를 그대로 사용하게 했습니다.
- `_write_status()`의 preview/final active round 계산에서 현재 `active_control_block`을 `_build_active_round(...)`에 전달하도록 연결했습니다.
- `pipeline_runtime/turn_arbitration.py`의 raw `active_control_*` dict 접근을 `active_control_snapshot_from_status()` 기반으로 교체했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 current control seq match가 timestamp보다 우선하는 positive case와 active control이 없을 때 timestamp fallback이 유지되는 case를 추가했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/turn_arbitration.py` 통과
- `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration` 통과 (`142 tests`)
- `git diff --check` 통과

## 남은 리스크
- 이번 slice는 handoff 제약에 따라 `app/`, `core/`, `storage/`, `verify_fsm.py`, `watcher_core.py`, `pipeline_runtime/schema.py`, `lane_surface.py`, `pipeline_gui/`를 수정하지 않았습니다.
- `pipeline_runtime/supervisor.py`와 주변 runtime/schema 계열에는 이번 라운드 이전부터 존재하던 dirty 변경이 섞여 있습니다. 이번 closeout은 CONTROL_SEQ 753에서 요구한 active-round selection 연결만 다룹니다.
- 변경은 runtime 내부 selection 기준과 단위 테스트에 한정되어 별도 제품 문서 동기화는 필요 없다고 판단했습니다.
