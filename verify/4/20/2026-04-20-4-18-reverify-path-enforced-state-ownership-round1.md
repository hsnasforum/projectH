# 2026-04-20 4-18 path-enforced state ownership round1 reverify

## 변경 파일
- `verify/4/20/2026-04-20-4-18-reverify-path-enforced-state-ownership-round1.md` (본 파일)

## 사용 skill
- `round-handoff`: 오늘(2026-04-20) 세션에서 **다섯 번째** 연속으로 dispatcher가 stale 이전 날짜 WORK/VERIFY pair를 가리켰고, 직전 seq 520 operator_request에 기록한 "4/18 WORK timestamp 역순 진행" 가설이 empirically 확인됐습니다. 이번 라운드 WORK=`work/4/18/2026-04-18-path-enforced-state-ownership-round1.md`(4/18 16:42 — 앞 4 round의 17:12 → 17:04 → 16:58에서 한 단계 더 뒤), VERIFY=`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`(5번째 연속 같은 manual-cleanup verify 재지정). 4/18 `/work` 주장이 current tree에서 유지되는지 narrow rerun으로 재확인하고, 5회 누적 + 가설 검증 사실을 seq 521 operator_request에 반영합니다.

## 변경 이유
- 직전 seq 520 operator_request는 4/18 WORK timestamp가 역순(17:12 → 17:04 → 16:58)으로 진행하는 구조적 hint를 명시하고, 다음 round가 16:58보다 이른 4/18 `/work`를 가리킬 가능성을 예측했습니다. 이번 round가 16:42의 `path-enforced-state-ownership-round1` `/work`를 가리킨 것은 그 예측을 정확히 empirical validation한 결과입니다.
- dispatcher repoint 누적:
  - Round N-4 (seq 516 → seq 517): 4/19 controller-fetch-failure-dedupe pair.
  - Round N-3 (seq 517 → seq 518): 4/18 17:12 pane-lease-owner-pid-wiring + manual-cleanup verify (1st reuse).
  - Round N-2 (seq 518 → seq 519): 4/18 17:04 watcher-supervisor-owner-death-lease-release + manual-cleanup verify (2nd reuse).
  - Round N-1 (seq 519 → seq 520): 4/18 16:58 matching-verify-receipt-selection + manual-cleanup verify (3rd reuse).
  - Round N (이번, seq 520 → seq 521): 4/18 16:42 path-enforced-state-ownership-round1 + manual-cleanup verify (4th reuse).
- manual-cleanup verify note 재지정 4회 연속 + 4/18 WORK timestamp 역순 진행(17:12 → 17:04 → 16:58 → 16:42) 4회 연속 = 가설 확정급 증거. CLAUDE.md Recursive Improvement 원칙 하에서 dispatcher owner boundary 식별/수정은 더 이상 후순위가 아닙니다.
- `/verify` README 규칙에 따라 seq 521 operator_request 쓰기 전에 이 verify note를 먼저 남깁니다.
- 4/18 `path-enforced-state-ownership-round1`은 오늘 처음 다루는 축이므로 narrow rerun으로 직접 확인해 둡니다.

## 핵심 변경
- **4/18 `path-enforced-state-ownership-round1` 주장이 current tree에서 유지됨**:
  - `pipeline_runtime/schema.py`:
    - `:48 JOB_STATE_DIR_NAME: str = "jobs"` 상수 존재.
    - `:51 def jobs_state_dir(state_dir: Path) -> Path:` helper 존재. `:57` `return state_dir / JOB_STATE_DIR_NAME`.
    - `:60 def iter_job_state_paths(state_dir: Path) -> list[Path]:` helper 존재. primary `<state_dir>/jobs/*.json` + root fallback(`STATE_DIR_SHARED_FILES` 제외) 구조 유지.
    - `:491 def load_job_states(...)` 유지, `iter_job_state_paths` 통해 스캔.
    - 4/18 `/work` 주장 그대로.
  - `watcher_core.py`:
    - `:67 iter_job_state_paths` import 유지.
    - `:1641 for path in iter_job_state_paths(self.state_dir):` (`_archive_stale_job_states` 경로 추정) 유지.
    - `:2020 for path in iter_job_state_paths(self.state_dir):` (`_verified_work_paths` 경로 추정) 유지.
    - `:2614 seen_job_ids: set[str] = set()` + `:2615 for path in iter_job_state_paths(...)` + `:2616-2618` dedupe 가드(`seen_job_ids`) 유지. `_get_current_run_jobs`에 primary/fallback 중복 yield 방지 가드가 명시적으로 들어가 있음.
  - `verify_fsm.py`:
    - `:13 from pipeline_runtime.schema import jobs_state_dir, read_json` import 유지.
    - `:99 def save(self, state_dir: Path) -> None:` → `:103 primary_dir = jobs_state_dir(state_dir)` 경로 유지.
    - `:113 def load(cls, state_dir: Path, job_id: str) -> Optional["JobState"]:` → `:114 primary_path = jobs_state_dir(state_dir) / f"{job_id}.json"` 유지. primary → root fallback 순서 그대로.
  - `tests/test_pipeline_runtime_schema.py`:
    - `:170 class PathEnforcedJobStateOwnershipTest(unittest.TestCase):` 존재. 7 test methods 모두 유지:
      - `test_jobs_state_dir_is_primary_subdirectory`
      - `test_iter_job_state_paths_prefers_primary_over_root_fallback`
      - `test_iter_job_state_paths_skips_shared_files_in_root_fallback`
      - `test_iter_job_state_paths_handles_missing_primary_gracefully`
      - `test_load_job_states_merges_primary_and_fallback_and_prefers_primary`
      - `test_job_state_save_writes_to_primary_jobs_subdirectory`
      - `test_job_state_load_reads_primary_first_then_root_fallback`
    - 4/18 `/work`가 기록한 "7 tests 추가" 주장과 정확히 일치.
- **supervisor 스위트의 pre-existing 6 failure**: 4/18 `/work`가 이미 baseline으로 명시적으로 기록. 이번 라운드도 그 축을 편집하지 않음. 추가 재실행 불필요.
- **sibling 4/18 manual-cleanup verify note는 축 다름**: 5번째 연속 같은 note 재지정. 이번 path-enforced state ownership round와 직접 겹치지 않음.
- **Dispatcher repoint structural hypothesis empirically validated**:
  - 가설 1(seq 519에서 제기 → seq 520에서 구체화): VERIFY 쪽은 같은 manual-cleanup verify note에 고정. Round N 기준 4/5 round 중 4회 연속 재지정(총 5 round 중 4 round가 같은 note). 가설 재확인.
  - 가설 2(seq 520에서 제기): 4/18 WORK timestamp 역순 진행(17:12 → 17:04 → 16:58). 다음 round가 16:58보다 이른 4/18 `/work`를 가리킬 것이라는 예측. 이번 round는 정확히 16:42의 `path-enforced-state-ownership-round1`를 가리킴 → 예측 empirical validation.
  - 구조적 해석: dispatcher가 4/18 `work/` 디렉터리를 역시간순(newest-first에 대한 반대) 혹은 reverse-sorted lexical로 walk하면서 "이미 처리된" 항목을 거르지 않는 bug 패턴 유력. VERIFY 쪽은 아예 single-path lock-in(특정 manual-cleanup verify file path가 dispatcher state에 고정).
  - verify lane 직접 수정 범위 밖이므로 seq 521 operator_request에서 operator에게 **validated hypothesis**로 승격. 후속 round에서도 16:42보다 이른 4/18 `/work`(16:23 `active-round-live-verify-preference`, 16:31 `stopped-runtime-receipt-pending-visibility` 등)를 가리킬 가능성이 높다고 예측합니다.
- **seq 520 operator_request는 여전히 최신 valid control**:
  - STATUS `needs_operator`, CONTROL_SEQ 520, REASON_CODE `waiting_next_control`, OPERATOR_POLICY `internal_only`, DECISION_CLASS `next_slice_selection`. operator 응답 전까지 어떤 implement-lane handoff도 열 truthful 근거가 없습니다.
  - seq 521은 4회 누적 pattern → **5회 + 가설 검증**으로 escalate.
- **`.pipeline` rolling slot snapshot (이번 verify 시점)**:
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `513` — 소비됨.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `514` — stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `515` — 소비됨.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `520` — 이번 round에서 seq 521로 supersede 대상.

## 검증
- `python3 -m unittest tests.test_pipeline_runtime_schema.PathEnforcedJobStateOwnershipTest -v`
  - 결과: `Ran 7 tests in 0.020s`, `OK`. 7개 모두 `ok`. 4/18 `/work`가 기록한 "이번 라운드가 추가한 테스트는 총 7개입니다" 주장과 정확히 일치.
- `git diff --check -- pipeline_runtime/schema.py watcher_core.py verify_fsm.py tests/test_pipeline_runtime_schema.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 출력 없음, exit code 0.
- narrow code/path 재확인
  - `rg -n 'JOB_STATE_DIR_NAME|def jobs_state_dir|def iter_job_state_paths|def load_job_states' pipeline_runtime/schema.py`: `:48 const`, `:51 jobs_state_dir def`, `:57 return`, `:60 iter_job_state_paths def`, `:491 load_job_states def`.
  - `rg -n 'jobs_state_dir|iter_job_state_paths|seen_job_ids' watcher_core.py`: `:67 import`, `:1641 scan`, `:2020 scan`, `:2614 seen_job_ids`, `:2615 scan`, `:2616/2618 dedupe`.
  - `rg -n 'jobs_state_dir|def save|def load' verify_fsm.py`: `:13 import`, `:99 save`, `:103 primary_dir`, `:113 load`, `:114 primary_path`.
  - `rg -n 'PathEnforcedJobStateOwnershipTest|class .*State.*Test' tests/test_pipeline_runtime_schema.py`: `:102 LoadJobStatesSharedFilesTest`, `:170 PathEnforcedJobStateOwnershipTest`.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - `tests.test_pipeline_runtime_schema` 전체(현 17 tests): `PathEnforcedJobStateOwnershipTest` 7건이 focused rerun에 포함, 나머지 10건은 이번 축 밖. 같은 날 이미 직전 라운드에서 `LatestVerifyNoteForWorkTest` 6건 확인.
  - `tests.test_watcher_core` 전체(111/112/138+): 오늘 이미 `PaneLeaseOwnerPidWiringTest = 7/OK` + `ClaudeHandoffDispatchTest` 3건 `OK` + `WorkNoteFilteringTest` 3건 `OK` 확인. watcher_core 자체 미편집.
  - `tests.test_pipeline_runtime_supervisor` 전체(68 tests / 6 baseline failures): 4/18 `/work`가 이 failure set을 pre-existing baseline으로 명시적으로 기록했고 이번 라운드는 supervisor 경계를 편집하지 않음. 재실행은 새 신호를 주지 않음.
  - Playwright / `make e2e-test`: browser-visible contract 변경 없음.
  - `tests.test_operator_request_schema`: 직전 round에서 `Ran 6 / OK (skipped=0)` 확인. 이번 seq 521은 canonical literal을 그대로 두고 BASED_ON_VERIFY + 5회/가설검증 맥락만 갱신하므로 재실행 불필요.

## 남은 리스크
- **Dispatcher repoint 5회 연속 + structural hypothesis empirically validated**:
  - VERIFY single-path lock-in: 같은 manual-cleanup verify note 재지정 4/5 round(실질 4회 연속 reuse, seq 517 이후 모두).
  - WORK reverse-walk: 4/18 WORK timestamp 4회 연속 역순 진행(17:12 → 17:04 → 16:58 → 16:42). 다음 round가 더 이른 4/18 `/work`를 가리킬 가능성이 유력(예: 16:31 `stopped-runtime-receipt-pending-visibility`, 16:23 `active-round-live-verify-preference`).
  - 단발 noise가 아니라 재현성 높은 dispatcher state bug로 확정. Claude verify lane 직접 수정 범위 밖이라 seq 521 operator_request에서 operator 승격. 16:42를 포함해 오늘 reverified 4/18 `/work` 4건(17:12, 17:04, 16:58, 16:42)은 모두 이미 truth-closed이므로 어떤 rerun도 새 구현을 요구하지 않습니다.
- **operator decision 여전히 미결**: seq 516/517/518/519/520 모두 `next_slice_selection` waiting. 5회 누적 + 가설 empirical validation이 `FIX_DISPATCHER_REPOINT` 후보를 leading에서 한 단계 더 올립니다. 나머지 후보는 그대로(CONTINUE_G7_GATE_BLOCKING / PIVOT_G11 / PIVOT_G8_PIN / PIVOT_G3 / PIVOT_OTHER / ACKNOWLEDGE_INFORMATIONAL / DROP_G7_OPTION_B).
- **4/18 path-enforced round 자체의 잔여 리스크**: 4/18 `/work`가 기록한 것(auto-move 미포함; archive asymmetry; supervisor pre-existing 6 failure family; tmux live replay 부재; 세션 동시 라운드로 인한 `git diff HEAD` 교차 기록 이슈)은 이번 reverify로 변하지 않았습니다.
- **오늘(2026-04-20) docs-only round count**: 0 유지. 이번 round는 `.pipeline/operator_request.md` control slot truth-sync refresh + `/verify` note 작성이라 docs-only micro-slice 조건에 해당하지 않음. same-family docs-only 3+ guard 발동되지 않음.
- **line drift accumulation**: `pipeline_runtime/schema.py:48/51/60/491`, `watcher_core.py:67/1641/2020/2614-2618`, `verify_fsm.py:13/99/103/113/114`, `tests/test_pipeline_runtime_schema.py:170` 등 이번 시점 기준 라인. 이후 탐색자는 심볼 기반 검색 권장.
- **Dirty worktree**: broad unrelated dirty files 그대로. 이번 round 직접 편집은 이 verify note + seq 521 operator_request supersede 두 파일.
