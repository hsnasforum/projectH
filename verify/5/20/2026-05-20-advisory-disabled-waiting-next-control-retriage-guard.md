STATUS: verified_with_residual_risk
WORK: work/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md
PREVIOUS_VERIFY: verify/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md
CONTROL_SEQ_NEXT: 1996
ADVISORY_ENABLED: false

# 검증 기록

## 요약

`work/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md`의
핵심 주장은 맞습니다. `tests/test_pipeline_runtime_automation_health.py`에는
`waiting_next_control` + `internal_only` + `next_slice_selection` + advisory
disabled + active control 없음 surface가 `needs_operator`가 아니라
`attention` / `verify_followup`으로 남는 회귀 테스트가 추가되어 있고,
focused compile/unit/whitespace 검증도 통과했습니다.

다만 runtime/status surface에는 잔여 리스크가 남아 있습니다.
dispatch 당시 runtime surface는 `runtime_state=RUNNING`,
`automation_health=ok`, `automation_next_action=continue`,
`active_control=.pipeline/implement_handoff.md#1995 implement`,
`turn_state=IDLE`, `active_round=VERIFY_PENDING`이었습니다. 현재 확인한
status도 `turn_state=IDLE`인 동안 `active_round.state=VERIFYING`,
`completion_stage=receipt_close_pending`, `automation_health=ok`를 보였습니다.
이는 local work를 막는 operator-only 경계는 아니지만, launcher/controller가
진행 중 verify round를 `ok/continue`로 오해할 수 있는 same-family runtime
surface 리스크입니다.

## 사용 skill

- `round-handoff`: 최신 `/work`를 재검증하고, 이전 `/verify` 및 runtime
  surface와 대조한 뒤 다음 단일 control을 선택하기 위해 사용했습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md`
- `verify/5/20/2026-05-20-codex-literal-fallback-runtime-resume-sanity.md`
- `tests/test_pipeline_runtime_automation_health.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_watcher_core.py`
- dispatcher 제공 runtime surface:
  `.pipeline/runs/20260520T061527Z-p65317/status.json`

## 실행한 검증

- `python3 -m py_compile tests/test_pipeline_runtime_automation_health.py`
  - 결과: PASS, 출력 없음.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health.PipelineRuntimeAutomationHealthTest.test_waiting_next_control_retriage_surface_is_not_operator_wait tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_routes_waiting_next_control_internal_only_to_triage tests.test_watcher_core.TurnResolutionTest.test_waiting_next_control_next_slice_selection_routes_to_verify_followup`
  - 결과: PASS. `Ran 3 tests in 0.017s`, `OK`.
- `python3 -m unittest -v tests.test_pipeline_runtime_automation_health`
  - 결과: PASS. `Ran 39 tests in 0.002s`, `OK`.
- `git diff --check -- tests/test_pipeline_runtime_automation_health.py work/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md`
  - 결과: PASS, 출력 없음.
- `nl -ba tests/test_pipeline_runtime_automation_health.py | sed -n '190,250p'`
  - 결과: CHECK. 새 테스트가 219행 부근에 존재함을 확인했습니다.

## 실행하지 않은 검증

- full `tests.test_pipeline_runtime_supervisor`, full `tests.test_watcher_core`,
  controller startup, Playwright, `make e2e-test`, long soak는 실행하지
  않았습니다.
- 이유: 최신 work는 단일 automation-health regression 추가였고, runtime
  dispatcher surface가 이미 recovered/running 상태를 제공했으므로 broad
  browser/controller 검증을 release-ready 근거로 주장하지 않았습니다.

## 변경 파일

- `verify/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md`

## 판정

- 최신 `/work`는 verified입니다.
- `.pipeline/advisory_request.md`는 advisory disabled 조건 때문에 쓰지
  않습니다.
- `.pipeline/operator_request.md`를 유지하거나 새로 쓸 operator-only
  경계는 확인되지 않았습니다. publication, merge, credential/auth,
  destructive action, approval/truth-sync repair, immediate safety stop도
  이번 검증 범위에서 확인되지 않았습니다.

## 다음 control 판정

COUNCIL_DECISION: implement
REASON_CODE: runtime_status_surface_mismatch
OWNER_ROLE: implement
NEXT_CONTROL_FILE: .pipeline/implement_handoff.md
NEXT_CONTROL_SEQ: 1996
EVIDENCE:
- `work/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md`
- `verify/5/20/2026-05-20-advisory-disabled-waiting-next-control-retriage-guard.md`
- dispatcher runtime surface: `turn_state=IDLE` while `active_round=VERIFY_PENDING`
- current status surface: `turn_state=IDLE` while `active_round.state=VERIFYING`
REJECTED:
- `operator_required`: 실제 operator-only 경계가 아니라 local status surface
  mismatch입니다.
- `advisory_followup`: `ADVISORY_ENABLED=false`입니다.
- `commit/push/PR publish`: implement lane 금지 사항이며 이번 검증의 다음
  local slice가 아닙니다.

## 남은 리스크

- `turn_state=IDLE`과 active verify round가 동시에 보이는 status surface는
  아직 별도 guard로 고정되지 않았습니다.
- lane-local runtime/tmux 접근이 dispatcher surface와 충돌할 경우
  dispatcher surface를 우선해야 합니다. 이번 기록에서는 local status를
  operator stop 근거로 쓰지 않았고, 잔여 리스크 보조 증거로만 사용했습니다.
- publication remains held. commit, push, branch/PR publication,
  PR creation/reuse/update, merge, release, external publication은 수행하지
  않았습니다.
