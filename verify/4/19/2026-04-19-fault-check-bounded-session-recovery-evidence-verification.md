# 2026-04-19 fault-check bounded session recovery evidence verification

## 변경 파일
- `verify/4/19/2026-04-19-fault-check-bounded-session-recovery-evidence-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/19/2026-04-19-fault-check-bounded-session-recovery-evidence.md`가 `fault-check`의 `session loss degraded` gate에 bounded `session_recovery_*` terminal event evidence를 추가했다고 주장하므로, 현재 tree의 실제 코드/테스트/문서가 그 설명과 맞는지 다시 확인해야 했습니다.
- prompt에 적힌 `VERIFY` 경로 `verify/4/19/2026-04-19-tmux-scaffold-failure-surfacing-verification.md`는 직전 same-family predecessor verify라서 읽고 이어받았지만, latest `/work`가 새 gate implementation round이므로 이번 라운드는 별도 `/verify` note로 닫는 편이 truthful합니다.

## 핵심 변경
- latest `/work`의 핵심 코드/테스트 주장은 현재 tree와 일치합니다.
  - `scripts/pipeline_runtime_gate.py`의 `session loss degraded` 체크는 실제로 `recovery_expected`, `broken_lane_names`, `event_observed`, `event_type`, `attempt`, `result`, `error`, raw `event`를 담는 `data.session_recovery`를 추가했고, recovery가 기대되는데 terminal `session_recovery_completed` / `session_recovery_failed` event가 없으면 체크가 실패하도록 좁혀졌습니다.
  - `tests/test_pipeline_runtime_gate.py`에는 `/work`가 설명한 focused 회귀 4건이 실제로 들어 있으며, module rerun에서도 모두 통과했습니다.
  - `python3 -m unittest -v tests.test_pipeline_runtime_gate` 재실행 결과도 `/work`가 적은 것처럼 `Ran 34 tests`, `OK`였습니다.
- 다만 `/work`의 “`.pipeline/README.md`는 이번 라운드에서 건드리지 않아도 drift가 없다”는 판단은 현재 tree 기준으로는 다소 과합니다.
  - `.pipeline/README.md`의 `session loss degraded` 설명은 여전히 `data.runtime_state / data.representative_reason / data.degraded_reasons / data.secondary_recovery_failures`까지만 열거하고 있고, 새 `data.session_recovery` payload와 recovery-expected 시 terminal event 요구는 적혀 있지 않습니다.
  - 즉 latest `/work`의 구현 핵심은 맞지만, README no-drift rationale은 완전히 닫히지 않았습니다.
- same-family 다음 current-risk는 consumer-contract drift로 좁혀졌습니다.
  - `tests/test_pipeline_runtime_gate.py`의 CLI/JSON sidecar regression인 `test_fault_check_cli_writes_markdown_and_json_sidecar_with_structured_checks`는 현재도 sample checks에 `session loss degraded` entry를 넣지 않아 새 `session_recovery` payload가 report/json sidecar consumer path에서 유지되는지를 직접 pin하지 않습니다.
  - `test_lifecycle_checks_expose_structured_data_on_green_path`도 현재는 `session loss degraded`에서 `representative_reason`만 확인하고 있어, green path에서 새 `data.session_recovery` fields가 보존되는지는 아직 regression으로 잠겨 있지 않습니다.
- 위 판단에 따라 `.pipeline/claude_handoff.md`를 `CONTROL_SEQ: 352`의 same-family next slice로 갱신했습니다.
  - next slice는 `.pipeline/README.md`와 `tests/test_pipeline_runtime_gate.py`의 consumer-facing contract를 새 `session_recovery` payload까지 맞추는 데만 좁힙니다.
  - next-slice ambiguity나 operator-only decision은 남지 않았으므로 `.pipeline/gemini_request.md`나 `.pipeline/operator_request.md`는 새로 쓰지 않았습니다.

## 검증
- `git status --short`
  - 결과: broad dirty worktree가 여전히 존재했고, 관련 범위에서는 `.pipeline/README.md`, `scripts/pipeline_runtime_gate.py`, `tests/test_pipeline_runtime_gate.py`가 modified였습니다. 이외 watcher/manual-cleanup, controller cozy, runtime docs/tests 등 unrelated 변경도 계속 존재했습니다.
- `git status --short scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md`
  - 결과: `M .pipeline/README.md`, `M scripts/pipeline_runtime_gate.py`, `M tests/test_pipeline_runtime_gate.py`
- `git diff --name-only -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md`
  - 결과: `.pipeline/README.md`, `scripts/pipeline_runtime_gate.py`, `tests/test_pipeline_runtime_gate.py`
- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_gate`
  - 결과: `Ran 34 tests`, `OK`
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md`
  - 결과: 출력 없음, exit code `0`
- 직접 코드/문서 대조
  - 대상: `scripts/pipeline_runtime_gate.py`, `tests/test_pipeline_runtime_gate.py`, `.pipeline/README.md`
  - 결과: gate와 회귀 테스트는 latest `/work` 설명과 일치했지만, `.pipeline/README.md`의 `session loss degraded` payload 설명은 새 `session_recovery` consumer contract까지는 아직 따라오지 못했음을 확인했습니다.
- live `python3 scripts/pipeline_runtime_gate.py fault-check ...`, live tmux session-loss 재현, browser/controller 검증은 이번 verify에서 다시 실행하지 않았습니다.
  - 이유: latest `/work`의 Python-only gate contract truth 판정에는 module-level unit/file 검증으로 충분했고, live runtime 조작은 현재 automation 세션에 직접 영향을 줄 수 있기 때문입니다.

## 남은 리스크
- latest `/work`의 gate 구현/테스트 주장은 맞지만, README no-drift 판단은 현재 tree와 완전히 일치하지 않습니다. `.pipeline/README.md`의 `session loss degraded` 문구는 새 `session_recovery` payload와 recovery-expected terminal event requirement를 아직 직접 설명하지 않습니다.
- current CLI/JSON sidecar regression test는 새 `session_recovery` payload를 sample consumer path에서 직접 pin하지 않습니다. 따라서 report/json sidecar consumer contract는 아직 end-to-end로 완전히 잠기지 않았습니다.
- live host에서 `session_missing` 이후 bounded `session_recovery_*` event가 timeout budget 안에 도착하는지, 그리고 gate가 실제 `events.jsonl`에서 같은 evidence를 확보하는지는 이번 verify에서 다시 재현하지 않았습니다.
