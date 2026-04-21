# 2026-04-20 pipeline_gui G5 undated DEGRADED unskip verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-g5-undated-degraded-unskip-verification.md` (본 파일)

## 사용 skill
- `round-handoff`: seq 501 `.pipeline/claude_handoff.md`(G5-unskip-DEGRADED_UNDATED, Gemini 500 advice — broaden 기존 DEGRADED branch의 age conjunct + body reason-switch) 구현 주장을 `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + `:1194` unskip + `:1256`/`:1012`/`:1062` 3-cell regression + smoke baseline(progress_summary/coverage/claims/reinvestigation)을 직접 재실행했습니다.

## 변경 이유
- seq 501 `.pipeline/claude_handoff.md`(Gemini 500 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-g5-undated-degraded-unskip.md`가 제출되었습니다.
- 목표는 기존 seq 498 DEGRADED branch의 age conjunct를 `(snapshot_age is None or snapshot_age <= SNAPSHOT_STALE_THRESHOLD)`로 교체해 undated payload도 같은 branch가 받도록 broaden하고, body에 local `reason` ternary를 넣어 `:1194`는 `"supervisor_missing_snapshot_undated"`로, `:1012`/`:1256`은 기존 `"supervisor_missing_recent_ambiguous"`로 유지하는 것이었습니다. 마지막 `@unittest.skip`(`:1194`) 한 줄 제거 포함.

## 핵심 변경
- `pipeline_gui/backend.py:141-167` 브로드닝 + reason-switch 확인. post-edit shape:
  ```python
  if (
      supervisor_missing
      and runtime_state == "RUNNING"
      and (
          snapshot_age is None
          or snapshot_age <= SNAPSHOT_STALE_THRESHOLD
      )
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
      reason = (
          "supervisor_missing_snapshot_undated"
          if snapshot_age is None
          else "supervisor_missing_recent_ambiguous"
      )
      status["runtime_state"] = "DEGRADED"
      status["degraded_reason"] = reason
      status["degraded_reasons"] = [reason]
      return status
  ```
  - 외부 `supervisor_missing` + `runtime_state == "RUNNING"` 유지. 내부 OR-disjunct shape(seq 498) 그대로 유지. age conjunct만 `(None or <=THRESHOLD)` 분기로 교체. body는 ternary `reason` + `status` 세 필드 rewrite + early return으로 교체. `watcher`/`lanes`/`control`/`active_round` 미편집.
  - 핸드오프가 기대한 body 줄 번호 `:157-160`는 post-edit에서 `:159-167`로 확장됐지만, ternary 포함 5줄 추가분이라 실제 효과는 정확히 pin과 일치합니다.
- `normalize_runtime_status` dispatch count 확인: STOPPING `:96-118` + BROKEN `:119-140` + broadened DEGRADED `:141-167` + RUNNING→BROKEN `:168-190` + quiescent `:191+` = 5-branch 그대로. 6번째 branch 추가 없음.
- `tests/test_pipeline_gui_backend.py:1194`(pre-edit) `@unittest.skip("pipeline_gui_backend_state_transition_deferred")` 한 줄 삭제 확인. post-edit `:1194`는 바로 `def test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded(self) -> None:`. 파일 전체 `@unittest.skip` 0건.
- grep 결과 대조(직접 재실행):
  - `rg -n 'supervisor_missing_recent_ambiguous' pipeline_gui/backend.py` → 1 hit(`:162` ternary else). 핸드오프 기대치 일치.
  - `rg -n 'supervisor_missing_snapshot_undated' pipeline_gui/backend.py` → 1 hit(`:160` ternary if). 핸드오프 기대치 일치.
  - `rg -n 'pipeline_gui_backend_state_transition_deferred' tests/test_pipeline_gui_backend.py` → 0건. 핸드오프 기대치 일치.
  - `rg -n '@unittest.skip' tests/test_pipeline_gui_backend.py` → 0건. 핸드오프 기대치 일치.
  - `rg -n 'if supervisor_missing and runtime_state' pipeline_gui/backend.py` → 3 hits(`:96 STOPPING`, `:119 BROKEN`, `:168 RUNNING→BROKEN`). broadened DEGRADED guard는 multi-line이라 미포함. 핸드오프 기대치 일치.
  - `rg -n 'watcher.get\("pid"\)' pipeline_gui/backend.py` → 2 hits(`:155 새 disjunct`, `:195 기존 quiescent`). 핸드오프 기대치 일치.
  - `rg -n 'snapshot_age is None' pipeline_gui/backend.py` → 2 hits(`:145 guard disjunct`, `:161 ternary`). 핸드오프 기대치 일치.
  - `rg -n 'snapshot_age' pipeline_gui/backend.py` → 4 hits(`:95 computation`, `:145 is None`, `:146 <=THRESHOLD`, `:161 ternary is None`). 핸드오프 기대치 일치.
  - `rg -n 'SNAPSHOT_STALE_THRESHOLD' pipeline_gui/backend.py` → 2 hits(`:35 const`, `:146 guard`). 불변.
  - `rg -n 'has_active_surface' pipeline_gui/backend.py` → 0건. 새 helper 미도입.
  - `rg -n 'def _degraded_reason' pipeline_gui/backend.py` → 0건. 새 helper function 미도입.
- 다른 branch 비변경 확인: STOPPING / BROKEN / RUNNING→BROKEN / quiescent 4개는 seq 498과 동일 shape 유지. `supervisor_alive`, `read_runtime_status`, `_supervisor_pid`, `_pid_is_alive`, `parse_iso_utc` 전부 미편집.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `501` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 502.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `499` — seq 500 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `500` — seq 501 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드/테스트 대조(경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.061s`, `OK`. baseline transition `OK (skipped=1) → OK (skipped=0)`, failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.{test_read_runtime_status_marks_undated_ambiguous_snapshot_degraded, test_read_runtime_status_marks_watcher_only_alive_without_pid_degraded_ambiguous, test_read_runtime_status_marks_recent_active_lane_without_supervisor_pid_degraded_ambiguous, test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken}`
  - 결과: `Ran 4 tests in 0.009s`, `OK`.
  - `:1194` unskip → broadened guard outer True(`snapshot_age is None`) + 두 번째 disjunct(`watcher.alive=True AND not watcher.pid`) 매칭 → DEGRADED + ternary `snapshot_age is None` 분기로 `supervisor_missing_snapshot_undated` 채택 + `control.active_control_status="implement"` + `watcher.alive=True` 보존. 전부 green.
  - `:1256` seq 498 regression: `snapshot_age is None = False` → ternary else로 계속 recent-ambiguous literal 유지. DEGRADED green.
  - `:1012` seq 495 regression: first disjunct + recent literal 그대로 유지. DEGRADED green.
  - `:1062` aged regression: `snapshot_age is None = False AND 20 <= 15 = False` → age disjunct 전체 False → outer fails → BROKEN 유지.
- `/work`가 별도 나열한 8-cell rerun(6개 previously-unskipped + 2개 direct-normalize, `Ran 8 tests / OK`)은 /work 기록 신뢰. 이번 slice가 broadened guard 외 branch를 건드리지 않아 영향 없음.
- `/work`의 `TestRuntimeStatusNormalize` AttributeError 노트 확인: 해당 class가 test module에 존재하지 않는 게 맞고, 동등 범위의 `test_normalize_runtime_status_drops_non_mapping_payload`/`test_normalize_runtime_status_converts_inactive_degraded_snapshot_to_stopped`가 `TestRuntimeStatusRead` 밑에 있어 8-test rerun에 포함되어 있음. verify 관점에서도 오해는 없음(class 이름을 고정한 실수였을 뿐 테스트 coverage 자체는 확보됨).
- `python3 -m unittest tests.test_smoke -k progress_summary` → `Ran 11 tests in 0.015s`, `OK`.
- `python3 -m unittest tests.test_smoke -k coverage` → `Ran 27 tests in 0.055s`, `OK`.
- `python3 -m unittest tests.test_smoke -k claims` → `Ran 7 tests in 0.001s`, `OK`.
- `python3 -m unittest tests.test_smoke -k reinvestigation` → `Ran 6 tests in 0.063s`, `OK`.
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `tests.test_web_app`, Playwright, `make e2e-test`는 의도적으로 생략(browser/웹 계약 변경 없음).

## 남은 리스크
- **G5-unskip-DEGRADED family 완전 폐기**:
  - `tests/test_pipeline_gui_backend.py` 파일 전체에 `@unittest.skip`가 남아 있지 않습니다. DEGRADED family 3셀(`:1012`, `:1256`, `:1194`)이 모두 green.
- **DEGRADED body 복잡도 증가**:
  - 기존 seq 498의 nested-OR guard 3중 중첩에, 이번 라운드에서 ternary reason-switch까지 body로 들어갔습니다. `normalize_runtime_status`의 DEGRADED 분기는 이제 `guard(18 lines) + ternary(5 lines) + assign(3 lines)`로 가장 두꺼운 branch가 됐습니다. G12 `_apply_shutdown_shape` refactor leverage가 그 어느 때보다 큽니다.
- **다음 슬라이스 ambiguity**:
  - G12 `_apply_shutdown_shape` — 5개 branch(STOPPING/BROKEN/broadened DEGRADED/RUNNING→BROKEN/quiescent)를 parameterized helper로 합치는 refactor. 저-중 위험, 순수 내부 cleanup. "helper-level neatness" 영역이라 선택 시 guardrail 고려 필요.
  - G7 REASON_CODE / OPERATOR_POLICY vocabulary 고정 — `.pipeline/operator_request.md` / `work` closeout / handoff 전반에서 reason code를 열거형으로 강제. 구조적.
  - G8 memory-foundation next slice — long-term north star와 정렬되지만 exact slice pin이 별도 필요.
  - G3 reinvestigation prefer_probe_first threshold tuning — 투기적.
  - G6-sub2 / G6-sub3 / G9 / G10 / G11 — 계속 deferred.
  - 단독 dominant current-risk reduction이 뚜렷하지 않고 후보가 여러 축에 걸쳐 있어 `.pipeline/gemini_request.md`로 arbitration을 여는 편이 `/verify` README 규칙과 일치.
- **seq 492 교훈 지속**: 앞으로 DEGRADED 혹은 state-dispatch 경로에 trigger를 더 넓히거나 넘길 때는 dated + undated 양쪽 currently-green cell 전체와 비교표 필수.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 targeted 2 files만 추가 수정.
