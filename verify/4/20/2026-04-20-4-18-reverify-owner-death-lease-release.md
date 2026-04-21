# 2026-04-20 4-18 watcher-supervisor owner death lease release reverify

## 변경 파일
- `verify/4/20/2026-04-20-4-18-reverify-owner-death-lease-release.md` (본 파일)

## 사용 skill
- `round-handoff`: 오늘(2026-04-20) 세션에서 **세 번째** 연속으로 dispatcher가 이전 날짜 stale WORK/VERIFY pair를 가리켰습니다. 이번 라운드 WORK=`work/4/18/2026-04-18-watcher-supervisor-owner-death-lease-release.md`(17:04), VERIFY=`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`. 둘 다 이미 shipped이고 서로 다른 축입니다. 같은 pattern이 3회 reproducible signal이 됐으므로, narrow rerun으로 4/18 PaneLease owner-death lease release 주장이 current tree에서 여전히 유효함을 재확인하고 seq 519 operator_request에 반복 pattern을 명시적으로 승격합니다.

## 변경 이유
- dispatcher가 이번 round에 지정한 WORK는 `work/4/18/2026-04-18-watcher-supervisor-owner-death-lease-release.md`(4/18 17:04, PaneLease owner_pid_path 최초 도입 round)이고, VERIFY는 `verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`(manual cleanup script `PROJECT_ROOT` 계약 truth-sync)로 완전히 다른 축입니다.
- 직전 라운드(seq 517 → seq 518)는 4/18 `2026-04-18-pane-lease-owner-pid-wiring.md`(17:12 hardening follow-up) + 같은 manual-cleanup verify pair였습니다. 이번 round는 같은 PaneLease owner_pid 가족의 **선행** `/work`(17:04)를 dispatcher가 다시 가리킨 셈입니다. 같은 날 동일 session에서 연속 3회 같은 repoint pattern이며, 그중 두 번은 같은 축(PaneLease owner_pid family)의 서로 다른 `/work`를 돌려가며 겹쳐 가리켰습니다.
- `/verify` README의 "pane 안 reasoning만 남기거나 next control slot만 먼저 갱신하는 것은 canonical verification closeout이 아닙니다" 규칙에 따라 seq 519 operator_request를 쓰기 전에 이 verify note를 먼저 남깁니다.
- 4/18 `/work`의 주장(`PaneLease.owner_pid` 추가, `os.kill(pid, 0)` 기반 stale lock 즉시 정리, 3개 focused regression green)이 current tree에서도 유지되는지는 narrow rerun으로 직접 확인해 둡니다.

## 핵심 변경
- **4/18 `watcher-supervisor-owner-death-lease-release` 주장이 current tree에서 유지됨**:
  - `watcher_core.py:245` `owner_pid_path: Optional[Path] = None` 인자 유지, `:250` `self.owner_pid_path = owner_pid_path` assign 유지.
  - `watcher_core.py:257-281` `owner_pid_path is None` guard → `stat()` → `read_text(...).strip()` → `int(pid)` → `os.kill(pid, 0)` 흐름 유지.
  - `watcher_core.py:289` `def _owner_dead(self) -> bool:` 존재, `:308` `_clear_if_owner_dead(slot)`, `:335 / :341 / :371` 세 호출 지점 모두 존재.
  - `watcher_core.py:1403-1412` WatcherCore `__init__`에서 `PaneLease(..., owner_pid_path=self.base_dir / "supervisor.pid")` 무조건 wire. 4/18 `/work`의 설명(startup 시 `.pipeline/supervisor.pid` 존재 여부와 무관하게 동일 경로로 wire) 그대로.
  - `.pipeline/README.md:101`에 "supervisor의 `finally` unlink는 정상 종료 경로에만 기대; `SIGKILL`처럼 `finally`가 실행되지 않는 종료에서는 stale `supervisor.pid`가 남을 수 있고, 살아남은 watcher의 owner-death 판정이 cleanup 책임을 맡습니다" 계약 라인 존재. 4/18 `/work`의 문서 변경 주장 유지.
  - `tests/test_watcher_core.py`:
    - `:2058 test_verify_lease_is_reclaimed_when_supervisor_pid_is_dead`
    - `:2083 test_handoff_update_waits_until_verify_lease_released`
    - `:2120 test_handoff_update_releases_when_supervisor_pid_is_dead`
    4/18 `/work`가 추가했다고 주장한 3개 regression이 정확히 유지됨. 라인은 4/18 시점 대비 약간 드리프트했지만 심볼은 동일.
- **sibling 4/18 `manual-cleanup-keep-recent-zero-failsafe-verification` verify note는 축 다름**:
  - 그 verify note는 `tests/test_pipeline_smoke_cleanup.py`(manual cleanup `PROJECT_ROOT` 진입 계약) 축이라 이번 PaneLease owner-death round와 직접 겹치지 않습니다. manual-cleanup 재실행은 이번 reverify와 무관해 생략했습니다.
- **Dispatcher repoint pattern 누적 3회 연속**:
  - Round N-2 (seq 516 → seq 517): dispatcher WORK=`work/4/19/2026-04-19-controller-fetch-failure-dedupe.md`, VERIFY=`verify/4/19/2026-04-19-operator-stop-verified-blocker-recovery-scope-late-verification.md`. 서로 다른 4/19 slice, 둘 다 shipped + truth-closed. 당시 `verify/4/20/2026-04-20-4-19-reverify-and-seq-516-effect.md`에 기록.
  - Round N-1 (seq 517 → seq 518): dispatcher WORK=`work/4/18/2026-04-18-pane-lease-owner-pid-wiring.md`(PaneLease owner_pid hardening, 17:12), VERIFY=`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`(manual cleanup 축). 당시 `verify/4/20/2026-04-20-4-18-reverify-pane-lease-owner-pid.md`에 기록. `tests.test_watcher_core.PaneLeaseOwnerPidWiringTest = Ran 7 / OK` 확인됨.
  - Round N (이번, seq 518 → seq 519): dispatcher WORK=`work/4/18/2026-04-18-watcher-supervisor-owner-death-lease-release.md`(PaneLease owner_pid 최초 도입, 17:04, 같은 가족의 선행 `/work`), VERIFY=`verify/4/18/2026-04-18-manual-cleanup-keep-recent-zero-failsafe-verification.md`(동일 manual cleanup verify 재지정). 3개 focused regression 직접 재실행 결과 `Ran 3 / OK`.
  - 3회 모두 "이미 shipped된 이전 날짜 `/work` + 다른 slice의 이전 날짜 `/verify`"라는 구조가 동일. 특히 Round N-1과 Round N은 같은 PaneLease owner_pid family 내부의 두 인접 `/work`를 돌려가며 가리키는 드리프트 양상입니다. CLAUDE.md Recursive Improvement "같은 incident family가 다시 나왔으면 조건문을 하나 더 얹기보다, 그 incident의 owner인 boundary/helper/module을 먼저 고칩니다"에 해당합니다. verify lane이 dispatcher owner를 직접 고칠 수는 없으므로, 이번 seq 519 operator_request에서 이 pattern을 단일 reproducible signal로 격상해 operator 주의를 명시적으로 요청합니다.
- **seq 518 operator_request는 여전히 최신 valid control**:
  - STATUS `needs_operator`, CONTROL_SEQ 518, REASON_CODE `waiting_next_control`, OPERATOR_POLICY `internal_only`, DECISION_CLASS `next_slice_selection`. operator 응답 전까지 어떤 implement-lane handoff도 열 truthful 근거가 없습니다.
  - seq 518은 이미 `FIX_DISPATCHER_REPOINT` 후보를 2회 pattern으로 올려 두었습니다. 이번 seq 519는 같은 후보를 **3회 누적** 근거로 갱신합니다.
- **`.pipeline` rolling slot snapshot (이번 verify 시점)**:
  - `.pipeline/claude_handoff.md`: STATUS `implement`, CONTROL_SEQ `513` — 소비됨.
  - `.pipeline/gemini_request.md`: STATUS `request_open`, CONTROL_SEQ `514` — stale.
  - `.pipeline/gemini_advice.md`: STATUS `advice_ready`, CONTROL_SEQ `515` — 소비됨.
  - `.pipeline/operator_request.md`: STATUS `needs_operator`, CONTROL_SEQ `518` — 이번 round에서 seq 519로 supersede 대상(BASED_ON_VERIFY 갱신 + dispatcher-repoint 누적 3회 기록).

## 검증
- `python3 -m unittest -v tests.test_watcher_core.ClaudeHandoffDispatchTest.test_verify_lease_is_reclaimed_when_supervisor_pid_is_dead tests.test_watcher_core.ClaudeHandoffDispatchTest.test_handoff_update_releases_when_supervisor_pid_is_dead tests.test_watcher_core.ClaudeHandoffDispatchTest.test_handoff_update_waits_until_verify_lease_released`
  - 결과: `Ran 3 tests in 0.031s`, `OK`. 세 테스트 모두 `ok`. 4/18 `/work` 검증 블록이 기록한 3개 regression과 정확히 일치.
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 출력 없음, exit code 0.
- narrow code/path 재확인
  - `rg -n 'owner_pid_path|_owner_dead|os\.kill' watcher_core.py`(head 25): `:245 arg`, `:250 assign`, `:257 None-guard`, `:260 stat`, `:261 read_text`, `:280 os.kill(pid, 0)`, `:289 _owner_dead def`, `:290 comment`, `:308 _clear_if_owner_dead`, `:335 call`, `:341 call`, `:371 call`, `:1403-1406 init comment`, `:1412 unconditional wire`. 4/18 `/work` 논리 구조 동일.
  - `rg -n 'supervisor\.pid' .pipeline/README.md`: `:101` 라인에 owner-death 판정 cleanup 책임 계약 존재.
  - `rg -n 'test_verify_lease_is_reclaimed_when_supervisor_pid_is_dead|test_handoff_update_releases_when_supervisor_pid_is_dead|test_handoff_update_waits_until_verify_lease_released' tests/test_watcher_core.py`: 3 hits(`:2058`, `:2083`, `:2120`).
- 이번 verify에서 재실행하지 않은 것과 그 이유
  - `python3 -m unittest tests.test_watcher_core` 전체 138+ 스위트: 직전 4/19 late-verify가 `Ran 138 / OK` 확인했고, 오늘 4/18 PaneLease owner_pid hardening reverify도 `PaneLeaseOwnerPidWiringTest = 7 / OK` 확인함. 이번 round는 `watcher_core.py` / `tests/test_watcher_core.py` 자체를 편집하지 않았으므로 같은 날 전체 suite 재실행은 과함.
  - `tests.test_pipeline_smoke_cleanup`(sibling 4/18 verify 축): 이번 reverify 축과 무관.
  - `tests.test_operator_request_schema`: 직전 라운드(seq 517/518)에서 이미 `Ran 6 / OK (skipped=0)` 확인. 이번 seq 519는 `REASON_CODE/OPERATOR_POLICY/DECISION_CLASS` canonical literal을 그대로 두고 BASED_ON_VERIFY + 3회 누적 맥락만 갱신하므로 재실행 불필요.
  - Playwright / `make e2e-test`: browser-visible contract 변경 없음.
  - supervisor/runtime broader suites: supervisor 경계 미편집.

## 남은 리스크
- **Dispatcher repoint pattern 3회 연속**: 오늘 동일 세션에서 세 번 연속 dispatcher가 stale 이전 날짜 pair를 가리켰고, 그중 두 번은 같은 PaneLease owner_pid family 내부의 서로 다른 `/work`를 교대로 지정했습니다. 단발 noise가 아니라 reproducible signal로 굳어졌습니다. CLAUDE.md Recursive Improvement 원칙에 따라 dispatcher owner boundary 확인이 필요합니다. verify lane 직접 수정 범위 밖이므로 seq 519 operator_request에서 operator 승격.
- **operator decision 여전히 미결**: seq 516/517/518 모두 `next_slice_selection` waiting. 오늘 3회 누적 pattern은 기존 후보에 `FIX_DISPATCHER_REPOINT`를 더 분명히 올리는 근거가 됐습니다. 나머지 후보(G7-gate-blocking / G11 adoption audit / G8-pin / G3 / PIVOT_OTHER / ACKNOWLEDGE_INFORMATIONAL / DROP_G7_OPTION_B)는 그대로.
- **4/18 watcher-supervisor owner-death round 자체의 잔여 리스크**: 4/18 `/work`가 기록한 것(supervisor 비정상 종료 runtime surface degrade/stop 승격 미구현, supervisor-managed가 아닌 수동 watcher 경로의 owner wiring 미정, 나머지 open-risk 4건 — `control_seq` drift / Claude idle timeout 오판 / verify artifact hash aliasing / generic `control_mismatch` observability 부족)은 이번 reverify로 변하지 않았습니다.
- **오늘(2026-04-20) docs-only round count**: 0 유지. 이번 round는 `.pipeline/operator_request.md` control slot truth-sync refresh + `/verify` note 작성이라 docs-only micro-slice 조건에 해당하지 않음. same-family docs-only 3+ guard 발동되지 않음.
- **line drift accumulation**: 직전 verify 기준 `watcher_core.py:1349→1412`, `.pipeline/README.md:93→100→101`, `pipeline_runtime/operator_autonomy.py:168→178` 등 누적 드리프트. 인용 line은 당시 시점에는 정확했으므로 수정 불필요하되, 이후 탐색자는 심볼 기반 검색을 권장.
- **Dirty worktree**: broad unrelated dirty files 그대로. 이번 round 직접 편집은 이 verify note + seq 519 operator_request supersede 두 파일.
