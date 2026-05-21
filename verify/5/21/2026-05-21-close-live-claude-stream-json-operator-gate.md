# verify: 2026-05-21 close live Claude stream-json operator gate

## 대상 work

`work/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md`

## 이전 verify

`verify/5/21/2026-05-21-claude-stream-json-flag-revert.md`

## 검증 결과

`VERIFY_DONE`.

최신 `/work`의 핵심 주장인 `.pipeline/operator_request.md#2078` gate 종료,
`HOLD_LIVE_VALIDATION_LOCAL_ONLY` 결정 기록, archive 이동, 활성 operator
request 슬롯 비움은 현재 파일 상태와 모순되지 않습니다.

이번 검증은 gate close 확인에 한정했습니다. 최신 `/work`는 코드 변경을
주장하지 않으므로 unit, Playwright, controller/full smoke, live Claude 검증으로
범위를 넓히지 않았습니다.

## 사용 skill

- `round-handoff`: 최신 `/work`와 같은 날 `/verify`를 기준으로 실제 파일 상태와
  검증 범위를 맞추기 위해 사용했습니다.
- `next-slice-triage`: 검증 truth가 현재화된 뒤, operator gate를 재발행하지 않고
  advisory-enabled 조건에서 다음 control을 고르기 위해 사용했습니다.

## 확인한 대상

- `AGENTS.md`
- `.pipeline/harness/verify.md`
- `.pipeline/harness/council.md`
- `work/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md`
- `verify/5/21/2026-05-21-claude-stream-json-flag-revert.md`
- `verify/5/21/2026-05-21-live-claude-stream-json-validation.md`
- `.pipeline/archive/2026-05-21/operator_request.2078-hold-live-validation-resolved.md`
- `.pipeline/implement_handoff.md`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/cli.py`
- `tests/test_pipeline_runtime_supervisor.py`
- `tests/test_pipeline_runtime_cli.py`

## 재실행 검증

- `test ! -f .pipeline/operator_request.md`
  - 결과: PASS. 활성 operator request 슬롯은 없습니다.
- `test -f .pipeline/archive/2026-05-21/operator_request.2078-hold-live-validation-resolved.md`
  - 결과: PASS. #2078 operator gate archive가 존재합니다.
- `rg -n "HOLD_LIVE_VALIDATION_LOCAL_ONLY|Case B|케이스 B|CONTROL_SEQ: 2078|STATUS: needs_operator|live_claude_stream_json_validation_boundary" ...`
  - 결과: PASS. 최신 `/work`, live validation `/verify`, archive된 operator request에서
    Case B와 local-only hold 근거가 확인됩니다.
- `git diff --check -- .pipeline/ work/5/21/ verify/5/21/`
  - 결과: PASS, 출력 없음.
- `git status --short -- .pipeline/operator_request.md .pipeline/archive/2026-05-21/operator_request.2078-hold-live-validation-resolved.md work/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md verify/5/21/2026-05-21-claude-stream-json-flag-revert.md`
  - 결과: 최신 close `/work`와 flag-revert `/verify`는 untracked입니다.
  - archive 파일은 현재 status 출력에 잡히지 않았습니다.

## 코드 spot check

- `pipeline_runtime/supervisor.py`
  - `_lane_vendor_command()`는 `lane_vendor_command_parts()` 결과를 그대로 quote해
    반환하며, Claude에 `--output-format stream-json`을 자동 추가하지 않습니다.
- `pipeline_runtime/cli.py`
  - `_lane_wrapper()`의 `_WrapperEmitter` 초기화는 `jsonl_mode=False`입니다.
- `tests/test_pipeline_runtime_supervisor.py`
  - Claude default command가 pane text mode를 유지하고 `--output-format`을 포함하지
    않는 회귀 테스트가 있습니다.
- `tests/test_pipeline_runtime_cli.py`
  - 모든 lane wrapper가 text mode로 초기화되는 회귀 테스트가 있습니다.

## 실행하지 않은 검증

- Python compile/unit은 재실행하지 않았습니다. 최신 `/work`는 코드/테스트 변경이
  아니라 이미 검증된 flag revert 이후 operator gate archive 이동과 기록에 한정됩니다.
- live Claude, tmux/session access, controller/browser server, Playwright, full smoke,
  long soak는 실행하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release는 실행하지
  않았습니다.

## 런타임 표면

Prompt에 포함된 `RUNTIME_STATUS_AT_DISPATCH`를 권위 있는 dispatcher surface로
사용했습니다.

- `runtime_state: RUNNING`
- `automation_health: recovering`
- `automation_next_action: retrying`
- `active_control: none#-1 none`
- `turn_state: IDLE`
- `active_round: VERIFY_PENDING`

lane-local `status --json`, `doctor --json`, `tmux` 확인은 실행하지 않았고, 그
종류의 lane-local access mismatch를 operator boundary 근거로 사용하지 않았습니다.

## 판정

- 최신 `/work`의 gate-close 주장은 현재 확인 범위에서 사실입니다.
- `.pipeline/operator_request.md#2078`은 active slot에 남아 있지 않고 archive에
  보존되어 있습니다.
- Case B에 따른 단기 교정은 기존
  `verify/5/21/2026-05-21-claude-stream-json-flag-revert.md`에서 READY로 기록돼
  있으며, 이번 spot check도 그 방향과 충돌하지 않습니다.
- release-ready, full-smoke-pass, controller-smoke-pass, publication-ready 상태는
  주장하지 않습니다.

## 남은 리스크

- `claude --print --verbose --output-format stream-json`을 stdin pipe로 실행하는
  wrapper 구조는 아직 구현되지 않았습니다.
- 현재 작업트리에는 이전 wrapper/runtime 라운드의 코드/테스트/verify/work dirty
  항목이 남아 있습니다. 이번 검증은 최신 gate-close `/work`에 한정했습니다.
- `.pipeline/implement_handoff.md#2077`은 현재 파일로 남아 있지만, 이번 dispatcher
  surface는 `active_control: none#-1 none`이며 최신 next control로 대체해야 합니다.
- publication은 계속 held 상태입니다.

## 다음 컨트롤 판단

COUNCIL_DECISION: advisory_followup
REASON_CODE: next_slice_ambiguity_after_live_claude_hold
OWNER_ROLE: advisory
NEXT_CONTROL_FILE: .pipeline/advisory_request.md
NEXT_CONTROL_SEQ: 2078

EVIDENCE:
- `work/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md`
- `verify/5/21/2026-05-21-close-live-claude-stream-json-operator-gate.md`
- `verify/5/21/2026-05-21-claude-stream-json-flag-revert.md`
- `verify/5/21/2026-05-21-live-claude-stream-json-validation.md`
- `.pipeline/archive/2026-05-21/operator_request.2078-hold-live-validation-resolved.md`
- `RUNTIME_STATUS_AT_DISPATCH`: `RUNNING`, `automation_health=recovering`,
  `automation_next_action=retrying`, `active_control=none#-1 none`

REJECTED:
- `.pipeline/operator_request.md`: live validation gate is closed as
  `HOLD_LIVE_VALIDATION_LOCAL_ONLY`; no destructive write, credential/auth,
  approval-record repair, truth-sync blocker, merge, release, external
  publication, or immediate safety boundary blocks local work now.
- `.pipeline/implement_handoff.md`: after the hold decision, there are multiple
  plausible safe local slices and the long-term stdin pipe wrapper direction was
  explicitly not auto-selected by the closeout. Advisory is enabled, so a
  low-confidence implement handoff would push prioritization ambiguity to the
  implement owner.
- commit/push/PR handoff: implement prompts forbid commit, push, branch/PR
  publication, PR creation, merge, and release.
- full smoke / release readiness handoff: latest evidence does not support
  controller-smoke pass, full-smoke pass, release-ready, or publication-ready
  claims.
