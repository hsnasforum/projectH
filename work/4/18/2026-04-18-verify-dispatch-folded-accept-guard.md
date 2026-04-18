# 2026-04-18 verify dispatch folded accept guard

## 변경 파일
### 이번 라운드 직접 편집 파일
- `verify_fsm.py`
- `tests/test_watcher_core.py`
- `.pipeline/README.md`

### 현재 `git diff HEAD`에 함께 보이는 별도 라운드/기존 dirty worktree
- `watcher_dispatch.py`, `watcher_core.py`, `pipeline_runtime/supervisor.py` 등은 오늘 다른 watcher/runtime 라운드 산출물이거나 세션 시작 전부터 있던 dirty worktree입니다.
- 이번 closeout은 위 "직접 편집 파일"만 이번 라운드 범위로 기록합니다.

## 사용 skill
- 없음

## 변경 이유
- 사용자 스크린샷의 pasted verify prompt를 보고 처음에는 pane readiness 오인 가능성을 의심했지만, 실제 current run 로그를 다시 읽어 보니 더 직접적인 증거는 verify requeue 쪽에 있었습니다.
- `.pipeline/runs/20260418T082837Z-p114196/events.jsonl`에는 `2026-04-18-runtime-gate-degraded-acb02b80` verify job이 `dispatch_stall_detected(stage=task_accept_missing)`로 한 번 requeue된 기록이 있었고, 같은 run의 `wrapper-events/codex.jsonl`에는 첫 dispatch(`dispatch_id=60b40...`) 뒤 `DISPATCH_SEEN`만 남고, 두 번째 dispatch(`dispatch_id=b564...`)에서야 `TASK_ACCEPTED`/`TASK_DONE`가 다시 잡혔습니다.
- `verify_fsm.py`는 wrapper read model의 `accepted_task`가 비어 있으면 accept를 못 본 것으로 간주하는데, `pipeline_runtime/wrapper_events.py`의 current read model은 latest `TASK_DONE`를 반영하는 순간 `accepted_task`를 지웁니다. 그래서 poll 타이밍이 늦으면 실제로는 accept가 있었어도 FSM은 `task_accept_missing`으로 오인해 같은 verify prompt를 다시 paste할 수 있었습니다.

## 핵심 변경
- `verify_fsm.py::_mark_dispatch_accepted_if_seen(...)`에 current dispatch의 matching `done_task` fallback을 추가했습니다. wrapper read model이 same-dispatch `TASK_ACCEPTED`를 이미 `TASK_DONE` 뒤에 접어 버린 경우에도, 그 `TASK_DONE`를 accept의 더 강한 증거로 보고 `accepted_dispatch_id`를 먼저 채웁니다.
- inferred accept 시각은 `done_ts` 또는 `last_event_ts`를 우선 써서, 단순 `time.time()`로 찍어 deadline/idle 계산을 왜곡하지 않도록 맞췄습니다.
- `tests/test_watcher_core.py`에 `test_matching_task_done_implies_accept_when_wrapper_model_already_folded_accept`를 추가했습니다. `DISPATCH_SEEN -> TASK_ACCEPTED -> TASK_DONE -> READY`가 wrapper log에 실제로 기록돼도 read model에서는 `accepted_task`가 이미 비어 있는 상황을 재현하고, 이때 FSM이 `task_accept_missing`으로 VERIFY_PENDING 재큐잉하지 않고 `accepted_dispatch_id`/`done_dispatch_id`를 모두 current dispatch로 고정하는지 확인했습니다.
- `.pipeline/README.md`에는 same-dispatch `TASK_DONE`가 accept-folding 이후에도 verify FSM에서 accept의 강한 증거로 취급된다는 현재 계약을 짧게 추가했습니다.

## 검증
- `python3 -m py_compile verify_fsm.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_watcher_core.VerifyCompletionContractTest.test_matching_task_done_implies_accept_when_wrapper_model_already_folded_accept tests.test_watcher_core.VerifyCompletionContractTest.test_dispatch_seen_missing_uses_distinct_machine_note_before_degrade tests.test_watcher_core.VerifyCompletionContractTest.test_late_old_task_done_does_not_close_new_dispatch`
  - 결과: `Ran 3 tests`, `OK`
- `python3 -m unittest -v tests.test_watcher_core`
  - 결과: `Ran 122 tests`, `OK`
- 로그 대조
  - 대상: `.pipeline/runs/20260418T082837Z-p114196/events.jsonl`, `.pipeline/runs/20260418T082837Z-p114196/wrapper-events/codex.jsonl`
  - 결과: first dispatch `DISPATCH_SEEN` 뒤 `task_accept_missing` requeue, second dispatch에서 `TASK_ACCEPTED/TASK_DONE`가 잡힌 current incident evidence를 확인했습니다.

## 남은 리스크
- 이번 수정은 "이미 current dispatch의 `TASK_DONE`가 보였는데도 accept를 못 본 채 재큐잉하는" 오인만 줄입니다. 첫 dispatch에서 wrapper가 정말 `TASK_ACCEPTED`를 늦게/못 찍는 근본 원인까지 닫은 것은 아닙니다.
- Codex wrapper의 `activity_detected` marker 집합은 여전히 좁습니다. vendor output이 busy marker나 `_ACTIVITY_MARKERS`에 안 걸리면 첫 accept가 늦게 찍힐 수 있습니다.
- live tmux replay / launcher stability gate는 이번 라운드에 다시 실행하지 않았습니다. 실제 세션에서 같은 family가 더 나오면 다음 후보는 `pipeline_runtime/cli.py`의 accept marker widening 또는 wrapper read model 보강입니다.
