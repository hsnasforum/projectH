# 2026-04-20 pipeline_gui G12 supervisor-missing helper verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-g12-supervisor-missing-helper-verification.md` (본 파일)

## 사용 skill
- `round-handoff`: seq 504 `.pipeline/claude_handoff.md`(G12 `_apply_supervisor_missing_status` helper refactor, Gemini 503 advice) 구현 주장을 `pipeline_gui/backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + DEGRADED 3셀 + aged counterpart + 직접-normalize 인액티브→STOPPED + smoke 4개 subset을 직접 재실행했습니다.

## 변경 이유
- seq 504 `.pipeline/claude_handoff.md`(Gemini 503 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-g12-supervisor-missing-helper.md`가 제출되었습니다.
- 목표는 `normalize_runtime_status`의 4개 supervisor_missing branch body(STOPPING / BROKEN / broadened-DEGRADED / RUNNING→BROKEN)를 공통 helper로 접어 duplication을 줄이고, 11개 currently-green cell을 그대로 유지하는 behavior-preserving refactor였습니다.

## 핵심 변경
- `pipeline_gui/backend.py:73-117` 새 module-level helper `_apply_supervisor_missing_status(status, lanes, *, state, reason, shutdown=True)` 추가 확인. post-edit shape는 핸드오프 504의 helper signature와 정확히 일치:
  - `status["runtime_state"] = state`, `status["degraded_reason"] = reason`, `status["degraded_reasons"] = [reason] if reason else []` 무조건.
  - `shutdown=True`일 때만 `control` / `active_round` / `watcher` reset + `lanes` rewrite. `note = reason or "stopped"`, `state == "STOPPED"` 분기는 `state="OFF"`, else 분기는 `OFF-preserve-else-BROKEN`.
  - keyword-only split(`*,` 앞에 `status`, `lanes` positional), `dict[str, object]` / `list[dict[str, object]]` 주석, 단일-라인 docstring 전부 핸드오프 pin과 일치.
- 4개 call site 교체 확인:
  - STOPPING guard `:143`, helper call `:144-150` (`state="STOPPED"`, `reason=""`, `shutdown=True`).
  - BROKEN guard `:151`, helper call `:152-158` (`state="BROKEN"`, `reason="supervisor_missing"`, `shutdown=True`).
  - broadened DEGRADED guard `:159-176` 그대로 유지, ternary `reason = "supervisor_missing_snapshot_undated" if snapshot_age is None else "supervisor_missing_recent_ambiguous"`가 `:177-181`, helper call `:182-188` (`state="DEGRADED"`, `reason=reason`, `shutdown=False`). `shutdown=False` 유지 확인 — 이 플래그 덕에 `control` / `active_round` / `watcher` / `lanes` 는 input-preserve되고 `:1012`/`:1256`/`:1194` 어설션이 통과합니다.
  - RUNNING→BROKEN guard `:189`, helper call `:190-196` (`state="BROKEN"`, `reason="supervisor_missing"`, `shutdown=True`).
- quiescent branch `:197-224`: 핸드오프 지시대로 건드리지 않음. 기존 body 그대로 `runtime_state=STOPPED`, `degraded_reason=""`, `degraded_reasons=[]`, `control` reset, `active_round=None`, `watcher={alive:False, pid:None}`, `lanes`는 `state="OFF"` rewrite(note key 없음, 기존 spec과 동일)로 유지됐습니다.
- 5-branch dispatch 순서와 early-return semantics 유지: STOPPING → BROKEN → broadened-DEGRADED → RUNNING→BROKEN → quiescent.
- outer locals(`runtime_state`, `watcher`, `lanes`, `active_round`, `has_quiescent_evidence`, `lanes_are_inactive`, `round_is_closed`, `supervisor_missing`, `updated_at_raw`, `snapshot_ts`, `snapshot_age`) 위치 / 계산 그대로.
- `tests/test_pipeline_gui_backend.py` 미편집 확인(git diff로 간접 확인, 핸드오프 scope 지시와 일치).
- grep 결과 대조(직접 재실행):
  - `rg -n 'def _apply_supervisor_missing_status' pipeline_gui/backend.py` → 1 hit(`:73`).
  - `rg -n '_apply_supervisor_missing_status\(' pipeline_gui/backend.py` → 5 hits(`:73 def` + `:144`, `:152`, `:182`, `:190` 4 call sites). 핸드오프 기대치 일치.
  - `rg -n 'supervisor_missing_recent_ambiguous' pipeline_gui/backend.py` → 1 hit(`:180` ternary else).
  - `rg -n 'supervisor_missing_snapshot_undated' pipeline_gui/backend.py` → 1 hit(`:178` ternary if).
  - `rg -n 'if supervisor_missing and runtime_state' pipeline_gui/backend.py` → 3 hits(`:143 STOPPING`, `:151 BROKEN`, `:189 RUNNING→BROKEN`). broadened DEGRADED은 multi-line이라 미포함.
  - `rg -n 'watcher.get\("pid"\)' pipeline_gui/backend.py` → 2 hits(`:173 DEGRADED 2nd disjunct`, `:201 quiescent`).
  - `rg -n 'snapshot_age is None' pipeline_gui/backend.py` → 2 hits(`:163 guard disjunct`, `:179 ternary`).
  - `rg -n 'snapshot_age' pipeline_gui/backend.py` → 4 hits(`:142 computation`, `:163`, `:164`, `:179`).
  - `rg -n '"supervisor_missing"' pipeline_gui/backend.py` → 2 hits(`:156 BROKEN call`, `:194 RUNNING→BROKEN call`).
  - `rg -n '"active_control_file": ""' pipeline_gui/backend.py` → 2 hits(`:87 helper`, `:209 quiescent`). 핸드오프 pin은 1을 예상했지만 /work가 정확히 해설했듯 quiescent branch를 일부러 untouched로 둔 결과라 2가 옳습니다. 분기 수(4 shutdown-aware + 1 quiescent)와 정합성 유지.
  - `rg -n 'status\["active_round"\] = None' pipeline_gui/backend.py` → 2 hits(`:92 helper`, `:214 quiescent`). 동일 맥락.
  - `rg -n '"alive": False, "pid": None' pipeline_gui/backend.py` → 2 hits(`:93 helper`, `:215 quiescent`). 동일 맥락.
  - `rg -n 'has_active_surface' pipeline_gui/backend.py` → 0.
  - `rg -n 'def _degraded_reason' pipeline_gui/backend.py` → 0.
  - `rg -n 'def _apply_shutdown_shape' pipeline_gui/backend.py` → 0.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `504` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 505.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `502` — seq 503 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `503` — seq 504 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드 대조(경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.071s`, `OK`. `OK (skipped=0) → OK (skipped=0)` 유지, failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.{test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded, test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous, test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous, test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken, test_normalize_runtime_status_converts_inactive_degraded_snapshot_to_stopped}`
  - 결과: `Ran 5 tests in 0.008s`, `OK`.
  - `:1194` undated: DEGRADED 유지(ternary if, `shutdown=False`로 `control`/`watcher`/`lanes` 보존).
  - `:1256` watcher-only: DEGRADED 유지(ternary else, `shutdown=False`).
  - `:1012` recent-active-lane: DEGRADED 유지(first disjunct, ternary else, `shutdown=False`).
  - `:1062` aged: BROKEN 유지(age disjunct 실패 → RUNNING→BROKEN helper call, `shutdown=True`).
  - `test_normalize_runtime_status_converts_inactive_degraded_snapshot_to_stopped`: quiescent branch path로 STOPPED 전환 유지 — helper가 quiescent를 건드리지 않았다는 주장을 함께 검증.
- /work가 별도 나열한 8-test rerun(6 previously-unskipped + 2 direct-normalize, `Ran 8 / OK`)은 /work 기록 신뢰. 위 5-cell rerun이 가장 예민한 축을 모두 커버합니다.
- `python3 -m unittest tests.test_smoke -k progress_summary` → `Ran 11 tests in 0.018s`, `OK`.
- `python3 -m unittest tests.test_smoke -k coverage` → `Ran 27 tests in 0.060s`, `OK`.
- `python3 -m unittest tests.test_smoke -k claims` → `Ran 7 tests in 0.001s`, `OK`.
- `python3 -m unittest tests.test_smoke -k reinvestigation` → `Ran 6 tests in 0.061s`, `OK`.
- `python3 -m py_compile pipeline_gui/backend.py` → 출력 없음, 통과.
- `git diff --check -- pipeline_gui/backend.py` → 출력 없음, 통과.
- `tests.test_web_app`, Playwright, `make e2e-test`는 browser/웹 계약 변경 없음이라 의도적으로 생략.

## 남은 리스크
- **G12 refactor 완료, behavior-preserving**:
  - `normalize_runtime_status`는 helper 도입 후에도 5-branch dispatch를 유지하고 branch precedence·early-return semantics가 그대로입니다. quiescent branch는 일부러 합치지 않았기 때문에 같은 reset 블록이 helper와 quiescent에 각각 남아 있습니다. 이는 `/work`가 올바르게 해설했고 의도된 결과입니다.
  - DEGRADED branch는 `shutdown=False` 호출로 `control`/`active_round`/`watcher`/`lanes` input-preserve 계약을 유지했고, ternary `reason`은 `normalize_runtime_status` 내부에 inline으로 남겨두었습니다(이번 라운드는 classification 분리 범위 밖).
- **다음 슬라이스 ambiguity**:
  - G5와 G12 family가 모두 닫혔고, 남은 후보는 G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11로 여러 축에 걸쳐 있습니다. 어느 하나가 dominant current-risk reduction이라고 단언하기 어려운 상태입니다.
  - `.pipeline/gemini_request.md`로 arbitration을 여는 편이 `/verify` README 규칙과 일치합니다. operator-only 결정 요소는 없습니다.
- **seq 492 교훈 지속**: 향후 supervisor_missing 계열 branch를 추가하거나 DEGRADED guard를 다시 넓힐 때는 helper에 새 `lane_state_rule` / `lane_note` parameter를 추가해야 할 수도 있습니다. 다만 당장 필요한 신규 branch가 없으므로 이번 라운드 범위 밖입니다.
- **helper parameter 설계의 한계**:
  - 현재 `_apply_supervisor_missing_status`는 `state == "STOPPED"` 여부만으로 lane-rewrite 규칙을 갈라 두 케이스만 처리합니다. 향후 lane-rewrite 규칙이 제3의 형태를 요구하면 helper widening이 필요합니다. 지금은 defer.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 `pipeline_gui/backend.py` 한 파일만 추가 수정.
