# 2026-05-21 Pipeline launcher Task 2 logic correctness

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_cli.py`
- `work/5/21/2026-05-21-pipeline-launcher-task2-logic-correctness.md`

## 사용 skill

- `security-gate`: tmux lane 재시작, wrapper 입력 자동 전송, runtime session 정리 경계가 바뀌므로 의도하지 않은 자동화 확대와 operator boundary를 확인했습니다.
- `work-log-closeout`: 변경 파일, 실패 확인, 검증 결과, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `docs/superpowers/plans/2026-05-21-pipeline-launcher-bugfixes.md`의 Task 2(P8/P11/P13/P16/P18)만 실행했습니다.
- `verify/5/21/2026-05-21-pipeline-launcher-task4ab-structural-stability.md`에서 Task 2가 다음 권장 슬라이스로 정리되어 있었습니다.
- 자동화 성공률보다 post-accept 작업 보호, tmux session 정리, wrapper 자동 입력의 명시성이 더 중요한 변경입니다.

## 핵심 변경

- P11: `_maybe_recover_lane()`의 post-accept BROKEN 차단을 implement owner 전용에서 모든 lane으로 확장했습니다. verify/advisory lane도 accepted task가 있으면 blind restart 없이 `*_interrupted_post_accept` reason을 반환합니다.
- P8: `_spawn_runtime_session()`에서 lane spawn 중간 실패 시 이미 생성된 lane이 있으면 session 전체를 정리하고 예외를 다시 올리게 했습니다. 현재 `TmuxAdapter`에는 `kill_lane`이 없으므로 요청 조건에 따라 `kill_session()` fallback을 사용했습니다.
- P16: Codex update prompt 자동 dismiss가 더 이상 `b"3\r"`를 고정 전송하지 않고, 화면 텍스트에서 `skip until next version` 항목 번호를 regex로 파싱해 해당 번호를 전송합니다. 항목을 못 찾을 때만 기존 `b"3\r"` fallback을 유지했습니다.
- P18: `_emit_task_done()`의 `control_seq` 변환을 `try/except`로 방어해 비정상 타입이 들어와도 `-1`로 fallback하게 했습니다.
- P13: `_terminate_current_run_watcher()`의 fingerprint 없는 legacy 경로에 주석을 추가해, fingerprint가 없을 때도 같은 repo cwd 매칭만 신뢰하고 cmdline만으로 kill 범위를 넓히지 않는 계약을 문서화했습니다.
- 각 항목에 실패 우선 테스트를 추가하고, 실패 확인 후 구현했습니다.

## 검증

- 수정 전 실패 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_maybe_recover_lane_blocks_verify_and_advisory_restart_post_accept tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_spawn_runtime_session_kills_session_on_lane_failure tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_codex_update_auto_dismiss_uses_parsed_number_not_hardcoded tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_emit_task_done_falls_back_for_invalid_control_seq`
  - 결과: 네 테스트가 모두 실패했습니다. verify/advisory post-accept lane이 차단되지 않았고, spawn 실패 시 session cleanup이 호출되지 않았으며, update prompt는 `b"3\r"`를 고정 전송했고, 비정상 `control_seq`에서 `TypeError`가 발생했습니다.
- 수정 후 focused 확인:
  - `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_maybe_recover_lane_blocks_verify_and_advisory_restart_post_accept tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_claude_post_accept_breakage_blocks_blind_replay tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_codex_pre_completion_breakage_restarts_within_retry_budget tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_spawn_runtime_session_kills_session_on_lane_failure tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_codex_update_prompt_is_auto_dismissed_with_skip_until_next_version tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_codex_update_auto_dismiss_uses_parsed_number_not_hardcoded tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_emit_task_done_falls_back_for_invalid_control_seq`
  - `Ran 7 tests in 0.014s` / `OK`.
- 지정 컴파일 확인:
  - `python3 -m py_compile pipeline_runtime/supervisor.py pipeline_runtime/cli.py`
  - 통과했습니다.
- 지정 전체 테스트 확인:
  - `python3 -m unittest tests.test_pipeline_runtime_supervisor tests.test_pipeline_runtime_cli -v`
  - `Ran 222 tests in 1.210s` / `OK`.
- whitespace 확인:
  - `git diff --check -- pipeline_runtime/supervisor.py pipeline_runtime/cli.py tests/test_pipeline_runtime_supervisor.py tests/test_pipeline_runtime_cli.py work/5/21`
  - closeout 작성 전후 모두 통과했습니다.

## 남은 리스크

- Task 3과 Task 4-C/D(P5/P7)는 이번 라운드 범위 밖이라 건드리지 않았습니다.
- Playwright, E2E, live runtime start/stop 검증은 요청 범위 밖이라 실행하지 않았습니다.
- 작업 시작 시점부터 대상 파일 일부는 기존 dirty 상태였고, 이 기록은 Task 2(P8/P11/P13/P16/P18) 변경만 설명합니다.
- commit, push, PR publish, merge, release는 수행하지 않았습니다.
