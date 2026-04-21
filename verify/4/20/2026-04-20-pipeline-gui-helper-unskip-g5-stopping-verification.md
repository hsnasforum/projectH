# 2026-04-20 pipeline_gui helper unskip G5-STOPPING verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-stopping-verification.md`

## 사용 skill
- `round-handoff`: seq 474 `.pipeline/claude_handoff.md`(G5-unskip-STOPPING, Gemini 473 advice narrowed) 구현 주장을 `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + 3개 targeted regression(STOPPING 신규, seq 468 unskip, seq 471 unskip), `py_compile`, `git diff --check`을 직접 재실행했습니다.

## 변경 이유
- seq 474 `.pipeline/claude_handoff.md`(Gemini 473 advice narrowed)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-helper-unskip-g5-stopping.md`가 제출되었습니다.
- 목표는 `normalize_runtime_status`에 `project: Path | None = None` kwarg 추가, supervisor-missing STOPPING 경로만 full shutdown shape로 정규화(lane `note="stopped"` 포함), `read_runtime_status`를 normalize-wrapper로 wire, target test unskip이었고 기존 quiescent block은 비변경 유지.

## 핵심 변경
- `pipeline_gui/backend.py:71` 신규 시그니처 `def normalize_runtime_status(value: object | None, project: Path | None = None) -> dict[str, object]:` 확인. 기본값 `project=None`로 기존 caller 호환.
- `:90` `supervisor_missing = project is not None and _supervisor_pid(project) is None` 계산.
- `:91-113` 신규 분기: `supervisor_missing and runtime_state == "STOPPING"`일 때 full shutdown normalization을 적용하고 early return. lane rewrite가 `state/attachable/pid`에 더해 `"note": "stopped"`까지 포함해 target test의 `lanes[0].note == "stopped"` assertion 만족.
- `:114-141` 기존 quiescent block은 수정 없음. `note` rewrite가 없는 기존 형태 그대로 유지돼, 다른 quiescent 테스트에 영향 없음. `rg -n '"note": "stopped"' pipeline_gui/backend.py` → `:109` 1건만 hit.
- `pipeline_gui/backend.py:551-569` `read_runtime_status`:
  - current_run이 없으면 None 반환(기존 동작).
  - status_path 기반 read 실패 시 run_id 기반 fallback 유지.
  - `:567-568` `data is None` 일 때 `None` 반환(`test_read_runtime_status_returns_none_without_current_run` 보호).
  - `:569` 최종적으로 `normalize_runtime_status(data, project=project)` 호출로 wire 완료. 계약이 "raw JSON reader"에서 "supervisor reality 기준 normalize reader"로 변경됨.
- `tests/test_pipeline_gui_backend.py`의 skip decorator grep 결과 8건(`:643, :792, :867, :945, :1016, :1065, :1200, :1262`) — `/work` 기록과 정합. target test `:718` 위치 decorator 제거 확인.
- `pipeline_gui/` caller 감사 결과(`rg -n 'read_runtime_status' pipeline_gui/`): `home_controller.py:12` import, `:177` normalize wrapper call, backend 내부 `:291/630/637` 모두 `normalize_runtime_status(...)`로 감쌈. 새 wiring은 모든 caller에서 idempotent.
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471 shipped 표면 전부 미편집 유지.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `474` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 475.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `472` — seq 473 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `473` — seq 474 handoff로 narrowed + 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — seq 465 이후 지속 superseded.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.042s`, `OK (skipped=8)`. baseline `OK (skipped=9)` → post-edit `OK (skipped=8)`, 새 failures/errors 없음. handoff 기대치 정합.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_converts_stopping_without_supervisor_into_stopped tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_from_current_run_pointer tests.test_pipeline_gui_backend.TestRuntimeStatusRead.test_read_runtime_status_does_not_mark_ambiguous_when_supervisor_is_alive`
  - 결과: `Ran 3 tests in 0.009s`, `OK`. 신규 STOPPING cell + seq 471 unskip + seq 468 unskip 모두 green 유지.
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과.
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py`
  - 결과: 출력 없음, 통과.
- `-k progress_summary/coverage/claims/reinvestigation`는 `/work`가 각 11/27/7/6 OK로 기록했고, 이번 slice는 `tests/test_smoke.py` / `core/` / `app/` / `storage/` 미편집이라 baseline 유지가 안전하게 추정됨. verify 재실행 생략.
- `tests.test_web_app`, Playwright, `make e2e-test`는 이번 라운드 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **read_runtime_status 계약 변경**: 이제 "supervisor reality를 반영한 normalize reader". raw JSON pass-through를 기대하던 caller가 있다면 normalized output을 보게 되고, seq 471 `/work`의 "thin reader" 설명은 stale. 현재 caller 감사 결과(`home_controller.py:177`, `backend.py:291/630/637`) 모두 normalize wrapper 사용이라 fragile caller는 없지만, 후속 라운드에서 새 caller가 추가되면 이 계약을 다시 확인해야 합니다.
- **lane `"note": "stopped"` 비대칭**: 새 supervisor-missing STOPPING branch에만 설정되고 기존 quiescent block에는 없음. 향후 quiescent 경로에서도 `note` 필드를 기대하는 테스트가 생기면 기존 block도 확장해야 합니다.
- **normalize_runtime_status call-site convention cleanup 미수행**: `runtime_state` / `runtime_active`가 여전히 `normalize_runtime_status(read_runtime_status(project))` 형태로 project를 넘기지 않음. correctness 영향은 없지만(이미 `read_runtime_status` 내부에서 project 기반 normalize가 한 번 적용됨), 장기적으로는 명시적 `project=project` 전달이 코드 일관성에 유리합니다.
- **8 cells 여전히 deferred**: `TestRuntimeStatusRead`의 나머지 8개 cell은 `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 상태. future G5-unskip-* sub-family(RUNNING→BROKEN variants, RUNNING→DEGRADED variants, aged ambiguous, degraded_reason vocabulary, watcher-only-alive)는 각각 bounded slice로 풀 수 있지만, 각 unskip은 backend 상태 규칙 + 해당 decorator 삭제를 함께 해야 합니다.
- **다음 슬라이스 ambiguity**: 남은 G5-unskip-* 후보 + G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11가 모두 서로 다른 축이고 dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 475)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests 잔존**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. this slice는 backend + tests이고 docs drift 유발 없음. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 해당 파일들을 건드리지 않음.
