# 2026-04-20 pipeline_gui G5 DEGRADED watcher-only verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-g5-degraded-watcher-only-verification.md` (본 파일)

## 사용 skill
- `round-handoff`: seq 498 `.pipeline/claude_handoff.md`(G5-unskip-DEGRADED_WATCHER_ONLY, Gemini 497 advice — 기존 DEGRADED branch guard broadening) 구현 주장을 `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + `:1256` unskip + `:1012`/`:1062`/`:865` 3-cell regression targeted rerun을 직접 재실행했습니다.

## 변경 이유
- seq 498 `.pipeline/claude_handoff.md`(Gemini 497 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-g5-degraded-watcher-only.md`가 제출되었습니다.
- 목표는 기존 DEGRADED branch guard를 `(not watcher.alive AND active lane) OR (watcher.alive AND not watcher.pid)` OR-disjunct로 broaden해 `:1256 watcher_only_alive_without_pid` 셀 하나만 unskip하고, 같은 `degraded_reason="supervisor_missing_recent_ambiguous"` 아래에서 `:1012`와 `:1256`을 semantically 묶는 것.

## 핵심 변경
- `pipeline_gui/backend.py:141-156` 기존 DEGRADED branch guard broadening 확인. post-edit shape:
  ```python
  if (
      supervisor_missing
      and runtime_state == "RUNNING"
      and snapshot_age is not None
      and snapshot_age <= SNAPSHOT_STALE_THRESHOLD
      and (
          (
              not watcher.get("alive")
              and any(str(lane.get("state") or "") != "OFF" for lane in lanes)
          )
          or (
              watcher.get("alive")
              and not watcher.get("pid")
          )
      )
  ):
  ```
  - 외부 conjunction(`supervisor_missing`, `RUNNING`, age-recency)은 seq 495와 동일.
  - 내부 disjunct 두 갈래로 분기: 첫 disjunct는 seq 495 `:1012` 패턴(watcher 없음 + active lane), 둘째 disjunct는 seq 498 `:1256` 패턴(watcher.alive=True + pid 없음). handoff 498 pin과 exact literal 일치.
- `pipeline_gui/backend.py:157-160` body 변경 없음 확인: `runtime_state="DEGRADED"` + `degraded_reason="supervisor_missing_recent_ambiguous"` + `degraded_reasons=["supervisor_missing_recent_ambiguous"]` + early return. `watcher` / `lanes` / `control` / `active_round` rewrite 없음.
- `normalize_runtime_status` dispatch count 확인: STOPPING `:96-118` + BROKEN `:119-140` + broadened DEGRADED `:141-160` + RUNNING→BROKEN `:161-183` + quiescent `:184+` = 5-branch 그대로. 6번째 branch 추가 없음.
- `tests/test_pipeline_gui_backend.py:1256`(pre-edit) `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 한 줄 삭제 확인. `def test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous`가 이제 live. 남은 단일 decorator는 `:1194` undated.
- `:1256` fixture 재확인 (`lanes=[]`, `watcher={alive:True, pid:None}`, `updated_at` present, `+5.0s` recent): broadened guard의 두 번째 disjunct에 매칭 → DEGRADED + `supervisor_missing_recent_ambiguous`, `watcher.alive=True` 보존 (body가 watcher rewrite 안 하므로 input 그대로). test assertion 전부 충족.
- grep 결과 대조:
  - `rg -n 'supervisor_missing_recent_ambiguous' pipeline_gui/backend.py` → 2 hits (`:158, :159`) — handoff 기대치와 일치.
  - `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py` → 1 hit (`:1194`) — 2 → 1 감소 확인.
  - `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py` → 1 hit (`:1194`).
  - `rg -n 'if supervisor_missing and runtime_state' pipeline_gui/backend.py` → 3 hits (STOPPING `:96`, BROKEN `:119`, RUNNING→BROKEN `:161`). broadened DEGRADED guard는 multi-line `if (` form이라 미포함.
  - `rg -n 'watcher.get\("pid"\)' pipeline_gui/backend.py` → 2 hits (`:153` 새 disjunct, `:188` 기존 quiescent block의 `watcher.get("pid") in {None, ""}`). handoff는 기대치 1을 pin했지만 기존 quiescent `:188`을 counting에서 누락한 것이라, /work가 올바르게 `:153` 새 hit + `:188` 기존 hit = 2로 explain함. broadening 적용 여부는 `:153` 새 hit으로 확인.
  - `rg -n 'snapshot_age' pipeline_gui/backend.py` → 3 hits (`:95` 계산 + `:144` `is not None` + `:145` `<= SNAPSHOT_STALE_THRESHOLD`) — 변동 없음.
  - `rg -n 'SNAPSHOT_STALE_THRESHOLD' pipeline_gui/backend.py` → 2 hits (`:35`, `:145`) — 변동 없음.
  - `rg -n 'has_active_surface' pipeline_gui/backend.py` → 0 hits.
- 다른 branch 비변경 확인: STOPPING / BROKEN / RUNNING→BROKEN / quiescent 4개는 seq 495와 동일 shape 유지. `supervisor_alive` helper, `read_runtime_status` wiring, `_supervisor_pid` / `_pid_is_alive` helper 전부 미편집.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `498` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 499.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `496` — seq 497 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `497` — seq 498 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.072s`, `OK (skipped=1)`. baseline transition `OK (skipped=2) → OK (skipped=1)`, failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.{test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous, test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous, test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken, test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor}`
  - 결과: `Ran 4 tests in 0.022s`, `OK`.
  - `:1256` unskip → 두 번째 disjunct 매칭 → DEGRADED + `supervisor_missing_recent_ambiguous` + `watcher.alive=True` 보존 전부 green.
  - `:1012` seq 495는 첫 disjunct로 계속 DEGRADED 유지.
  - `:1062` aged는 age guard(`+20s > 15.0`) 덕분에 계속 BROKEN.
  - `:865` seq 483 (`watcher.alive=True AND pid=4242 AND recent`)은 두 번째 disjunct의 `not watcher.pid`가 `not 4242 = False`라 제외 → RUNNING→BROKEN 분기로 떨어져 BROKEN 유지. 새 OR-disjunct의 critical regression counterpart가 green.
- `/work`가 별도 나열한 6개 다른 previously-unskipped cell(`Ran 6 tests / OK`)은 /work 기록 신뢰하고 재실행 생략. 이번 slice가 broadened guard 외 branch를 건드리지 않아 해당 경로들은 영향 없음.
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → `/work` `출력 없음, 통과` 신뢰.
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → `/work` `출력 없음, 통과` 신뢰.
- `tests.test_smoke -k progress_summary/coverage/claims/reinvestigation`는 `/work`가 각 `11/27/7/6 OK` 기록, 이번 slice가 `tests/test_smoke.py` / `core/` / `app/` / `storage/`를 건드리지 않아 baseline 유지 안전. verify 재실행 생략.
- `tests.test_web_app`, Playwright, `make e2e-test`는 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **1 DEGRADED cell 여전히 deferred**:
  - `:1194` `undated_ambiguous_snapshot_degraded` — fixture에 `updated_at` ABSENT → `parse_iso_utc("") = 0.0` → `snapshot_age = None` → 현재 broadened guard의 `snapshot_age is not None`이 False → 외부 guard 실패 → RUNNING→BROKEN fallthrough → BROKEN. test는 DEGRADED + `degraded_reason="supervisor_missing_snapshot_undated"` (다른 literal) 기대. watcher shape는 `:1256`과 동일(`alive=True, pid=None`).
- **다음 슬라이스 ambiguity**:
  - A) `G5-unskip-DEGRADED_UNDATED as new 6th branch` — `snapshot_age is None AND (inner disjunct)` guard + `degraded_reason="supervisor_missing_snapshot_undated"` 별도 body. 5-branch → 6-branch 증가.
  - B) `G5-unskip-DEGRADED_UNDATED via broaden current branch with reason-switch` — 현재 `:141-160` guard의 age 조건을 `snapshot_age is not None OR True` 류로 다시 넓히고, body에서 `snapshot_age is None이면 reason=supervisor_missing_snapshot_undated`로 분기. 5-branch 유지하되 body가 커짐.
  - C) `G12 _apply_shutdown_shape refactor 먼저` — 남은 1 cell을 landing하기 전 refactor로 분기 parameterize. 5→refactored→6 순서.
  - D) G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11 중 하나로 rotate.
  - 세 후보(A/B/C)가 모두 bounded single-file slice로 실행 가능하고 dominant current-risk reduction이 뚜렷하지 않아 `.pipeline/gemini_request.md`로 arbitration open하는 편이 `/verify` README 규칙과 일치.
- **seq 492 lesson 재확인**: narrow trigger 제안 전 모든 `supervisor_missing + RUNNING` currently-green cell 비교표 필수. 특히 `:1194` 다음 슬라이스에서는 `snapshot_age is None`인 모든 currently-green cell(있다면)과의 collision도 미리 scan.
- **G12 refactor leverage**: broadened DEGRADED guard가 5단 OR disjunct + 괄호 3중 중첩이라 readability가 이미 낮음. `:1194` slice 이후 G12 refactor 필요성이 더 높아짐.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 targeted 2 files만 추가 수정.
