# 2026-04-18 PaneLease owner_pid_path wiring hardening

## 변경 파일

### 이번 라운드 직접 편집 파일
- `watcher_core.py` — `PaneLease._owner_dead` 보수적 판정 + WatcherCore init에서 `owner_pid_path`를 무조건 `base_dir/supervisor.pid`로 wire
- `tests/test_watcher_core.py` — 새 `PaneLeaseOwnerPidWiringTest` 클래스 5개 테스트 추가
- `.pipeline/README.md` — `PaneLease.owner_pid_path` wiring contract 한 줄 추가 (line 93)

### 현재 `git diff HEAD`에 함께 보이는 별도 round 파일
- `pipeline_runtime/schema.py`, `verify_fsm.py`, `tests/test_pipeline_runtime_schema.py`의 path-ownership 관련 대형 변경 — `work/4/18/2026-04-18-path-enforced-state-ownership-round1.md` 라운드 산출물
- `pipeline_runtime/supervisor.py`와 `tests/test_pipeline_runtime_supervisor.py`의 liveness rank + STOPPED surface 변경 — `work/4/18/2026-04-18-active-round-live-verify-preference.md` 및 `work/4/18/2026-04-18-stopped-runtime-receipt-pending-visibility.md` 산출물
- `.pipeline/README.md`의 path-ownership 및 STOPPED/RECEIPT_PENDING 단락 — 위 두 라운드 산출물
- `tests/test_watcher_core.py`의 `state/jobs/` glob 두 줄 변경 — path-ownership 라운드 산출물
- 나머지 `controller/*`, `core/*`, `docs/*`, `e2e/*`, `README.md`, `app/web.py`, `tests/test_controller_server.py`, `tests/test_smoke.py`, `tests/test_web_app.py`, `verify/4/9/*` 등은 이번 세션 시작 전부터 누적된 dirty worktree이며 이번 라운드와 무관

## 사용 skill
- `superpowers:systematic-debugging`: 사용자 증상이 모호해서 Phase 1(증거 수집)을 Explore 서브에이전트로 먼저 실행하고, 단일 가설을 명시한 뒤 minimal fix로 좁혔습니다. 추측 수정을 피하기 위한 핵심 discipline이었습니다.
- `work-log-closeout`: `/work` closeout 형식과 실제 사실 항목을 current repo 규칙에 맞춰 정리하기 위해 사용했습니다.

## 변경 이유
- 사용자 증상: "watcher_core 실행 시 제대로 진행되지 않거나 꼬이는 경우가 있음".
- Explore 서브에이전트가 `/work` + `/verify` + 코드 surface를 thorough 조사해 incident family 5개를 ranking. 사용자가 top 1 (비정상 supervisor 종료 시 lease 미해제)을 선택.
- 코드 증거를 다시 읽으면서 실제 entry point를 좁힘: `PaneLease` 자체 `_owner_dead` 로직은 구현돼 있지만, [watcher_core.py:1349-1356](watcher_core.py#L1349-L1356)의 init에서 `owner_pid_path`를 `supervisor.pid` **파일 존재 여부 체크**로 조건부 wire하고 있었습니다. watcher가 supervisor보다 먼저 뜨거나 standalone으로 실행되면 `owner_pid_path=None`으로 영구 고정되어, 이후 supervisor가 떠서 죽어도 owner-death 감지가 영원히 꺼집니다. 결과적으로 stale `slot_verify` lease가 TTL(기본 900초) 만기 전까지 절대 해제되지 않아 pending Claude handoff가 "안 잡히는" 증상이 됩니다.
- 동시에 기존 `_owner_dead` 구현은 `FileNotFoundError`를 "dead"로 해석했습니다. `owner_pid_path`를 항상 wire로 바꾸면, 이 해석 때문에 `supervisor.pid`가 없는 정상 standalone 경로에서 매 check마다 lease가 즉시 clear되어 `is_active`가 영구 False가 되는 **새로운 회귀**가 발생합니다. 같은 라운드 안에서 두 문제를 일관성 있게 닫아야 했습니다.

## 핵심 변경
- `watcher_core.py::PaneLease._owner_dead` 보수적 판정으로 정리했습니다:
  - `owner_pid_path is None` → 감시 대상 없음 → `False` (기존 그대로).
  - `FileNotFoundError` → supervisor가 아직/이미 없음 == standalone 또는 정리 후 상태 → `False` (기존: `True` → 수정).
  - 빈 파일 내용 → supervisor 쓰기 중 가능 → `False` (기존: `True` → 수정).
  - 손상된 pid 내용 → 보수적 `False` (기존: `True` → 수정).
  - valid pid인데 `os.kill(pid, 0)`이 `ProcessLookupError` → `True` (기존 그대로). 이 케이스만 stale lock 정리를 유발합니다.
- `watcher_core.py::WatcherCore.__init__` 내 `PaneLease` 생성 시 `owner_pid_path=self.base_dir / "supervisor.pid"`를 무조건 전달합니다. init 시점의 파일 존재 여부 체크는 제거했습니다. `_owner_dead`가 매 check마다 파일을 다시 읽고 보수적으로 판단하므로, 이후 supervisor가 나타나고/사라지는 lifecycle 전체에서 owner-death 감지가 유효하게 유지됩니다.
- `tests/test_watcher_core.py`에 `PaneLeaseOwnerPidWiringTest` 클래스 추가. 다섯 개 회귀를 고정했습니다:
  - `test_watchercore_wires_owner_pid_path_even_when_supervisor_pid_missing` — WatcherCore init에서 `supervisor.pid` 없어도 `owner_pid_path`가 항상 wire됨을 확인.
  - `test_owner_dead_returns_false_when_supervisor_pid_missing` — standalone 경로에서 lease가 즉시 clear되지 않음을 확인.
  - `test_owner_dead_returns_false_when_supervisor_pid_empty_or_invalid` — 쓰기 중/손상된 pid를 dead로 잘못 확정하지 않음을 확인.
  - `test_owner_dead_returns_true_when_supervisor_pid_no_longer_exists_as_process` — valid pid가 process 사라졌을 때만 dead로 판정하고 stale lock이 즉시 clear됨을 확인.
  - `test_owner_pid_appearing_after_watcher_start_still_detects_dead_owner` — **핵심 start-up race 시나리오**: watcher가 먼저 뜨고 나중에 supervisor가 떠서 죽는 흐름에서도 owner-death 감지가 유효함을 확인.
- `.pipeline/README.md`에 `PaneLease.owner_pid_path` wiring contract 한 줄 추가. init 시점 파일 체크로 None 고정하지 말 것, "pid 파일 없음"은 dead가 아닐 것, `signal 0` 응답 없는 valid pid만 dead로 판정할 것을 명시.

## 슬라이스 경계
- 범위 안: `PaneLease` owner_pid_path wiring 및 `_owner_dead` 보수적 판정. 회귀 테스트. 문서 한 줄.
- 범위 밖 (건드리지 않음):
  - `pipeline_runtime/supervisor.py`의 `finally`/shutdown 경로 — 별도 follow-up 슬라이스가 맞습니다.
  - `verify_fsm.py`의 deadline 로직.
  - `watcher_core._poll` 구조.
  - incident family #2~#5 (control_seq drift, claude idle timeout false negative, artifact hash rebaseline, dispatch defer reason codes).
  - `/work/4/16/*`의 열린 남은 리스크(half-broken payload, pid 비어있는 recent snapshot 등).

## 검증
- `python3 -m py_compile watcher_core.py tests/test_watcher_core.py`
  - 결과: 통과
- `python3 -m unittest tests.test_watcher_core.PaneLeaseOwnerPidWiringTest -v`
  - 결과: `Ran 5 tests`, `OK` (새 클래스 5개 모두 통과)
- `python3 -m unittest -v tests.test_watcher_core.PaneLeaseOwnerPidWiringTest tests.test_watcher_core.ClaudeHandoffDispatchTest tests.test_watcher_core.VerifyCompletionContractTest`
  - 결과: `Ran 24 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core` (전체)
  - 결과: `Ran 119 tests`, `OK`. 이번 변경으로 새로 깨진 테스트는 없습니다.
- `git diff --check -- watcher_core.py tests/test_watcher_core.py .pipeline/README.md`
  - 결과: 통과
- `tests.test_pipeline_runtime_supervisor` 전체는 이번 라운드 범위 밖이지만 path-ownership 라운드 closeout에서 이미 확인한 baseline failure(6 failures, 1 error resolved by prior stopped-runtime round)와 동일합니다. 이번 변경으로 새로 깨진 supervisor 테스트는 없습니다.

## 남은 리스크
- **Supervisor finally 경로**: 이번 라운드는 watcher-side의 owner-death 감지만 복구했습니다. supervisor가 SIGKILL처럼 `finally`에 도달 못 하는 경로에서 supervisor.pid 파일 정리 책임은 여전히 미정의입니다. Explore 서브에이전트가 지적한 `/work/4/16/controller-graceful-stop-flush-and-contract-audit.md` L59의 남은 리스크는 이 후속 슬라이스에서 닫혀야 합니다.
- **Start-up race 실제 tmux replay 부재**: 이번 라운드는 unit 범위에서 race scenario를 단위 test로만 고정했습니다. 실제 launcher/supervisor/watcher tmux bring-up 순서에서 owner-death 감지가 정상 동작하는지는 다음 stability gate에서 추가 확인이 안전합니다.
- **Incident family #2~#5 잔여**: control_seq drift, claude idle timeout false negative, artifact hash rebaseline, dispatch defer reason codes는 같은 "꼬임" 증상을 공유할 수 있습니다. 사용자 증상이 이번 수정 후에도 재발하면 family #2(control_seq drift, `watcher_dispatch.flush_pending`) 가 evidence 기준 다음 후보입니다.
- **`PaneLease` 구조적 smell**: `PaneLease`와 supervisor 사이 "death callback" 경계는 여전히 없습니다. 현재는 lazy check (`_owner_dead`가 필요할 때마다 파일 읽음) 에 의존합니다. 큰 재설계는 4축 bundle 구조 라운드(`project_state_owner_boundary_bundle` memory 참고)의 일부로 다뤄야 합니다.
