# Fault-check JSON sidecar export

## 변경 파일

- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 305, HANDOFF_SHA `8825991e...`)가 직전 라운드까지 모든 `run_fault_check()` entry에 붙은 structured `data` payload가 메모리 밖으로는 markdown report로만 나가는 export 경계를 좁히라고 지목함. Python을 import하지 않는 CI/operator tool은 아직 detail 문자열을 scraping해야 했음.
- 같은 `fault-check` pass/fail / markdown 계약을 유지하면서 CLI path 끝단에서만 JSON 파일 하나를 추가하면 되는 좁은 슬라이스. supervisor 의미나 `synthetic-soak` 등 인접 명령의 export 계약을 건드리지 않음.

## 핵심 변경

- `scripts/pipeline_runtime_gate.py`
  - helper 두 개 추가:
    - `_fault_check_json_sidecar_path(report_path)` — markdown path에 `with_suffix(".json")`을 적용해 페어된 JSON 경로를 돌려줌. `.md` 파일과 suffix 없는 파일 양쪽 모두 안전.
    - `_write_fault_check_json_sidecar(json_path, *, title, ok, summary_fields, checks)` — `{"title", "ok", "summary", "checks"}` 구조의 payload를 `json.dumps(..., ensure_ascii=False, indent=2) + "\n"`으로 기록. 부모 디렉터리가 없으면 먼저 생성.
  - `main()`의 `fault-check` 분기에서 summary를 `summary_fields` dict로 먼저 만들고 기존 `summary` list는 `f"{key}={value}"`로 파생시키도록 바꿔, markdown report 내용과 동일 source에서 JSON sidecar도 쓰게 함. markdown report 쓰기 직후 sidecar writer를 호출해 같은 `checks` 리스트(각 entry의 `data` 포함)를 그대로 JSON에 담음. stdout 출력과 종료 코드는 기존과 동일.
- `tests/test_pipeline_runtime_gate.py`
  - `test_fault_check_cli_writes_markdown_and_json_sidecar_with_structured_checks`: `main(["--project-root", root, "fault-check", "--workspace-root", root, "--report", path/to/foo.md])`를 실행하고 `prepare_synthetic_workspace`, `run_fault_check`, `_finalize_synthetic_workspace`를 mock해 probe/lifecycle/recovery 체크가 담긴 `checks` 리스트를 주입. markdown `PASS` 섹션들이 그대로 나오는지, JSON sidecar(`.json`)가 존재하며 `title`, `ok`, `summary.session`/`mode`/`workspace_retained`/`workspace_cleanup`과 각 대표 체크(probe, `runtime start`, `status surface ready`, `lane recovery`)의 `data` payload가 그대로 보존되는지 검증. exit code 0 유지.
  - `test_fault_check_json_sidecar_path_swaps_md_suffix_and_appends_for_suffixless_paths`: helper가 `.md` suffix를 `.json`으로 치환하고, suffix 없는 path에는 `.json`을 append하는지 단위 검증.
- `.pipeline/README.md`
  - 직전 라운드의 lifecycle 문단 다음에 한 줄을 추가해 JSON sidecar 계약(`{"title", "ok", "summary", "checks"}` 구조, basename 공유, `data` payload 보존)을 명시.

## 검증

- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_gate` → 28/28 pass (기존 26건 + 이번 라운드 추가 2건).
- `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md` → 전체 `PASS`. 실행 후 `/tmp/projecth-runtime-fault-check.md`와 `/tmp/projecth-runtime-fault-check.json`이 동시에 존재. markdown 내용은 이전 라운드와 동일.
- 핸드오프가 요구한 sidecar python one-liner (`json.loads(...); any(item.get("name")=="runtime start" and "data" in item ...)` 등)도 실제 실행에서 "sidecar assertions passed"로 통과.
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- JSON sidecar는 `--report` flag가 지정됐든 default path로 떨어지든 항상 같은 basename에 `.json`으로 붙음. 기존 consumer가 report 디렉터리에 markdown만 두는 운영 전제를 가졌다면 JSON 파일이 새로 생김으로써 tooling이 예상치 못한 파일을 만날 수 있음. 이번 slice에서는 report-directory 정책을 넓히지 않고 CLI 경로만 확장함.
- `synthetic-soak`와 `check-operator-classification` 등 다른 CLI 경로는 이번 라운드에서 수정하지 않았기 때문에 여전히 markdown만 기록함. 같은 sidecar 계약을 반복 적용하려면 별도 슬라이스가 필요하며, 이번 라운드에서는 스코프를 좁게 유지.
- JSON payload는 `ensure_ascii=False, indent=2`로 기록되어 비교적 사람이 읽기 쉽지만 크기가 늘어남. 보존된 synthetic workspace 테스트에서 6~10KB 수준이므로 당장은 문제 없으나 soak 경로로 확장할 경우 크기 통제를 같이 검토해야 함.
