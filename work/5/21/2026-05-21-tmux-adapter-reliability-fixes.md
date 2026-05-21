# 2026-05-21 tmux adapter reliability fixes

## 변경 파일
- `pipeline_runtime/tmux_adapter.py` 수정
- `pipeline_runtime/supervisor.py` 수정
- `tests/test_tmux_adapter.py` 수정
- `tests/test_pipeline_runtime_supervisor.py` 수정
- `work/5/21/2026-05-21-tmux-adapter-reliability-fixes.md` 신규 작성

## 사용 skill
- `security-gate`: tmux shell/runtime control 변경이 local-first 범위와 operator 승인 경계를 완화하지 않는지 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `subprocess.run(timeout=...)` 예외가 tmux scaffold/spawn 계층으로 전파되어 런타임이 크래시될 수 있었습니다.
- `create_scaffold()` 중간 실패 시 부분 생성된 tmux session이 남아 다음 기동에서 `session already exists` 계열 오류를 만들 수 있었습니다.
- `_build_lane_statuses()`가 lane별 `pane_for_lane()` 경로를 반복 호출해 status poll마다 pane 목록을 불필요하게 재조회했습니다.
- `restart_lane()`이 기존 lane 종료 없이 `spawn_lane()`만 호출해 "재시작" 의미와 맞지 않았습니다.

## 핵심 변경
- `TmuxAdapter._run()`이 `subprocess.TimeoutExpired`를 잡아 `returncode=1`인 `CompletedProcess`를 반환하도록 변경했습니다.
- `create_scaffold()`에서 `new-session` 이후 필수 단계 실패가 발생하면 `kill_session()`으로 부분 생성 session을 롤백하도록 했습니다. 기존 cosmetic option failure 허용 동작은 유지했습니다.
- `get_pane_map()`, `cache_pane_map()`, `clear_pane_map_cache()`를 추가하고, `_build_lane_statuses()`가 status poll 시작 시 pane snapshot을 한 번만 읽어 lane health와 tail capture 경로에서 재사용하도록 했습니다.
- `kill_lane()`을 추가하고 `restart_lane()`을 `kill_lane()` 후 `spawn_lane()` 순서로 재구현했습니다. 현재 layout 보존을 위해 pane 자체 삭제 대신 `respawn-pane -k`로 lane 프로세스를 종료한 뒤 재생성합니다.
- adapter 회귀 테스트에 timeout 처리, scaffold rollback, restart 순서를 추가했고, supervisor 회귀 테스트에 status poll당 pane snapshot 1회 사용을 고정했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/tmux_adapter.py pipeline_runtime/supervisor.py tests/test_tmux_adapter.py tests/test_pipeline_runtime_supervisor.py`
- 통과: `python3 -m unittest tests.test_tmux_adapter -v`
  - 결과: `Ran 10 tests`, `OK`
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_lane_statuses_reuses_single_pane_snapshot_for_status_poll`
  - 결과: `Ran 1 test`, `OK`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: `Ran 215 tests`, `OK`
- 통과: `git diff --check -- pipeline_runtime/tmux_adapter.py pipeline_runtime/supervisor.py tests/test_tmux_adapter.py tests/test_pipeline_runtime_supervisor.py`

## 남은 리스크
- `_build_lane_statuses()`의 pane snapshot cache는 정상 return 경로에서 해제됩니다. status 조립 중 예상 밖 예외가 발생하는 경로는 이번 슬라이스에서 별도 구조 변경하지 않았습니다.
- `kill_lane()`은 tmux pane layout을 보존하기 위해 실제 `kill-pane`이 아니라 `respawn-pane -k "exec bash"`를 사용합니다. pane 삭제/재분할 방식이 필요하면 별도 슬라이스에서 scaffold layout 복원 정책과 함께 다뤄야 합니다.
- 이번 변경은 tmux adapter 신뢰성 보강에 한정했고, commit, push, PR 생성, merge, release, publication은 실행하지 않았습니다.
- `.pipeline/config/agent_profile.json`, runtime policy 관련 파일, 기존 `/work`/`verify` dirty 항목은 이번 슬라이스 이전부터 존재한 변경이며 되돌리지 않았습니다.
