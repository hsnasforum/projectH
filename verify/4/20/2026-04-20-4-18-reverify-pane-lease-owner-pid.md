# 2026-04-20 4-18 PaneLease owner_pid_path reverify

## 변경 파일
- `verify/4/20/2026-04-20-4-18-reverify-pane-lease-owner-pid.md` (본 파일)

## 사용 skill
- `round-handoff`: dispatcher가 오늘 두 번째 연속으로 stale 이전 날짜 pair를 WORK/VERIFY로 가리켰습니다(어제 4/19, 이번 4/18). 4/18 PaneLease owner_pid_path wiring `/work` 주장이 current tree에서 여전히 유효한지 narrow-rerun으로 재확인하고, 연속되는 dispatcher-repoint 패턴을 seq 518 operator_request에 명시적으로 반영할 준비를 했습니다.

## 변경 이유
- dispatcher가 오늘(2026-04-20) WORK=`work/4/18/2026-04-18-pane-lease-owner-pid-wiring.md`, VERIFY=`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`로 지정했습니다. 두 4/18 slice는 서로 다른 축(PaneLease owner_pid_path 보수적 wiring vs. manual cleanup script `PROJECT_ROOT` 진입 계약 고정)이라 pair mismatch이며, 둘 다 이미 shipped로 truth-closed 상태입니다.
- 오늘 이미 두 번 연속 stale 이전 날짜 pair를 dispatcher가 가리킨 셈입니다(직전 round 4/19, 이번 round 4/18). 같은 pattern이 재귀적으로 관찰된 만큼, 이번 verify note에서 이 사실을 명시적으로 기록하고 seq 518 operator_request에서 operator에게 가시화합니다.
- `/verify` README의 "pane 안 reasoning만 남기거나 next control slot만 먼저 갱신하는 것은 canonical verification closeout이 아닙니다" 규칙에 따라 seq 518 쓰기 전에 이 note를 먼저 남깁니다.

## 핵심 변경
- **4/18 `pane-lease-owner-pid-wiring` 주장이 current tree에서도 유지됨**:
  - `watcher_core.py:289` `def _owner_dead(self) -> bool:` 존재 확인.
  - `watcher_core.py:245-250` `owner_pid_path: Optional[Path] = None` 인자 + `self.owner_pid_path = owner_pid_path` 유지.
  - `watcher_core.py:1403-1412` WatcherCore `__init__`에서 `PaneLease` 생성 시 주석 블록(init 시점 파일 존재 여부 체크 없이 무조건 동일 경로로 wire)과 `owner_pid_path=self.base_dir / "supervisor.pid"` 인자 존재 확인. 4/18 `/work`가 인용한 `:1349-1356` line 인용은 라인 드리프트(~+60)일 뿐 의미 동일.
  - `.pipeline/README.md:100`에 `owner_pid_path` wiring contract 라인 유지. 4/18 `/work`의 `line 93` 인용은 minor line drift.
  - `tests/test_watcher_core.py:1694` `class PaneLeaseOwnerPidWiringTest(unittest.TestCase):` 존재. 원래 5 test(1695/1721/1748/1775/1802) 모두 유지:
    - `test_watchercore_wires_owner_pid_path_even_when_supervisor_pid_missing`
    - `test_owner_dead_returns_false_when_supervisor_pid_missing`
    - `test_owner_dead_returns_false_when_supervisor_pid_empty_or_invalid`
    - `test_owner_dead_returns_true_when_supervisor_pid_no_longer_exists_as_process`
    - `test_owner_pid_appearing_after_watcher_start_still_detects_dead_owner`
  - 이후 같은 클래스에 2 test가 추가되어 현재 총 7건(1830 `test_lease_persists_owner_pid_and_clears_after_owner_restart`, 1863 `test_legacy_lease_without_owner_pid_clears_when_supervisor_restarts`). 모두 green.
  - `python3 -m unittest tests.test_watcher_core.PaneLeaseOwnerPidWiringTest -v` → `Ran 7 tests in 0.019s`, `OK`. 4/18 `/work` baseline(5 tests/OK)에서 2 test 확장, 실패 없음. start-up race scenario와 standalone 경로 보수성 둘 다 유지.
- **4/18 sibling `manual-cleanup-keep-recent-zero-failsafe-verification` note는 축이 다름**:
  - 그 verify note는 `tests/test_pipeline_smoke_cleanup.py` 축(manual cleanup `PROJECT_ROOT` 진입 계약)의 truth-sync였고, 이번 PaneLease wiring round와는 직접 축이 다릅니다. manual-cleanup 쪽 재실행은 이번 verify 축과 무관해 생략했습니다.
- **dispatcher repoint pattern 연속 관찰**:
  - 이번 round 직전(seq 516 → seq 517) 라운드에서도 dispatcher는 4/19 mismatched pair를 가리켰고, 이번 round에는 4/18 mismatched pair입니다. 둘 다 이미 shipped, 둘 다 WORK/VERIFY가 서로 다른 slice. 같은 날 두 번 연속 같은 pattern이 reproducible하므로 operator가 dispatcher 상태를 확인하는 편이 맞다고 판단됩니다(4/19 late-verify의 `dispatcher_state_truth_sync` 선례와 동일 계열).
- **seq 517 operator_request는 여전히 최신 valid control**:
  - STATUS `needs_operator`, CONTROL_SEQ 517, REASON_CODE `waiting_next_control`, OPERATOR_POLICY `internal_only`, DECISION_CLASS `next_slice_selection`. operator 응답 전까지 어떤 implement-lane handoff도 열 truthful 근거가 없습니다.
- **`.pipeline` rolling slot snapshot**:
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `513` — 소비됨.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `514` — stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `515` — 소비됨.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `517` — 이번 round에서 seq 518로 supersede 대상(BASED_ON_VERIFY 갱신 + dispatcher-repoint 연속 관찰 기록).

## 검증
- `python3 -m unittest tests.test_watcher_core.PaneLeaseOwnerPidWiringTest -v`
  - 결과: `Ran 7 tests in 0.019s`, `OK`. 각 test 이름과 실행 순서 확인 완료. 5(원본) + 2(이후 확장) 모두 green.
- narrow code/path 확인
  - `rg -n 'owner_pid_path|_owner_dead' watcher_core.py` (head 25) → 12 hits(`:245 param`, `:250 assign`, `:257 None-guard`, `:260-261 stat/read`, `:289 _owner_dead def`, `:290 comment`, `:308 _clear_if_owner_dead`, `:335 call`, `:341 call`, `:371 call`, `:1403-1406 init comment`, `:1412 unconditional wire`). 4/18 `/work` 설명과 논리 구조 동일.
  - `rg -n 'owner_pid_path' .pipeline/README.md` → `:100` 매치(4/18 `/work`의 `line 93`에서 드리프트).
  - `awk` 스캔으로 `PaneLeaseOwnerPidWiringTest` 클래스의 test method 7건을 라인 번호와 함께 정렬 확인.
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 출력 없음, 통과.
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - `python3 -m unittest tests.test_watcher_core` 전체 138+ 스위트: 4/19 late-verify가 이미 `Ran 138 / OK` 확인했고, 이번 라운드는 watcher_core 자체를 편집하지 않았습니다. 같은 날 동일 스위트 전체 재실행은 과합니다.
  - `tests.test_pipeline_smoke_cleanup`(4/18 sibling verify가 다룬 축): 이번 축과 무관.
  - `tests.test_pipeline_runtime_supervisor` 전체: 이번 라운드가 supervisor 경계를 건드리지 않음.
  - Playwright / `make e2e-test`: browser-visible contract 변경 없음.
  - `tests.test_operator_request_schema`: 직전 round(seq 517 closeout)에서 `Ran 6 / OK (skipped=0)` 확인했고, 이번 round는 `.pipeline/operator_request.md` REASON_CODE/OPERATOR_POLICY/DECISION_CLASS literal을 바꾸지 않고 BASED_ON_VERIFY와 맥락만 갱신하므로 재실행 불필요.

## 남은 리스크
- **Dispatcher repoint pattern 연속(누적 2회)**: 오늘 같은 세션에서 두 번 연속 dispatcher가 stale 이전 날짜 pair를 WORK/VERIFY로 가리켰습니다. 단발성 noise가 아니라 reproducible signal로 판단하는 편이 안전합니다. 동일 pattern이 recursive-improvement 범주("같은 incident family가 재발하면 owner boundary를 먼저 고친다")에 해당하므로, 이번 round에서 operator_request에 명시적으로 기록해 operator가 dispatcher owner를 확인하도록 합니다. 직접 수정은 현재 verify lane 범위 밖.
- **operator decision 여전히 미결**: seq 516/517 모두 `next_slice_selection` waiting 상태. Gemini 515는 G8-pin / G11 / G3 tight pin 불가, option B(allowlist)는 seq 516 truth-sync로 low-value, gate-blocking 시기상조. 후보 집합은 그대로.
- **4/18 PaneLease wiring 자체의 잔여 리스크**: 4/18 `/work`의 `## 남은 리스크`에 기록된 supervisor finally 경로, start-up race 실제 tmux replay 부재, incident family #2~#5(control_seq drift, claude idle timeout false negative, artifact hash rebaseline, dispatch defer reason codes), PaneLease 구조적 smell은 이번 reverify로 변하지 않았고 후속 슬라이스에서 별도로 다뤄야 합니다.
- **오늘(2026-04-20) docs-only round count**: 0 유지. 이번 round는 `.pipeline/operator_request.md`(control slot truth-sync refresh) + `/verify` note 작성이라 docs-only micro-slice 조건과 무관. same-family docs-only 3+ guard에 걸리지 않습니다.
- **line drift accumulation**: `watcher_core.py:1349→1412`, `.pipeline/README.md:93→100`, `pipeline_runtime/operator_autonomy.py:168→178` 등 라인 번호 인용이 여러 `/work`/`/verify` 노트에서 드리프트되고 있습니다. 각 인용 시점에는 옳았으므로 수정은 불필요하지만, 이후 탐색자가 인용 line을 그대로 신뢰하지 않도록 함수/심볼 이름 기준 검색이 안전합니다.
- **Dirty worktree**: broad unrelated dirty files 그대로. 이번 round 직접 편집은 이 verify note + seq 518 operator_request supersede 두 파일.
