# 2026-04-18 soak JSON sidecar export verification

## 변경 파일
- `verify/4/18/2026-04-18-watcher-dispatch-control-mismatch-requery-verification.md`
- `.pipeline/claude_handoff.md`

## 사용 skill
- `round-handoff`

## 변경 이유
- latest `/work`인 `work/4/18/2026-04-18-soak-json-sidecar-export.md`가 `synthetic-soak`와 plain `soak` CLI가 markdown report 옆에 JSON sidecar를 함께 쓰도록 export 경계를 좁혔다고 주장하므로, 그 주장을 현재 코드/문서와 좁은 재실행으로 다시 확인해야 했습니다.
- 이번 요청은 같은 same-day `/verify` 경로를 최신 round truth로 갱신하라고 명시했으므로, 직전 seq 306 verification 내용을 그대로 두지 않고 seq 307 기준 사실로 덮어써 `/work`와 맞췄습니다.
- verification 뒤에는 exact next slice 하나만 남겨야 하므로, soak-family export gap이 닫힌 뒤에도 남아 있는 `check-operator-classification` report artifact 경계 한 건만 다음 handoff 대상으로 좁혔습니다.

## 핵심 변경
- latest `/work`의 핵심 주장은 현재 파일과 일치합니다. `scripts/pipeline_runtime_gate.py`는 이전 라운드의 `fault-check` 전용 helper를 `_report_json_sidecar_path` / `_write_report_json_sidecar`로 일반화했고, 새 `_soak_summary_fields(summary, *, base)` helper로 `run_soak()` summary를 JSON-safe하게 평탄화한 뒤 `synthetic-soak`와 plain `soak` 분기 모두에서 markdown write 직후 같은 basename의 `.json` sidecar를 함께 기록합니다.
- `synthetic-soak`와 plain `soak` sidecar shape도 `/work` 설명과 맞습니다. `summary`에는 `duration_sec`, `ready_ok`, `ready_wait_sec`, `state_counts`, `degraded_counts`, `receipt_count`, `control_change_count`, `duplicate_dispatch_count`, `classification_gate_failures`, `classification_gate_details`, `orphan_session`, `broken_seen`, `degraded_seen`, `readiness_snapshot` 등이 평탄화되어 들어가고, synthetic 경로에는 추가로 `workspace_retained` / `workspace_cleanup`이 남습니다.
- markdown contract는 회귀하지 않았습니다. `synthetic-soak`와 plain `soak` stdout/report는 이전과 같은 요약 라인과 human-readable check detail을 유지하고, JSON sidecar만 추가로 생깁니다.
- `tests/test_pipeline_runtime_gate.py`에도 latest `/work`가 적은 focused regression이 실제로 들어 있습니다. `test_synthetic_soak_cli_writes_markdown_and_json_sidecar`와 `test_plain_soak_cli_writes_markdown_and_json_sidecar`가 두 CLI 경로의 `.md`/`.json` 동시 생성, `summary` 필드, 대표 check 포함 여부를 잠그고, 기존 helper 경계 테스트는 `test_report_json_sidecar_path_swaps_md_suffix_and_appends_for_suffixless_paths`로 이름을 맞춰 유지합니다.
- `.pipeline/README.md`도 현재 구현과 일치합니다. `synthetic-soak`와 plain `soak`가 같은 basename 규칙으로 JSON sidecar를 쓰고, `run_soak()` summary dict가 `summary` 아래에 평탄화되며 synthetic 전용 필드(`workspace_retained`, `workspace_cleanup`) 차이가 남는다고 명시합니다.
- 재실행 결과 latest `/work`의 결론은 truthful합니다. `tests.test_pipeline_runtime_gate`는 `Ran 30 tests`, `OK`였고, live `synthetic-soak`는 `/work`가 적은 대로 exit code `1`로 끝났지만 이는 `synthetic workload produced receipts` 한 체크만 `receipt_count=0`으로 FAIL한 기존 synthetic workload 특성 때문이었습니다. sidecar export 자체는 정상이며, one-liner는 실제로 `synthetic soak sidecar assertions passed`를 출력했습니다.
- 같은 `/work`가 적은 fault-check 회귀 확인도 사실과 맞습니다. `fault-check` live rerun은 exit code `0`이었고, sidecar assertion one-liner도 다시 `sidecar assertions passed`를 출력했습니다.
- rerun evidence 기준의 다음 same-family current-risk도 명확합니다. `fault-check`, `synthetic-soak`, plain `soak`는 이제 모두 persisted JSON sidecar를 갖지만, `check-operator-classification` CLI는 여전히 markdown-only입니다. 이 경로는 one-check report라 범위가 가장 좁아 다음 handoff를 그 한 건으로 고정하는 것이 맞습니다.

## 검증
- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py`
  - 결과: 통과
- `python3 -m unittest -v tests.test_pipeline_runtime_gate`
  - 결과: `Ran 30 tests in 0.125s`, `OK`
- `python3 scripts/pipeline_runtime_gate.py synthetic-soak --workspace-root /tmp --duration-sec 10 --sample-interval-sec 1 --min-receipts 1 --report /tmp/projecth-runtime-synthetic-soak.md`
  - 결과: exit code `1`
  - 세부:
    - `PASS` `runtime start`
      - detail: `started`
    - `PASS` `runtime ready barrier`
      - detail: `wait_sec=3.543, timeout_sec=45.0, {"active_round": {"state": ""}, "control": {"active_control_status": "none"}, "lanes": [{"attachable": true, "last_event_at": "2026-04-18T09:57:58.975736Z", "last_heartbeat_at": "2026-04-18T09:57:58.927416Z", "name": "Claude", "note": "prompt_visible", "pid": 259040, "state": "READY"}, {"attachable": true, "last_event_at": "2026-04-18T09:57:58.971051Z", "last_heartbeat_at": "2026-04-18T09:57:58.930409Z", "name": "Codex", "note": "prompt_visible", "pid": 259068, "state": "READY"}, {"attachable": true, "last_event_at": "2026-04-18T09:57:59.046876Z", "last_heartbeat_at": "2026-04-18T09:57:59.001611Z", "name": "Gemini", "note": "prompt_visible", "pid": 259111, "state": "READY"}], "runtime_state": "RUNNING", "watcher": {"alive": true, "pid": 259183}}`
    - `FAIL` `synthetic workload produced receipts`
      - detail: `receipt_count=0`
    - `PASS` `soak completed without BROKEN`
      - detail: `broken_seen=False`
    - `PASS` `soak completed without DEGRADED`
      - detail: `degraded_seen=False`
    - `PASS` `duplicate dispatch stayed at zero`
      - detail: `duplicate_dispatch_count=0`
    - `PASS` `control surface stayed free of persistent mismatch`
      - detail: `control_mismatch_samples=0, max_streak=0`
    - `PASS` `classification_fallback_detected`
      - detail: `[]`
    - `PASS` `stop left no orphan session`
      - detail: `orphan_session=False`
- `python3 -c 'import json, pathlib; p=pathlib.Path("/tmp/projecth-runtime-synthetic-soak.json"); payload=json.loads(p.read_text()); checks=payload.get("checks") or []; assert p.exists(); assert any(item.get("name")=="runtime ready barrier" for item in checks); assert any(item.get("name")=="classification_fallback_detected" for item in checks); print("synthetic soak sidecar assertions passed")'`
  - 결과: `synthetic soak sidecar assertions passed`
  - 직접 확인: `/tmp/projecth-runtime-synthetic-soak.json`이 존재하고 `summary.workspace_retained=true`, `summary.workspace_cleanup="retained_for_failure"`, `checks`에 `runtime ready barrier` / `classification_fallback_detected`가 존재함을 확인
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md`
  - 결과: exit code `0`
  - 세부:
    - `PASS` `receipt manifest mismatch degraded precedence`
      - detail: `runtime_state=DEGRADED, reasons=["receipt_manifest:job-fault-manifest:artifact_hash_mismatch"]`
    - `PASS` `active lane auth failure degraded precedence`
      - detail: `runtime_state=DEGRADED, reasons=["claude_auth_login_required"]`
    - `PASS` `runtime start`
      - detail: `started`
    - `PASS` `status surface ready`
      - detail: `wait_sec=1.0, {"active_round": {"state": ""}, "control": {"active_control_status": "none"}, "lanes": [{"attachable": true, "last_event_at": "2026-04-18T09:58:19.394722Z", "last_heartbeat_at": "2026-04-18T09:58:19.349261Z", "name": "Claude", "note": "prompt_visible", "pid": 260338, "state": "READY"}, {"attachable": true, "last_event_at": "2026-04-18T09:58:19.407547Z", "last_heartbeat_at": "2026-04-18T09:58:19.360566Z", "name": "Codex", "note": "prompt_visible", "pid": 260365, "state": "READY"}, {"attachable": true, "last_event_at": "2026-04-18T09:58:19.426414Z", "last_heartbeat_at": "2026-04-18T09:58:19.384489Z", "name": "Gemini", "note": "prompt_visible", "pid": 260393, "state": "READY"}], "runtime_state": "RUNNING", "watcher": {"alive": true, "pid": 260487}}`
    - `PASS` `session loss degraded`
      - detail: `runtime_state=DEGRADED, reason=session_missing, reasons=["session_missing","claude_recovery_failed","codex_recovery_failed","gemini_recovery_failed"], secondary_recovery_failures=["claude_recovery_failed","codex_recovery_failed","gemini_recovery_failed"]`
    - `PASS` `runtime stop after session loss`
      - detail: `stopped`
    - `PASS` `runtime restart`
      - detail: `started`
    - `PASS` `recoverable lane pid observed`
      - detail: `lane=Claude, pid=261767`
    - `PASS` `lane recovery`
      - detail: `{"seq": 8, "ts": "2026-04-18T09:58:24.861176Z", "run_id": "20260418T095823Z-p261039", "event_type": "recovery_completed", "source": "supervisor", "payload": {"lane": "Claude", "attempt": 1, "result": "restarted"}}`
- `python3 -c 'import json, pathlib; p=pathlib.Path("/tmp/projecth-runtime-fault-check.json"); payload=json.loads(p.read_text()); checks=payload.get("checks") or []; assert p.exists(); assert any(item.get("name")=="runtime start" and "data" in item for item in checks); assert any(item.get("name")=="status surface ready" and "data" in item for item in checks); assert any(item.get("name")=="lane recovery" and "data" in item for item in checks); print("sidecar assertions passed")'`
  - 결과: `sidecar assertions passed`
  - 직접 확인: `/tmp/projecth-runtime-fault-check.json`에 `title="Pipeline Runtime fault check"`, `ok=true`, `summary.session="aip-projecth-pipeline-runtime-synthetic-lo5_54aq"`와 `checks[*].data`가 존재함을 확인
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md`
  - 결과: 통과
- 직접 대조:
  - 대상: `scripts/pipeline_runtime_gate.py`, `tests/test_pipeline_runtime_gate.py`, `.pipeline/README.md`
  - 결과: shared sidecar helper, soak CLI write path, test coverage, README 문장이 현재 구현과 일치함을 확인

## 남은 리스크
- `fault-check`, `synthetic-soak`, plain `soak` export gap은 닫혔지만 `check-operator-classification` CLI는 여전히 markdown만 기록합니다. 이 경로도 현재는 `report_path`가 주어지면 file artifact를 쓰므로, 같은 basename sidecar 계약을 붙이기 가장 좁습니다.
- soak readiness snapshot과 operator classification detail은 둘 다 raw helper-derived 문자열/JSON을 함께 싣고 있으므로, 다음 `check-operator-classification` sidecar를 열 때도 top-level stable fields와 raw detail의 역할을 분리하는 편이 안전합니다.
- 이번 verify는 narrowest relevant gate/export checks만 다시 돌렸습니다. broader soak, supervisor 전반 audit, controller/browser surface audit은 이번 라운드 범위 밖입니다.
- 이번 verify는 narrowest relevant gate checks만 다시 돌렸습니다. broader soak, supervisor 전반 audit, controller/browser surface audit은 이번 라운드 범위 밖입니다.
