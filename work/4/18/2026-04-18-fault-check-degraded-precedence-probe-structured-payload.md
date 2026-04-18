# Fault-check degraded-precedence probe: structured data payload

## 변경 파일

- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 303, HANDOFF_SHA `c5a520f2...`)가 `fault-check` 최상단 두 synthetic degraded-precedence probe(`receipt manifest mismatch degraded precedence`, `active lane auth failure degraded precedence`)를 구조화 payload로 바꾸라고 지목함. 이 두 체크는 그동안 `detail` 문자열만 남겨 automation이 `runtime_state=DEGRADED, reasons=[...]`을 그대로 scraping해야 했음.
- 같은 `fault-check` 계약을 유지하면서 gate/harness 레이어만 손대면 되는 슬라이스이고, 직전 라운드에 추가한 `session loss degraded`/`recoverable lane pid observed`/`lane recovery` 구조화 payload와 같은 패턴을 반복 적용하는 좁은 후속 작업.

## 핵심 변경

- `scripts/pipeline_runtime_gate.py`
  - 모듈 상단에 `_RECEIPT_MANIFEST_PROBE_REASON_PREFIX = "receipt_manifest:job-fault-manifest"`, `_ACTIVE_AUTH_PROBE_EXPECTED_REASON = "claude_auth_login_required"` 상수 추가.
  - `_probe_receipt_manifest_mismatch_degraded_precedence()`와 `_probe_active_lane_auth_failure_degraded_precedence()` return type을 `tuple[bool, str]` → `tuple[bool, str, dict[str, Any]]`로 확장. 각 probe가 `runtime_state`, `degraded_reasons`, `matched_reason`, 그리고 expected prefix(전자) 또는 expected reason(후자)을 담은 dict를 돌려줌. supervisor가 degrade를 숨기는 회귀 경로에서는 `matched_reason`이 빈 문자열로 유지돼 증거 부재가 structured 상태로 노출됨.
  - `run_fault_check()`에서 두 probe 호출을 새 3-tuple unpacking으로 바꾸고, 각 check entry에 `data` 필드를 동일 dict 값으로 실음. `detail` 문자열은 이전과 동일 포맷을 유지해 markdown report 가독성이 회귀하지 않음.
- `tests/test_pipeline_runtime_gate.py`
  - 기존 4개 probe 테스트(`test_probe_receipt_manifest_mismatch_degraded_precedence_catches_regression`, `test_probe_active_lane_auth_failure_degraded_precedence_catches_regression`, `test_probe_receipt_manifest_mismatch_flags_regression_when_supervisor_hides_degrade`, `test_probe_active_lane_auth_failure_flags_regression_when_supervisor_hides_degrade`)를 3-tuple unpacking으로 고치고 `data.runtime_state` / `data.degraded_reasons` / `data.matched_reason` / expected prefix·reason을 함께 검증. supervisor가 degrade를 숨긴 경우 `matched_reason == ""`로 유지되는지 명시적으로 잠금.
  - 새 테스트 `test_run_fault_check_synthetic_probe_entries_carry_structured_data_payloads` 추가. probe 두 개를 mock해 그들의 반환값을 check entry의 `data`로 실었는지와 markdown report가 여전히 동일 evidence를 보여주는지 확인.
  - 다른 테스트에서 probe를 mock할 때 쓰던 2-tuple(`(True, "probe ok")`)을 3-tuple(`(True, "probe ok", {})`)로 일괄 업데이트해 새 signature와 일치하게 함.
- `.pipeline/README.md`
  - 직전 라운드의 live 복구 문단 다음에 한 줄 추가. 두 synthetic probe entry의 `data.runtime_state` / `data.degraded_reasons` / `data.matched_reason`과 각각 `data.expected_reason_prefix`/`data.expected_reason` 필드 규약을 명시하고, 회귀 경로에서 `matched_reason = ""`로 남는 계약을 문서화.

## 검증

- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_gate` → 24/24 pass (기존 23건 + 이번 라운드 추가 1건, 기존 4건은 signature 업데이트로 유지).
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md` → 전체 `PASS`. 두 synthetic probe detail이 이전과 동일한 포맷으로 기록되고(`runtime_state=DEGRADED, reasons=[...]`), 새 `data` payload가 같은 evidence를 structured로 함께 들고 있음. `session loss degraded`/`recoverable lane pid observed`/`lane recovery`의 structured payload와 pass/fail 계약은 회귀 없이 유지.
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- 두 probe의 `data` payload 키(`runtime_state`, `degraded_reasons`, `matched_reason`, `expected_reason_prefix`/`expected_reason`)는 자동화 쪽 schema로 고정. 새 probe가 추가되거나 기대 reason 이름이 바뀌면 README와 테스트를 동반 업데이트해야 함. 이번 slice에서는 taxonomy를 넓히지 않았음.
- `matched_reason`은 probe가 매칭하려는 첫 항목만 담음. 장래에 복수 reason을 증거로 남겨야 하면 필드를 list로 확장하거나 별도 `matched_reasons` 필드를 추가해야 하며, 지금은 `expected_reason_prefix` / `expected_reason`으로 탐지 규약을 명시해 둠.
- 이번 변경은 probe 반환 signature를 바꾸므로 향후 다른 호출자가 probe helper를 직접 재사용하기 시작하면 signature 계약을 같이 명시해야 함. 현재는 `run_fault_check`와 테스트에서만 호출됨.
