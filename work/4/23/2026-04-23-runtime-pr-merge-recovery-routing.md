# 2026-04-23 runtime PR merge recovery routing

## 변경 파일
- `pipeline_runtime/automation_health.py`
- `pipeline_runtime/supervisor.py`
- `watcher_core.py`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- `work/4/23/2026-04-23-runtime-pr-merge-recovery-routing.md`

## 사용 skill
- `security-gate`: PR merge gate recovery가 operator/publication boundary를 우회하지 않고, 이미 해소된 gate만 verify follow-up으로 회수되는지 점검.
- `finalize-lite`: 테스트/문서 동기화 필요 여부와 `/work` closeout 준비 상태를 마무리 확인.
- `release-check`: 실행한 검증과 미실행 검증을 분리하고, 런타임 제어 표면 변경의 남은 리스크를 정리.
- `work-log-closeout`: 이번 구현 라운드의 변경 파일, 검증, 남은 리스크를 한국어 `/work` 노트로 기록.

## 변경 이유
- PR #29 merge 후 `.pipeline/operator_request.md`는 같은 `CONTROL_SEQ: 14` 내용을 유지했지만, 외부 PR 상태는 `MERGED`로 바뀌었다. 기존 watcher는 operator 파일 signature 변화에 주로 반응해서 `OPERATOR_WAIT`가 남을 수 있었다.
- `signal_mismatch`는 새 seq 13 handoff가 들어온 직후 이전 seq 12 wrapper task/receipt 신호가 섞이며 "새 handoff와 맞지 않는 작업 중"으로 표면화된 주의 상태였다.
- 사용자가 명시적으로 subagent 활용을 요청했기 때문에, PR merge recovery와 `signal_mismatch` 원인을 분리 조사한 뒤 한 번의 runtime 복구 slice로 묶었다.

## 핵심 변경
- `watcher_core.py`에 operator 파일 변경이 없어도 recoverable operator control을 재평가하는 `_check_operator_recovery_without_signal()` 경로를 추가하고, `_poll()`에서 pipeline signal 확인 직후 실행한다.
- `watcher_core.py`의 operator recovery 전환/알림을 `_route_operator_recovery()`로 모아 PR merge completed/head mismatch, 승인 완료, stale operator control 회수 경로가 같은 audit 이벤트와 중복 방지 key를 쓰게 했다.
- `pipeline_runtime/supervisor.py`는 stale operator control이 해소된 경우 status/compat `turn_state`를 `VERIFY_FOLLOWUP`으로 노출하고, `active_control_status`는 `none`으로 유지해 GUI가 operator wait로 고착되지 않게 했다.
- `pipeline_runtime/supervisor.py`는 verify receipt 작성 시 현재 active control seq보다 job의 `dispatch_control_seq`를 우선해 이전 seq verify receipt가 새 handoff seq에 잘못 귀속되지 않게 했다.
- `pipeline_runtime/supervisor.py`는 `already_done` / `already_implemented` blocked reason도 duplicate handoff family로 정규화하고, stale lower-seq wrapper task는 새 implement handoff의 `signal_mismatch`로 과대 표시하지 않게 했다.
- `pipeline_runtime/automation_health.py`는 `pr_merge_completed` / `pr_merge_head_mismatch` recovery의 next action을 `verify_followup`으로 분류한다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_runtime/supervisor.py pipeline_runtime/automation_health.py tests/test_watcher_core.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_automation_health.py` → 통과.
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v` → 1차 실행에서 새 stale lower-seq 테스트 1개 실패. 원인은 stale `accepted_task`가 더 위 분기에서 `WORKING`으로 고정되던 경로였고, 보정 후 재검증했다.
- `python3 -m unittest tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_lane_statuses_ignores_stale_lower_seq_task_for_new_handoff -v` → 통과.
- `python3 -m unittest tests.test_pipeline_runtime_automation_health tests.test_pipeline_runtime_supervisor tests.test_watcher_core -v` → 358개 테스트 통과.
- `.pipeline/current_run.json`과 `.pipeline/runs/20260423T042237Z-p41181/status.json` 확인 → 현재 runtime은 `RUNNING`, automation health는 `ok`, next action은 `continue`, active control은 `.pipeline/implement_handoff.md` seq 15다. 기존 seq 14 `operator_request.md`는 stale 목록에만 남는다.

## 남은 리스크
- 장시간 soak나 실제 tmux 재시작 검증은 실행하지 않았다. 이번 확인은 compile, targeted/full unittest, live status 파일 확인까지다.
- operator/publication boundary 자체는 유지된다. 이 변경은 이미 해소된 PR merge gate를 verify follow-up으로 회수하는 runtime surface이며, PR merge 실행이나 publish 권한을 새로 자동화하지 않는다.
- `verify/4/23/2026-04-23-milestone12-axis3-trace-quality-scoring.md`는 이번 라운드 전부터 dirty 상태였고 수정하지 않았다. 커밋 범위 정리 시 별도 판단이 필요하다.
