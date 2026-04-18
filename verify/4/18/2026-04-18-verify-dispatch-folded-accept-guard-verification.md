# 2026-04-18 verify dispatch folded accept guard verification

## 변경 파일
- `verify/4/18/2026-04-18-verify-dispatch-folded-accept-guard-verification.md`

## 사용 skill
- 없음

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-verify-dispatch-folded-accept-guard.md`가 same-dispatch `TASK_DONE`를 accept의 stronger evidence로 취급해 false `task_accept_missing` 재큐잉을 막았다고 주장하므로, 그 주장을 focused regression과 current runtime evidence 대조로 다시 확인해야 했습니다.

## 핵심 변경
- 현재 `verify_fsm.py::_mark_dispatch_accepted_if_seen(...)`는 `accepted_task`가 비어 있어도 `done_task.dispatch_id == job.dispatch_id`면 accept를 먼저 복구합니다. wrapper read model이 latest `TASK_DONE`를 반영하면서 `accepted_task`를 비운 뒤에도 current dispatch를 `task_accept_missing`으로 되감지하지 않도록 하는 의도와 구현이 일치합니다.
- 새 `tests.test_watcher_core.VerifyCompletionContractTest.test_matching_task_done_implies_accept_when_wrapper_model_already_folded_accept`는 `DISPATCH_SEEN/TASK_ACCEPTED/TASK_DONE/READY`가 실제 wrapper log에 다 있는 상황을 한 번에 읽었을 때, FSM이 VERIFY_PENDING 재큐잉 대신 current dispatch의 accept/done을 모두 복구하는지 확인합니다.
- current run evidence(`.pipeline/runs/20260418T082837Z-p114196`)도 다시 읽었습니다. `events.jsonl`에는 `task_accept_missing` requeue가, `wrapper-events/codex.jsonl`에는 같은 job의 first dispatch `DISPATCH_SEEN`과 second dispatch `TASK_ACCEPTED/TASK_DONE`가 남아 있어 latest `/work`가 잡은 incident family 분류는 현재 tree와 모순되지 않습니다.

## 검증
- `python3 -m py_compile verify_fsm.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_matching_task_done_implies_accept_when_wrapper_model_already_folded_accept tests.test_watcher_core.VerifyCompletionContractTest.test_dispatch_seen_missing_uses_distinct_machine_note_before_degrade tests.test_watcher_core.VerifyCompletionContractTest.test_late_old_task_done_does_not_close_new_dispatch`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 122 tests`, `OK`
- 직접 로그 대조
  - 대상: `.pipeline/runs/20260418T082837Z-p114196/events.jsonl`, `.pipeline/runs/20260418T082837Z-p114196/wrapper-events/codex.jsonl`
  - 결과: first dispatch `DISPATCH_SEEN` 뒤 false `task_accept_missing` requeue가 있었고, second dispatch에서 `TASK_ACCEPTED/TASK_DONE`가 잡힌 current incident evidence를 확인했습니다.

## 남은 리스크
- current fix는 verify FSM이 folded accept를 복구하는 guard입니다. wrapper가 첫 dispatch에서 accept를 늦게/못 emit하는 원인 자체는 아직 남아 있을 수 있습니다.
- `pipeline_runtime/cli.py`의 `_ACTIVITY_MARKERS`가 실제 Codex 출력 다양성을 충분히 덮는지는 이번 verify 범위 밖입니다.
- live stability gate는 이번 verify에 포함하지 않았습니다.
