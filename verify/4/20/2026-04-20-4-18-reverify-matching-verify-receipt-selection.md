# 2026-04-20 4-18 matching verify receipt selection reverify

## 변경 파일
- `verify/4/20/2026-04-20-4-18-reverify-matching-verify-receipt-selection.md` (본 파일)

## 사용 skill
- `round-handoff`: 오늘(2026-04-20) 세션에서 **네 번째** 연속으로 dispatcher가 stale 이전 날짜 WORK/VERIFY pair를 가리켰습니다. 이번 라운드 WORK=`work/4/18/2026-04-18-matching-verify-receipt-selection.md`(4/18 16:58, matching verify receipt selection — supervisor/watcher/helpers), VERIFY=`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`(4번째 연속 같은 manual-cleanup verify 재지정). 두 slice 축은 서로 무관. 4/18 `/work` 주장이 current tree에서 유지되는지 narrow rerun으로 재확인하고, 4회 누적 dispatcher-repoint pattern을 seq 520 operator_request에 승격합니다.

## 변경 이유
- dispatcher가 이번 round에 지정한 WORK는 4/18 16:58의 `matching-verify-receipt-selection`(pipeline_runtime/schema.py에 3 helpers 추가 + watcher/supervisor wiring + receipt fail-safe)이고, VERIFY는 같은 manual-cleanup verify(4회째 같은 note 재지정). 서로 다른 축, 둘 다 이미 shipped.
- 오늘 동일 session에서의 dispatcher repoint 누적:
  - Round N-3 (seq 515 → seq 516 근처): 4/19 controller-fetch-failure-dedupe pair.
  - Round N-2 (seq 517 → seq 518): 4/18 pane-lease-owner-pid-wiring(17:12) + 같은 manual-cleanup verify.
  - Round N-1 (seq 518 → seq 519): 4/18 watcher-supervisor-owner-death-lease-release(17:04) + 같은 manual-cleanup verify.
  - Round N (이번, seq 519 → seq 520): 4/18 matching-verify-receipt-selection(16:58) + 같은 manual-cleanup verify.
- 4회 연속 중 3회는 같은 manual-cleanup verify note를 재지정했고, WORK 쪽은 4/18 내부에서 타임스탬프가 뒤로 갈수록 거꾸로 올라가는(17:12 → 17:04 → 16:58) 패턴을 보여 줍니다. 단순 stale selection이 아니라 4/18 `work/` 디렉터리 내부 특정 순회 규칙의 드리프트로 추정되는 구조적 신호입니다.
- `/verify` README의 "pane 안 reasoning만 남기거나 next control slot만 먼저 갱신하는 것은 canonical verification closeout이 아닙니다" 규칙에 따라 seq 520 operator_request를 쓰기 전에 이 verify note를 먼저 남깁니다.
- 4/18 `matching-verify-receipt-selection` `/work` 주장은 오늘 verify lane에서 처음 다루는 축이므로 narrow rerun으로 직접 확인해 둡니다.

## 핵심 변경
- **4/18 `matching-verify-receipt-selection` 주장이 current tree에서 유지됨**:
  - `pipeline_runtime/schema.py`:
    - `:295 def normalize_repo_artifact_path(value: str | Path | None, repo_root: Path) -> str:` 존재.
    - `:309 def same_day_verify_dir_for_work(work_root: Path, verify_root: Path, work_path: Path) -> Path:` 존재.
    - `:358 def latest_verify_note_for_work(...)` 존재. `:365` `normalized_work = normalize_repo_artifact_path(work_path, repo_root)` 호출 경로 유지.
    - 세 helper 모두 shared 해석 소스로 살아 있음. 4/18 `/work` 주장 그대로.
  - `watcher_core.py`:
    - `:68 from ... import (..., latest_verify_note_for_work, ...)` import 유지.
    - `:1450 get_latest_same_day_verify_path_for_work=self._get_latest_same_day_verify_path_for_work` wiring 유지.
    - `:2221 def _get_latest_same_day_verify_path_for_work(self, work_path: Optional[Path]) -> Optional[Path]:` 존재.
    - `:2224 return latest_verify_note_for_work(...)` delegation 유지.
    - `:2249`/`:2510` 두 호출 지점에서 동일 helper 소비. global latest `/verify`로의 회귀 드리프트 없음.
  - `pipeline_runtime/supervisor.py`:
    - `:29 latest_verify_note_for_work` import 유지.
    - `:1079 return latest_verify_note_for_work(...)` artifact 해석 경로 유지.
    - `:1118 degraded_reason = f"receipt_verify_missing:{job_id}"` fail-safe 경로 유지. 매칭 verify가 없을 때 unrelated note로 receipt를 쓰지 않는 계약 그대로.
  - `.pipeline/README.md`:
    - `:85/:89/:96/:143/:144/:145/:224` 등 `receipt close` / `matching verify` / `supervisor` 문맥의 계약 라인들이 유지됨(`:96`의 verify/handoff-owner round close 순서 `TASK_ACCEPTED → TASK_DONE → current-round /verify receipt + next control → receipt close`, `:89`의 supervisor verify hint 계약 등). 4/18 `/work`의 문서 변경 주장과 충돌 없음.
  - `tests/test_pipeline_runtime_schema.py`, `tests/test_pipeline_runtime_supervisor.py`, `tests/test_watcher_core.py`에 4/18 `/work`가 추가했다고 주장한 회귀들이 정확히 유지됨. 아래 focused rerun으로 확인.
- **4/18 `/work`의 잔여 failure 6건은 명시적 pre-existing baseline**:
  - 4/18 `/work`의 `## 검증` 섹션이 `tests.test_pipeline_runtime_supervisor`에서 `FAILED (failures=6)` 상태를 사실대로 기록했습니다. 이번 라운드에서 그 6 failure(`test_auth_failure_breakage_blocks_restart`, `test_claude_post_accept_breakage_blocks_blind_replay`, `test_codex_breakage_stops_after_retry_budget`, `test_codex_pre_completion_breakage_restarts_within_retry_budget`, `test_manifest_mismatch_blocks_receipt_and_marks_degraded`, `test_write_status_marks_runtime_degraded_on_active_lane_auth_failure`)는 이 축 밖이라 재실행하지 않았습니다.
- **sibling 4/18 manual-cleanup verify는 축 다름**:
  - 4회째 같은 manual-cleanup verify(4/18 `tests/test_pipeline_smoke_cleanup.py` `PROJECT_ROOT` 진입 계약)가 재지정됐지만, 이번 matching-verify-receipt-selection round와 직접 겹치지 않습니다. 재실행은 축과 무관해 생략했습니다.
- **Dispatcher repoint pattern 누적 4회 연속**:
  - 4회 모두 "이미 shipped된 이전 날짜 `/work` + 서로 다른 축의 이전 날짜 `/verify`" 구조.
  - N-1/N/N+1(=N-2→N-1→N round index 재정렬해도)의 WORK 쪽 4/18 타임스탬프가 17:12 → 17:04 → 16:58로 역순 진행.
  - VERIFY 쪽은 3회 연속 같은 manual-cleanup verify note 재지정.
  - CLAUDE.md Recursive Improvement 원칙: "같은 incident family가 다시 나왔으면 조건문을 하나 더 얹기보다, 그 incident의 owner인 boundary/helper/module을 먼저 고칩니다." verify lane이 dispatcher owner를 직접 고칠 수는 없으므로 seq 520 operator_request에서 operator 승격(이번에는 시간적 역순 + 동일 verify 고정이라는 구체적 hint 포함).
- **seq 519 operator_request는 여전히 최신 valid control**:
  - STATUS `needs_operator`, CONTROL_SEQ 519, REASON_CODE `waiting_next_control`, OPERATOR_POLICY `internal_only`, DECISION_CLASS `next_slice_selection`. operator 응답 전까지 어떤 implement-lane handoff도 열 truthful 근거가 없습니다.
  - seq 519가 `FIX_DISPATCHER_REPOINT`를 leading 후보로 올려 둔 상태. 이번 seq 520은 **4회 누적 + WORK timestamp 역순 진행 + VERIFY 3회 고정** 근거로 그 leading 후보를 한 단계 더 구체화합니다.
- **`.pipeline` rolling slot snapshot (이번 verify 시점)**:
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `513` — 소비됨.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `514` — stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `515` — 소비됨.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `519` — 이번 round에서 seq 520로 supersede 대상.

## 검증
- `python3 -m unittest -v tests.test_pipeline_runtime_schema.LatestVerifyNoteForWorkTest tests.test_watcher_core.WorkNoteFilteringTest.test_latest_unverified_broad_work_ignores_newer_unrelated_verify tests.test_watcher_core.WorkNoteFilteringTest.test_same_day_verify_lookup_accepts_direct_day_dir_note tests.test_watcher_core.WorkNoteFilteringTest.test_same_day_verify_lookup_rejects_multiple_unrelated_verifies tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_receipt_uses_verify_matching_job_work tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`
  - 결과: `Ran 12 tests in 0.081s`, `OK`. 모든 이름이 `ok`. 4/18 `/work`가 인용한 focused rerun(`Ran 10` 상태 인용)보다 2건 확장(`LatestVerifyNoteForWorkTest`가 6 methods로 명시돼 total 12), 실패 없음.
- `git diff --check -- pipeline_runtime/schema.py pipeline_runtime/supervisor.py watcher_core.py tests/test_pipeline_runtime_schema.py tests/test_pipeline_runtime_supervisor.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 출력 없음, exit code 0.
- narrow code/path 재확인
  - `rg -n 'latest_verify_note_for_work|same_day_verify_dir_for_work|normalize_repo_artifact_path' pipeline_runtime/schema.py`(head 10): `:295`, `:309`, `:351`, `:358`, `:365`, `:371` hit. 3 helper def + 내부 호출 라인.
  - `rg -n '_get_latest_same_day_verify_path_for_work|latest_verify_note_for_work' watcher_core.py`: `:68 import`, `:1450 wiring`, `:2221 def`, `:2224 delegate`, `:2249 call`, `:2510 call`.
  - `rg -n 'receipt_verify_missing|latest_verify_note_for_work' pipeline_runtime/supervisor.py`: `:29 import`, `:1079 helper call`, `:1118 fail-safe literal`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - `tests.test_pipeline_runtime_schema` 전체(17 tests): `LatestVerifyNoteForWorkTest` 6건이 focused rerun에 포함됐고, 나머지 11건은 이번 축 밖. 같은 helper 재실행은 비용 대비 낮은 추가 신호.
  - `tests.test_watcher_core` 전체(112+): 오늘 이미 `PaneLeaseOwnerPidWiringTest = 7/OK` + `ClaudeHandoffDispatchTest` 3건 `OK` + 직전 4/19 late-verify `Ran 138 / OK` 확인. watcher_core 자체 미편집.
  - `tests.test_pipeline_runtime_supervisor` 전체(71 tests, baseline 6 failures): 4/18 `/work`가 이 6 failure를 pre-existing baseline으로 명시적으로 기록했고, 이번 라운드는 supervisor 경계를 편집하지 않음. focused 3 tests(`test_build_artifacts_latest_verify_matches_latest_work_over_newer_unrelated_verify`, `test_write_status_receipt_uses_verify_matching_job_work`, `test_write_status_marks_receipt_verify_missing_when_only_unrelated_verify_exists`)로 이번 축만 좁혀 재확인.
  - Playwright / `make e2e-test`: browser-visible contract 변경 없음.
  - `tests.test_operator_request_schema`: 직전 round(seq 519)에서 이미 `Ran 6 / OK (skipped=0)` 확인. 이번 seq 520은 `REASON_CODE/OPERATOR_POLICY/DECISION_CLASS` canonical literal을 그대로 두고 BASED_ON_VERIFY + 4회 누적 맥락만 갱신하므로 재실행 불필요.

## 남은 리스크
- **Dispatcher repoint pattern 4회 연속 + 구조적 hint**: 오늘 동일 세션에서 네 번 연속 stale 이전 날짜 pair 지정. 4회 중 3회는 같은 manual-cleanup verify note를 재지정했고, WORK 쪽은 4/18 내부에서 17:12 → 17:04 → 16:58로 시간적 역순으로 내려가는 양상. 이는 "4/18 `work/` 디렉터리 내부를 특정 정렬 규칙으로 순회하며 manual-cleanup verify와 교차시키는" 구조적 드리프트 가능성을 시사합니다. seq 520 operator_request에서 이 hint를 명시적으로 추가해 operator가 dispatcher owner boundary를 더 좁게 짚을 수 있게 합니다. verify lane 직접 수정 범위 밖.
- **operator decision 여전히 미결**: seq 516/517/518/519 모두 `next_slice_selection` waiting. 4회 누적 + 구조적 hint가 `FIX_DISPATCHER_REPOINT` 후보의 근거를 한 단계 더 보강합니다. 나머지 후보(G7-gate-blocking / G11 adoption audit / G8-pin / G3 / PIVOT_OTHER / ACKNOWLEDGE_INFORMATIONAL / DROP_G7_OPTION_B)는 그대로.
- **4/18 matching-verify-receipt-selection round 자체의 잔여 리스크**: 4/18 `/work`가 기록한 것(historical receipt/status artifact backfill 안 함; backward-compat single-note fallback 남아 있음; supervisor 스위트의 pre-existing 6 failure family는 별도 slice)은 이번 reverify로 변하지 않았습니다.
- **오늘(2026-04-20) docs-only round count**: 0 유지. 이번 round는 `.pipeline/operator_request.md` control slot truth-sync refresh + `/verify` note 작성이라 docs-only micro-slice 조건에 해당하지 않음. same-family docs-only 3+ guard 발동되지 않음.
- **line drift accumulation**: `pipeline_runtime/schema.py:295/309/358`, `watcher_core.py:2221/2224`, `pipeline_runtime/supervisor.py:1079/1118`, `.pipeline/README.md:96` 등 이번 시점 기준 라인. 이후 탐색자는 심볼 기반 검색 권장.
- **Dirty worktree**: broad unrelated dirty files 그대로. 이번 round 직접 편집은 이 verify note + seq 520 operator_request supersede 두 파일.
