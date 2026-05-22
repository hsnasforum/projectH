# 2026-05-22 watcher status writer extraction

## 변경 파일
- `watcher_core.py`
- `watcher_status_writer.py`
- `tests/test_watcher_status_writer.py`

## 사용 skill
- `security-gate`: 런타임 status 파일 쓰기 경계가 로컬 `.pipeline/runs/<run>/status.json` 및 `current_run.json` 포인터 갱신에 머무르는지 확인했습니다.
- `finalize-lite`: 실행한 검증, 문서 동기화 필요 여부, `/work` closeout 준비 상태를 점검했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- CONTROL_SEQ 2152의 A3 Step 6 지시에 따라 `watcher_core.py`의 `_write_runtime_status()` 본문을 별도 writer 모듈로 분리해야 했습니다.
- `_build_lane_statuses()`와 다른 lane status builder는 Step 7 범위로 남겨 두어 이번 라운드에서 추출하지 않았습니다.

## 핵심 변경
- 새 `watcher_status_writer.py`를 추가해 runtime status payload 구성, active control snapshot 변환, automation health 파생, `status.json` 원자적 쓰기를 담당하게 했습니다.
- `WatcherCore._write_runtime_status()`는 active control, lane statuses, turn state, runtime controls를 계산한 뒤 새 `write_runtime_status()`에 위임하도록 축소했습니다.
- `_build_lane_statuses()`와 lane 상태 계산 로직은 `watcher_core.py`에 그대로 남겼습니다.
- 새 `tests/test_watcher_status_writer.py`에서 active control 경로, turn fallback 경로, status 파일 쓰기, exporter disabled 경로를 검증했습니다.
- security-gate 점검 결과 승인 요구, 외부 네트워크, 삭제/이동, 사용자 문서 저장 동작은 새로 추가되지 않았고 기존 로컬 runtime status 쓰기 경계만 유지됩니다.
- 제품/운영 문서 변경은 필요하지 않은 내부 리팩터링으로 판단해 문서 파일은 수정하지 않았습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_status_writer.py`
- 통과: `python3 -m unittest tests.test_watcher_status_writer -v`
  - 결과: 4 tests OK
- 통과: `python3 -m unittest tests.test_watcher_core -v`
  - 결과: 265 tests OK
  - 참고: handoff에는 264개로 적혀 있었지만, 작업 시작 전부터 있던 verify done deadline 테스트 추가분 때문에 현재 작업트리 기준 집계는 265개입니다.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v`
  - 결과: 548 tests OK
- 통과: `git diff --check -- watcher_core.py watcher_status_writer.py tests/test_watcher_status_writer.py`
  - 결과: PASS, 출력 없음

## 남은 리스크
- 브라우저/E2E는 실행하지 않았습니다. 이번 변경은 watcher runtime status writer 내부 리팩터링이고 handoff 검증 범위가 Python compile/unit으로 지정되어 있어 제외했습니다.
- 작업 시작 전부터 `.pipeline/config/agent_profile.json`, `.pipeline/config/runtime_policy.json`, `pipeline_runtime/cli.py`, `pipeline_runtime/supervisor.py`, 관련 테스트와 다수의 `work/`, `verify/`, `report/gemini/` 파일에 기존 dirty state가 있었습니다. 이번 라운드에서는 해당 기존 변경을 되돌리거나 수정하지 않았습니다.
- `watcher_core.py`에는 기존 dirty 변경인 verify done deadline 관련 diff도 함께 남아 있습니다. 이번 라운드의 직접 변경 범위는 runtime status writer 위임과 새 writer 테스트입니다.
