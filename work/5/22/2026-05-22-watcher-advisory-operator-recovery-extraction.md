# 2026-05-22 watcher advisory operator recovery extraction

## 변경 파일
- `watcher_core.py`
- `watcher_recovery.py`
- `tests/test_watcher_recovery.py`
- `work/5/22/2026-05-22-watcher-advisory-operator-recovery-extraction.md`

## 사용 skill
- `security-gate`: operator/advisory recovery runtime control 경계를 건드리므로 승인, 기록, 되돌림 경계를 점검했습니다.
- `finalize-lite`: 실행한 검증, 문서 동기화 필요 여부, 남은 리스크를 구현 라운드 종료 전에 정리했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 검증, 남은 리스크를 한국어 `/work` closeout으로 기록했습니다.

## 변경 이유
- CONTROL_SEQ 2154의 A3 Step 8 지시에 따라 `watcher_core.py`에 남아 있던 stale advisory recovery cluster와 operator retriage/recovery marker cluster를 별도 모듈로 분리해야 했습니다.
- runtime control 회복 로직의 상태값과 분기 본문을 `WatcherCore` 밖으로 옮겨 core 본문을 줄이고, 같은 public wrapper 이름은 유지해야 했습니다.

## 핵심 변경
- 새 `watcher_recovery.py`에 `StaleAdvisoryRecovery`와 `OperatorRetrageTracker`를 추가했습니다. 올바른 철자 import를 위한 `OperatorRetriageTracker` alias도 함께 내보냈습니다.
- `WatcherCore.__init__`의 advisory retry/recovery 상태와 operator retriage/recovery 상태를 새 객체가 소유하도록 이동했습니다.
- `WatcherCore`의 `_retry_advisory_if_idle()`, `_recover_stale_advisory()`, `_route_operator_recovery()` 등 기존 호출 표면은 얇은 delegation wrapper로 유지했습니다.
- 기존 테스트가 직접 접근하는 operator retriage 내부 필드는 tracker proxy property로 유지했습니다.
- `tests/test_watcher_recovery.py`를 추가해 stale advisory 반복 회복, request supersede, operator idle retriage, operator recovery 중복 억제를 fake callable 기반으로 검증했습니다.
- `watcher_core.py`는 4130줄에서 3858줄로 줄었습니다. diff 기준으로 418줄을 삭제하고 146줄을 추가해 net -272줄입니다. callback injection과 기존 내부 필드 호환 property 때문에 net 감소 폭은 본문 삭제량보다 작습니다.

## 검증
- 통과: `python3 -m py_compile watcher_core.py watcher_recovery.py tests/test_watcher_recovery.py`
- 통과: `python3 -m unittest tests.test_watcher_recovery -v`
  - 결과: 4 tests OK
- 초기 실패 후 수정: `python3 -m unittest tests.test_watcher_core -v`
  - 초기 결과: 5 failures. 새 tracker가 초기 bound callback을 보관해 `mock.patch.object(core, "_notify_verify_control_recovery")`가 반영되지 않았습니다.
  - 수정: callback을 런타임 조회 lambda로 바꿔 기존 patch/호출 계약을 복구했습니다.
- 통과: 실패했던 5개 focused watcher_core 테스트 재실행
- 통과: `python3 -m unittest tests.test_watcher_core -v`
  - 결과: 266 tests OK
- 통과: `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_pipeline_runtime_supervisor tests.test_watcher_core tests.test_watcher_status_writer tests.test_watcher_lane_status tests.test_watcher_recovery 2>&1 | tail -5`
  - 결과: 560 tests OK
- 통과: `git diff --check -- watcher_core.py watcher_recovery.py tests/test_watcher_recovery.py work/5/22/2026-05-22-watcher-advisory-operator-recovery-extraction.md`
  - 결과: PASS, 출력 없음

## 남은 리스크
- 브라우저/E2E는 실행하지 않았습니다. 이번 변경은 watcher runtime recovery 내부 리팩터링이고 handoff 검증 범위가 Python compile/unit으로 지정되어 있어 제외했습니다.
- 제품 문서 변경은 하지 않았습니다. shipped behavior, 승인 정책, operator stop 정책, control slot 형식은 바꾸지 않은 내부 추출입니다.
- `watcher_recovery.py`의 새 객체는 `WatcherCore` callback을 주입받습니다. callback wiring이 넓지만 기존 테스트에서 patch 가능한 동적 조회 방식으로 보존했습니다.
- 작업 중 `.pipeline/config/agent_profile.json`, `report/gemini/2026-05-22-*.md`, `verify/5/23/`에 기존 또는 외부 dirty state가 있었습니다. 이번 라운드에서는 handoff 대상 외 파일을 수정하지 않았습니다.
