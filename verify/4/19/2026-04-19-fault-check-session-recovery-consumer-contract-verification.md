# 2026-04-19 fault-check session recovery consumer contract verification

## 변경 파일
- `verify/4/19/2026-04-19-fault-check-session-recovery-consumer-contract-verification.md`
- `.pipeline/gemini_request.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/19/2026-04-19-fault-check-session-recovery-consumer-contract.md`가 `fault-check`의 `session loss degraded` consumer contract를 docs/tests 쪽에서 `data.session_recovery`까지 맞췄다고 주장하므로, 현재 tree의 실제 문서와 회귀가 그 설명과 일치하는지 다시 확인해야 했습니다.
- prompt에 적힌 `VERIFY` 경로 `verify/4/19/2026-04-19-fault-check-bounded-session-recovery-evidence-verification.md`는 직전 same-family predecessor verify라서 읽고 이어받았지만, latest `/work`가 새 consumer-contract round이므로 이번 라운드는 별도 `/verify` note로 닫는 편이 truthful합니다.

## 핵심 변경
- latest `/work`의 직접 변경 주장과 현재 tree는 일치합니다.
  - `.pipeline/README.md`의 `session loss degraded` 설명에는 이제 `data.session_recovery` payload와 그 하위 필드(`recovery_expected`, `broken_lane_names`, `event_observed`, `event_type`, `attempt`, `result`, `error`, raw `event`)가 들어 있고, recovery가 기대되지 않을 때의 stable empty/default shape와 recovery가 기대될 때 terminal `session_recovery_completed` / `session_recovery_failed` evidence를 요구하는 조건도 문서화되어 있습니다.
  - `tests/test_pipeline_runtime_gate.py`의 `test_lifecycle_checks_expose_structured_data_on_green_path`는 BROKEN lane이 없는 green path에서도 `session loss degraded` entry가 stable default `session_recovery` structure를 유지하는지 실제로 pin합니다.
  - 같은 파일의 `test_fault_check_cli_writes_markdown_and_json_sidecar_with_structured_checks`는 `session loss degraded` sample을 markdown/json sidecar consumer path에 넣고 `session_recovery` payload가 그대로 유지되는지 실제로 pin합니다.
- latest `/work`가 말한 검증 주장도 이번 rerun과 맞았습니다.
  - `python3 -m py_compile tests/test_pipeline_runtime_gate.py`는 통과했습니다.
  - focused 2-test rerun은 `Ran 2 tests`, `OK`였습니다.
  - module rerun인 `python3 -m unittest tests.test_pipeline_runtime_gate`도 `Ran 34 tests`, `OK`였습니다.
  - `git diff --check -- tests/test_pipeline_runtime_gate.py .pipeline/README.md scripts/pipeline_runtime_gate.py`도 출력 없이 통과했습니다.
- 다만 next control은 `.pipeline/claude_handoff.md`로 바로 고정하지 않고 `.pipeline/gemini_request.md`를 `CONTROL_SEQ: 353`으로 갱신했습니다.
  - 같은 family의 code/docs/tests consumer-contract drift는 이번 verify로 truthfully 닫혔습니다.
  - 남은 후보는 live `fault-check` evidence를 계속 좁힐지, 아니면 internal operator tooling 바깥의 document-first priority로 축을 옮길지인데, 현재 repo 우선순위와 `operator tooling remains outside the current release gate` 문구까지 감안하면 자동 tie-break 확신이 낮습니다.
  - 따라서 weak한 다음 implement micro-slice를 억지로 쓰기보다 Gemini arbitration을 먼저 열어 exact next control path만 묻는 편이 truthful합니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `.pipeline/README.md`, `tests/test_pipeline_runtime_gate.py`, `scripts/pipeline_runtime_gate.py`, latest `/work`, predecessor `/verify`
  - 결과: latest `/work`가 설명한 consumer-contract sync는 현재 tree와 일치했고, `scripts/pipeline_runtime_gate.py`의 `session_recovery` gate behavior는 이전 same-family round에서 이미 들어온 상태 그대로 유지되고 있음을 확인했습니다.
- `python3 -m py_compile tests/test_pipeline_runtime_gate.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_gate.PipelineRuntimeGateSoakTest.test_lifecycle_checks_expose_structured_data_on_green_path tests.test_pipeline_runtime_gate.PipelineRuntimeGateSoakTest.test_fault_check_cli_writes_markdown_and_json_sidecar_with_structured_checks`
  - 결과: `Ran 2 tests`, `OK`
- `python3 -m unittest tests.test_pipeline_runtime_gate`
  - 결과: `Ran 34 tests`, `OK`
- `git diff --check -- tests/test_pipeline_runtime_gate.py .pipeline/README.md scripts/pipeline_runtime_gate.py`
  - 결과: 출력 없음, exit code `0`
- live `python3 scripts/pipeline_runtime_gate.py fault-check ...`, live tmux session-loss 재현, browser/controller 검증은 이번 verify에서 다시 실행하지 않았습니다.
  - 이유: latest `/work`의 docs/tests consumer-contract truth 판정에는 unit/file-level rerun으로 충분했고, live runtime 조작은 현재 automation 세션에 직접 영향을 줄 수 있기 때문입니다.

## 남은 리스크
- live host에서 `session_missing` 이후 bounded `session_recovery_*` terminal event가 실제 `events.jsonl`에 원하는 budget 안에 찍히는지는 이번 verify에서 다시 재현하지 않았습니다. 현재 증거는 synthetic/unit contract까지입니다.
- `scripts/pipeline_runtime_gate.py`는 이번 라운드의 직접 수정 파일은 아니지만 same-family prior round 변경이 계속 dirty state로 남아 있으므로, 향후 gate field를 다시 바꾸면 README/tests consumer contract도 함께 다시 맞춰야 합니다.
- next slice는 더 이상의 명백한 consumer-contract drift가 아니라 “internal runtime family를 더 계속할지, document-first priority로 돌아갈지”의 우선순위 문제라서, 이번 라운드는 Gemini arbitration 없이는 low-confidence handoff가 될 가능성이 있습니다.
