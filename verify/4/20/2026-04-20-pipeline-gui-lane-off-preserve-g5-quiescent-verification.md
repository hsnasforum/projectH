# 2026-04-20 pipeline_gui lane OFF preserve G5-quiescent verification

## 변경 파일
- `verify/4/20/2026-04-20-pipeline-gui-lane-off-preserve-g5-quiescent-verification.md`

## 사용 skill
- `round-handoff`: seq 489 `.pipeline/claude_handoff.md`(G5-unskip-QUIESCENT_LANE, Gemini 488 advice) 구현 주장을 `pipeline_gui/backend.py`, `tests/test_pipeline_gui_backend.py` 실제 상태와 대조했고, 전체 `tests.test_pipeline_gui_backend` + 5개 targeted regression(신규 field_quiescent + seq 486/483/480/477) + `py_compile` + `git diff --check`을 직접 재실행했습니다.

## 변경 이유
- seq 489 `.pipeline/claude_handoff.md`(Gemini 488 advice)가 구현되어 새 `/work` 노트 `work/4/20/2026-04-20-pipeline-gui-lane-off-preserve-g5-quiescent.md`가 제출되었습니다.
- 목표는 seq 477 BROKEN branch + seq 480 RUNNING→BROKEN branch의 lane state rewrite를 `"BROKEN"` 고정 → 조건부(OFF 보존, 그 외 BROKEN)로 refine하고 `:942` skip decorator 한 줄 삭제.

## 핵심 변경
- `pipeline_gui/backend.py:128` (seq 477 BROKEN branch lane state) + `:151` (seq 480 RUNNING→BROKEN branch lane state) 두 위치 모두 조건부로 변경 확인: `lane.get("state") if str(lane.get("state") or "") == "OFF" else "BROKEN"`
  - `"OFF"` 입력은 보존, 그 외는 `"BROKEN"`으로 rewrite. handoff 지시와 exact literal 일치.
- 다른 lane field(`attachable=False`, `pid=None`, `note="supervisor_missing"`)는 기존 무조건 rewrite 유지 확인.
- 다른 branch 비변경 확인:
  - STOPPING branch `:106` 여전히 `"state": "OFF"` hardcoded
  - quiescent block도 `"state": "OFF"` hardcoded 유지 (post-edit grep에서 2건 hit 중 하나)
  - `supervisor_missing` 계산, `read_runtime_status` wiring, `_supervisor_pid`/`_pid_is_alive`/`supervisor_alive` helper 전부 미편집
- `tests/test_pipeline_gui_backend.py:942`(pre-edit) `@unittest.skip` 한 줄 삭제 확인. 남은 3개 decorator는 정확히 `:1012, :1195, :1257` 위치에 있음 (기존 `:1013, :1196, :1258`에서 한 줄씩 up shift).
- grep 검증: `"state": "BROKEN"` literal 0건, 새 conditional 2건(`:128, :151`), `"state": "OFF"` 2건(`:106 STOPPING, :181 quiescent block 추정`), `SNAPSHOT_STALE_THRESHOLD|parse_iso_utc` 0건(advice 485 age machinery 도입 없음 재확인).
- 7 previously-unskipped cells(seq 486/483/480/477/474/471/468) 모두 green 유지 확인. regression 근거:
  - seq 486 `:1062` aged_ambiguous: lane state=READY → conditional else branch → "BROKEN" output → assertion pass
  - seq 483 `:865` recent_quiescent: lane state=READY → same → pass
  - seq 480 `:643` stale: lane state=READY → same → pass
  - seq 477 `:792` BROKEN-input: lane state=BROKEN → conditional `"BROKEN" != "OFF"` → else → "BROKEN" → pass
  - seq 474 `:718` STOPPING: 다른 branch(STOPPING `:106`)가 fire, 이번 slice 편집 무관
  - seq 471 `:594`, seq 468 `:1134`: supervisor alive mock 또는 no watcher/lanes라 supervisor_missing branch 모두 비발화
- seq 408/411/414/417/420/423/427/430/438/441/444/447/450/453/456/459/465/468/471/474/477/480/483/486 shipped surfaces 전부 미편집 유지.
- `.pipeline` rolling slot snapshot
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `489` — shipped, 새 `/work`로 소비. 다음 라운드는 seq 490.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `487` — seq 488 advice로 응답, stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `488` — seq 489 handoff로 변환, stale.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `462` — 지속 superseded.

## 검증
- 직접 코드/테스트 대조 (경로 + `:line`은 ## 핵심 변경 참조)
- `python3 -m unittest tests.test_pipeline_gui_backend`
  - 결과: `Ran 45 tests in 0.103s`, `OK (skipped=3)`. baseline `OK (skipped=4)` → post-edit `OK (skipped=3)`. 새 failures/errors 없음.
- `python3 -m unittest tests.test_pipeline_gui_backend.TestRuntimeStatusRead.{test_read_runtime_status_marks_recent_field_quiescent_running_status_broken_without_pids, test_read_runtime_status_converts_aged_ambiguous_snapshot_into_broken, test_read_runtime_status_marks_recent_quiescent_running_status_broken_without_supervisor, test_read_runtime_status_marks_stale_running_status_broken_when_supervisor_is_missing, test_read_runtime_status_normalizes_broken_payload_when_supervisor_is_missing}`
  - 결과: `Ran 5 tests in 0.018s`, `OK`. 신규 field_quiescent + seq 486/483/480/477 regression 전부 green.
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py` → 출력 없음, 통과.
- `-k progress_summary/coverage/claims/reinvestigation`는 `/work`가 각 11/27/7/6 OK 기록, 이번 slice가 `tests/test_smoke.py`/`core/`/`app/`/`storage/`를 건드리지 않아 baseline 유지 안전. verify 재실행 생략.
- `tests.test_web_app`, Playwright, `make e2e-test`는 범위 밖이라 의도적으로 생략.

## 남은 리스크
- **3 cells 여전히 deferred (모두 DEGRADED family)**:
  - `:1012` `recent_active_lane_without_supervisor_pid_degraded_ambiguous`
  - `:1195` `undated_ambiguous_snapshot_degraded`
  - `:1257` `watcher_only_alive_without_pid_degraded_ambiguous`
- **DEGRADED collision 미해결**: 3 DEGRADED 셀 모두 fixture가 RUNNING + supervisor_missing + `lanes[0].state == "READY"`. 이번 lane-preservation refinement는 OFF→preserve만 추가했고 READY 입력에는 여전히 "BROKEN"을 써서 DEGRADED 기대와 충돌. 다음 DEGRADED 슬라이스는 반드시 **RUNNING→BROKEN branch 앞에 더 narrow한 DEGRADED branch**를 삽입해 recent-active-lane/undated/watcher-only-alive 신호로 분기해야 함.
- **branch duplication still 3**: STOPPING + BROKEN + RUNNING→BROKEN + quiescent. G12 `_apply_shutdown_shape` refactor는 4번째 DEGRADED branch가 landing할 때 high-leverage pre-slice로 검토 가능.
- **다음 슬라이스 ambiguity**: 3 DEGRADED 후보 + G3 / G6-sub2 / G6-sub3 / G7 / G8 / G9 / G10 / G11 / G12가 모두 서로 다른 축, dominant current-risk reduction 부재. next control slot은 `.pipeline/operator_request.md`보다 `.pipeline/gemini_request.md`(CONTROL_SEQ 490)로 여는 편이 `/verify` README 규칙과 일치.
- **unrelated red tests**: `tests.test_web_app` residual 10 `LocalOnlyHTTPServer` PermissionError 그대로.
- **docs round count**: 오늘(2026-04-20) docs-only round count 0 유지. same-family docs-only 3회 이상 반복 조건 해당 없음.
- **dirty worktree**: broad unrelated dirty files 그대로. 이번 라운드는 targeted 2 files 외 변경 없음.
