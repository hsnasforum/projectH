# Soak CLI JSON sidecar export

## 변경 파일

- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_gate.py`
- `.pipeline/README.md`

## 사용 skill

- 없음

## 변경 이유

- `.pipeline/claude_handoff.md` (CONTROL_SEQ: 306, HANDOFF_SHA `54ffbb16...`)가 `fault-check`에 이어 `synthetic-soak`와 plain `soak` CLI도 markdown과 같은 basename으로 JSON sidecar를 남기도록 확장하라고 지목함. 두 CLI 모두 `run_soak()`이 만든 풍부한 summary/check 데이터를 이미 in-memory로 들고 있으면서 markdown만 내보내던 export 경계를 좁히는 슬라이스.
- `check-operator-classification`은 handoff가 이번 slice에서는 넘기라고 명시했으므로 건드리지 않음.

## 핵심 변경

- `scripts/pipeline_runtime_gate.py`
  - 이전 라운드의 `_fault_check_json_sidecar_path` / `_write_fault_check_json_sidecar` 헬퍼를 `_report_json_sidecar_path` / `_write_report_json_sidecar`로 리네이밍해 세 CLI가 공유하는 단일 sidecar writer로 만들었음. JSON payload 구조(`{"title", "ok", "summary", "checks"}`)는 그대로 유지해 기존 fault-check 계약이 깨지지 않음.
  - 새 헬퍼 `_soak_summary_fields(summary, *, base)`를 추가해 `run_soak()` summary dict를 JSON-safe한 평탄화된 구조로 옮기고, path-specific base(`project`, `session`, `mode`, synthetic의 `workspace_retained`/`workspace_cleanup`)는 호출자 쪽에서 주입.
  - `main()`의 `synthetic-soak` 분기에서 markdown write 이후 `_write_report_json_sidecar(_report_json_sidecar_path(report_path), ...)` 호출을 추가. 기본 report path(`default_report_path(...)`)를 쓸 때도 sidecar가 같은 디렉터리에 같은 basename으로 함께 남음.
  - 동일 패턴을 `main()`의 plain `soak` 분기에도 적용. stdout 출력과 종료 코드는 이전과 동일.
- `tests/test_pipeline_runtime_gate.py`
  - `test_synthetic_soak_cli_writes_markdown_and_json_sidecar`: `main()`을 `synthetic-soak` argv로 호출해 markdown `.md`와 JSON `.json` 두 파일이 동시에 생기는지, JSON `summary`에 `project`/`mode`/`workspace_retained`/`workspace_cleanup`/`receipt_count`/`duplicate_dispatch_count`/`classification_gate_failures`/`classification_gate_details`/`orphan_session`/`readiness_snapshot`이 담기고 `checks`에 `runtime ready barrier` 등 대표 체크가 포함되는지 확인. 모든 파일 접근은 tempdir 블록 안에서 수행하도록 바로잡음.
  - `test_plain_soak_cli_writes_markdown_and_json_sidecar`: 동일 계약을 plain `soak` 경로에도 잠금. synthetic 전용 필드(`workspace_retained`/`workspace_cleanup`)는 plain 경로 summary에 들어가지 않는다는 점까지 검증.
  - 기존 `test_fault_check_json_sidecar_path_swaps_md_suffix_and_appends_for_suffixless_paths` 테스트를 새 helper 이름으로 변경해 `test_report_json_sidecar_path_swaps_md_suffix_and_appends_for_suffixless_paths`로 유지.
- `.pipeline/README.md`
  - 직전 라운드의 fault-check JSON sidecar 문단 다음에 한 줄을 추가해 `synthetic-soak`와 plain `soak` CLI도 같은 sidecar 계약을 공유하며, summary에 `run_soak()` 결과가 평탄화되어 실린다는 점과 synthetic 전용 필드(`workspace_retained`/`workspace_cleanup`) 차이를 명시.

## 검증

- `python3 -m py_compile scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py` → 통과.
- `python3 -m unittest -v tests.test_pipeline_runtime_gate` → 30/30 pass (기존 28건 + 이번 라운드 추가 2건 + 이름 변경 1건 업데이트).
- `python3 scripts/pipeline_runtime_gate.py synthetic-soak --workspace-root /tmp --duration-sec 10 --sample-interval-sec 1 --min-receipts 1 --report /tmp/projecth-runtime-synthetic-soak.md` 실행 결과 markdown/JSON 두 파일이 함께 생성되고, handoff가 요구한 Python one-liner(`any(item.get("name")=="runtime ready barrier"...)`, `classification_fallback_detected...`)도 "synthetic soak sidecar assertions passed"로 통과.
  - 이 실행의 전체 exit code는 `1`로 끝났는데, `synthetic workload produced receipts` 체크만 FAIL이고(10초 duration에 receipt가 아직 쌓이지 않음) 이는 이번 slice가 만지지 않는 synthetic workload의 기존 특성. 이 현상은 markdown과 JSON 모두에 같은 FAIL check로 기록되며 sidecar 구조/필드에는 영향 없음.
- 직전 라운드의 `fault-check` sidecar 회귀가 없는지 확인하기 위해 `python3 scripts/pipeline_runtime_gate.py fault-check --workspace-root /tmp --report /tmp/projecth-runtime-fault-check.md`를 재실행해 exit 0 + handoff의 fault-check sidecar one-liner 통과 확인.
- plain `soak` 경로는 focused unit test(`test_plain_soak_cli_writes_markdown_and_json_sidecar`)로 CLI-level behavior 잠금. live tmux 환경에서 별도 실행은 범위 밖.
- `git diff --check -- scripts/pipeline_runtime_gate.py tests/test_pipeline_runtime_gate.py .pipeline/README.md` → clean.

## 남은 리스크

- `synthetic-soak` live 재실행은 `synthetic workload produced receipts` check가 짧은 duration에서 FAIL로 떨어질 수 있음. 이는 기존 synthetic workload 특성이며 이번 slice에서 다루지 않음. CI/operator가 sidecar consumer를 붙일 때 이 check 하나의 FAIL을 별도로 해석할 수 있어야 함.
- `check-operator-classification` CLI는 여전히 markdown만 기록함. 동일 sidecar 계약으로 확장하려면 별도 slice가 필요함.
- helper 리네이밍은 internal helper에 한정되지만, 동일 파일을 import해서 helper를 직접 호출하던 consumer가 있다면 import path를 업데이트해야 함. 현재 저장소 내에서는 `tests/test_pipeline_runtime_gate.py`만 호출하므로 영향 없음.
