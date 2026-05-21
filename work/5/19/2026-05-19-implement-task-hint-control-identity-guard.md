# 2026-05-19 implement task hint control identity guard

## 변경 파일

- `pipeline_runtime/supervisor.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `.pipeline/implement_handoff.md`
- `verify/5/19/2026-05-19-codex-verify-dispatch-failure-loop-resume-sanity.md`
- `work/5/19/2026-05-19-codex-verify-dispatch-failure-loop-resume-sanity.md`
- `work/5/19/2026-05-19-implement-task-hint-control-identity-guard.md`

## 사용 skill

- `work-log-closeout`: 런타임 복구 중 발견한 task-hint identity 수정과 실제 검증 결과를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유

- `codex_verify_dispatch_failure_loop` 복구 후 verify/handoff가 닫히고 다음 implement control로 넘어가는 과정에서, 이미 `CLOSED`인 verify round의 `job_id`가 implement lane task-hint에 섞이는 것을 확인했습니다.
- 그 결과 task-hint가 `verify-job-old + seq-<CONTROL_SEQ>` 형태가 되어, 실제 implement control identity인 `ctrl-<CONTROL_SEQ>`와 불일치할 수 있었습니다.
- 이는 무한 재전송과는 다른 증상이지만, 같은 dispatcher/receipt chain에서 후속 handoff를 흔들 수 있는 current-risk였습니다.

## 핵심 변경

- `pipeline_runtime/supervisor.py`의 implement-owner task-hint 생성은 active control이 있을 때 항상 `ctrl-<CONTROL_SEQ>` / `seq-<CONTROL_SEQ>`를 사용하도록 고정했습니다.
- self-verify 단일 Codex 모드에서는 살아 있는 verify round identity가 implement control identity보다 우선되도록 조건 순서를 조정했습니다.
- `tests/test_pipeline_runtime_supervisor.py`에 닫힌 verify round identity가 implement task-hint로 새지 않는 회귀 테스트와 self-verify 우선순위 회귀 테스트를 추가했습니다.
- `.pipeline/implement_handoff.md`는 verify-triage 결과에 따라 같은 docs bundle을 `CONTROL_SEQ: 1981`로 재발행한 상태입니다.
- 앞선 resume sanity verify 기록과 work 기록은 유지했고, `.pipeline/operator_request.md#1978`은 계속 stale operator slot입니다.

## 검증

- `python3 -m py_compile pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
  - 결과: PASS.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_implement_lane_has_dispatch_fields_when_active tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_implement_lane_ignores_closed_verify_round_identity tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_task_hints_self_verify_round_identity_takes_precedence`
  - 결과: PASS. 3개 테스트 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest`
  - 결과: PASS. 163개 테스트 통과.
- `git diff --check -- pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py .pipeline/implement_handoff.md verify/5/19/2026-05-19-codex-verify-dispatch-failure-loop-resume-sanity.md work/5/19/2026-05-19-codex-verify-dispatch-failure-loop-resume-sanity.md`
  - 결과: PASS, 출력 없음.

## 남은 리스크

- live runtime은 이 기록 시점에 아직 최신 `supervisor.py` 코드를 로드했다고 주장할 수 없으므로, 후속으로 controlled reload/start sanity가 필요합니다.
- 이번 수정은 task-hint identity 누수를 막는 focused guard입니다. controller/browser, Playwright, 전체 unittest, long soak는 실행하지 않았습니다.
- publication은 계속 held 상태입니다. commit, push, branch/PR publication, PR creation/reuse/update, merge, release, external publication은 수행하지 않았습니다.
