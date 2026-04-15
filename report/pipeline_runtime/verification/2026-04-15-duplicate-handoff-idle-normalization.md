# 2026-04-15 duplicate handoff idle normalization verification

## 변경 파일
- 없음

## 사용 skill
- 없음

## 변경 이유
- duplicate/no-op implement handoff 이후 Claude가 실제로는 다음 control 대기인데도 `WORKING`으로 남는 정지 표면이 runtime/status/controller/launcher에 다시 나오지 않는지 확인하기 위해 검증했습니다.

## 핵심 변경
- watcher의 soft-complete triage가 `handoff_sha`를 함께 남기는지 확인했습니다.
- supervisor가 duplicate marker를 읽어 `control_duplicate_ignored`를 쓰고 Claude lane을 `READY + waiting_next_control`로 내리는 회귀를 확인했습니다.
- wrapper `TASK_DONE.reason=duplicate_handoff`와 launcher detail surface를 함께 확인했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_duplicate_handoff_task_hint_closure_emits_reason_once`
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_surfaces_duplicate_handoff_as_ready_and_emits_duplicate_event`
- `python3 -m unittest -v tests.test_pipeline_launcher.TestPipelineLauncherSessionContract.test_duplicate_handoff_ready_note_is_rendered_truthfully`
- `python3 -m unittest -v tests.test_watcher_core.ClaudeImplementBlockedTest.test_already_completed_handoff_soft_blocks_after_settle`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental synthetic-soak --duration-sec 30 --sample-interval-sec 1 --min-receipts 1 --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-15-synthetic-soak-short-duplicate-handoff.md`
- `python3 scripts/pipeline_runtime_gate.py --project-root /home/xpdlqj/code/projectH --mode experimental fault-check --report /home/xpdlqj/code/projectH/report/pipeline_runtime/verification/2026-04-15-fault-check-duplicate-handoff.md`

## 남은 리스크
- short synthetic soak와 fault-check는 통과했지만, 문서 채택 기준의 최신 6h/24h synthetic soak는 아직 남아 있습니다.
- `tests.test_pipeline_gui_app` 전체 묶음은 한 차례 tempdir cleanup 타이밍 에러가 있었으나, 같은 테스트 단독 재실행과 suite 재실행은 통과했습니다. 이번 duplicate handoff slice와 직접 연결된 회귀로 보이지는 않지만, setup-mode cleanup 타이밍은 계속 관찰이 필요합니다.
