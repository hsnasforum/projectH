# Fault-check session loss check: structured secondary_recovery_failures payload

## 변경 파일

- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 301, HANDOFF_SHA `0bd69826...`)가 직전 라운드에서 live `session loss degraded` detail 문자열 안에만 실렸던 `secondary_recovery_failures`를 check payload의 구조화된 필드로 올려달라고 지목함. 이렇게 해야 CI / launcher / 후속 runtime tooling이 human-readable detail 문자열을 scraping하지 않고도 같은 evidence를 읽을 수 있음.
- supervisor 의미나 pass/fail 계약은 바꾸지 않고 gate/harness 레이어에서만 끝낼 수 있는 slice이므로 다른 quality axis나 degraded taxonomy 확장보다 좁은 다음 단계가 됨.

## 핵심 변경

- `scripts/pipeline_runtime_gate.py::run_fault_check()`
  - `session loss degraded` 체크 앞에서 `session_loss_data` 구조화 dict를 먼저 조립: `runtime_state`, `representative_reason`, `degraded_reasons`, `secondary_recovery_failures`. `secondary_recovery_failures`는 `degraded_reasons` 중 `*_recovery_failed`로 끝나는 항목만 골라 담고, 없으면 빈 list(`[]`)로 유지.
  - `checks.append(...)` 엔트리에 `data` 필드를 추가하고, 기존 `detail` 문자열은 동일 dict 값을 포맷해 만들도록 바꿔 사람이 읽는 보고서와 구조화 payload가 반드시 같은 evidence에서 파생되도록 강제.
  - pass/fail 판정(`session_loss_ok`)은 이전 라운드의 representative-reason 규칙을 그대로 유지. 직전 라운드의 probe 2건, pre-accept 복구, 세션 상실 ordering 논리는 건드리지 않음.
- `tests/test_pipeline_runtime_gate.py`
  - `test_session_loss_check_exposes_secondary_recovery_failures_as_structured_data`: 3개 lane `*_recovery_failed`가 `session_missing`과 함께 올 때 `check["data"]["secondary_recovery_failures"]`가 정확한 list로 존재하고, markdown report도 동일 payload에서 사람이 읽는 내용이 나오는지 확인.
  - `test_session_loss_check_reports_empty_secondary_recovery_failures_when_none_present`: 오직 `session_missing`만 보이는 경우에도 `data["secondary_recovery_failures"]`가 빈 list로 반드시 존재하는 stable schema 규약을 잠금.
  - 두 테스트 모두 `_wait_until`를 one-shot evaluator로 mock해 tmux live 대기를 생략. 기존 representative-reason 회귀 테스트와 probe precedence 테스트는 그대로 통과.
- `.pipeline/README.md`
  - `session loss degraded` 문단 다음에 한 줄을 더해 `data.runtime_state` / `data.representative_reason` / `data.degraded_reasons` / `data.secondary_recovery_failures` 구조화 payload 규약과 `secondary_recovery_failures=[]` default를 명시.

## 검증

- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_gate` → 21/21 pass (기존 19건 + 이번 라운드 추가 2건).
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md` → 전체 `PASS`. `session loss degraded` detail이 여전히 `reason=session_missing, reasons=["session_missing", "claude_recovery_failed", "codex_recovery_failed", "gemini_recovery_failed"], secondary_recovery_failures=["claude_recovery_failed", "codex_recovery_failed", "gemini_recovery_failed"]`로 기록돼 같은 evidence를 detail과 data 양쪽에서 볼 수 있음. markdown report(`/tmp/projecth-runtime-fault-check.md`)의 가독성은 그대로 유지됨.
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- 이번 slice는 `session loss degraded` 체크 엔트리에만 `data` payload를 추가했음. 다른 체크(예: `lane recovery`)도 비슷한 구조화 payload가 필요해지면 동일 패턴을 반복 적용해야 하며, 지금은 `detail` 문자열이 그대로 남아 있음.
- `data["secondary_recovery_failures"]`는 `*_recovery_failed`로 끝나는 reason만 필터링함. lane recovery 실패 명명 규약이 바뀌면 이 필터를 같이 확장해야 함. 이번 slice에서는 기존 `_maybe_recover_lane(...)` 이름 규약(`{lane}_recovery_failed`)을 그대로 따름.
- 현재 consumer는 detail 문자열을 scraping하지 않도록 가이드를 README에 적었지만, 기존 자동화가 detail 문자열에 의존하고 있다면 마이그레이션은 별도 라운드에서 다뤄야 함. 이번 slice는 structured payload를 추가만 했고 기존 detail 필드 형식을 강제로 변경하지 않음.
