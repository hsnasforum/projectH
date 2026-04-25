# 2026-04-24 런처 대형 검증 및 wrapper 안정화

## 변경 파일
- `pipeline_runtime/cli.py`
- `scripts/pipeline_runtime_gate.py`
- `tests/test_pipeline_runtime_cli.py`
- `report/pipeline_runtime/verification/2026-04-24-pipeline-runtime-synthetic-90s-soak.md`
- `report/pipeline_runtime/verification/2026-04-24-pipeline-runtime-synthetic-90s-soak.json`
- `report/pipeline_runtime/verification/2026-04-24-pipeline-runtime-synthetic-5m-soak.md`
- `report/pipeline_runtime/verification/2026-04-24-pipeline-runtime-synthetic-5m-soak.json`
- `report/pipeline_runtime/verification/2026-04-24-operator-classification-check.md`
- `work/4/24/2026-04-24-large-automation-verification.md`
- `verify/4/24/2026-04-24-large-automation-verification.md`

## 사용 skill
- `release-check`: 대형 회귀 검증 범위와 실행 결과를 release-readiness 관점으로 확인했습니다.
- `security-gate`: pipeline launcher, wrapper, tmux/runtime report 경계가 로컬-first 및 승인 기반 정책을 벗어나지 않는지 확인했습니다.
- `round-handoff`: 최신 `/work`와 `/verify` 기준으로 검증 truth와 남은 control-slot 의미를 분리했습니다.
- `work-log-closeout`: 변경 파일, 실행한 검증, 남은 리스크를 한국어 `/work` closeout으로 기록했습니다.

## 변경 이유
- synthetic launcher soak에서 Claude lane 출력이 task hint보다 먼저 도착하거나, ready prompt가 trailing newline 없이 남는 경우 wrapper receipt가 늦거나 닫히지 않을 수 있는 경계가 있었습니다.
- 완전 자동화 목표에서는 이런 작은 receipt/ready 판정 흔들림이 중복 dispatch, verify 대기, 불필요한 operator stop으로 번질 수 있으므로 wrapper 쪽 shared lane-surface 판정을 보강했습니다.
- synthetic soak가 fake Claude busy 상태를 충분히 관측할 수 있도록 synthetic lane delay를 조정해 런처 안정성 gate가 실제 위험 신호를 놓치지 않게 했습니다.

## 핵심 변경
- `_WrapperEmitter`가 newline으로 확정된 최근 줄뿐 아니라 `partial` prompt 조각도 평가해 `Claude Code\n❯ `처럼 줄바꿈 없이 끝난 ready prompt를 `TASK_DONE`으로 닫을 수 있게 했습니다.
- wrapper의 busy 판정은 전체 scrollback 문자열 검색 대신 shared `tail_has_busy_indicator()`를 사용해 과거 busy 로그가 현재 ready prompt를 가리지 않게 했습니다.
- task hint가 늦게 들어와도 현재 tail이 busy 상태이면 `TASK_ACCEPTED`를 발행하도록 해 출력 선행/힌트 후행 순서를 안정화했습니다.
- synthetic gate의 fake Claude delay를 `0.2s`에서 `8.0s`로 늘려 supervisor/wrapper handshake 중 busy 상태가 관측 가능한 시간 동안 유지되게 했습니다.
- 위 경계는 `tests/test_pipeline_runtime_cli.py`에 replay 테스트 3개로 고정했습니다.

## 검증
- `python3 -m unittest tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_ready_prompt_without_trailing_newline_allows_task_done tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_ready_prompt_after_busy_tail_allows_task_done tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_visible_busy_tail_emits_task_accepted_when_task_hint_arrives_after_output tests.test_pipeline_runtime_cli.WrapperEmitterTest.test_task_accept_waits_for_settle_before_done`
  - 통과: `OK`
- `python3 -m unittest tests.test_pipeline_runtime_cli tests.test_watcher_core tests.test_pipeline_runtime_gate tests.test_pipeline_runtime_fake_lane tests.test_pipeline_gui_app tests.test_web_app`
  - 통과: `Ran 640 tests in 295.354s`, `OK`
- `python3 -m unittest discover -s tests -p 'test_*.py'`
  - 통과: `Ran 1778 tests in 279.784s`, `OK (skipped=1)`
- `make e2e-test`
  - 통과: `143 passed (5.9m)`
- `python3 scripts/pipeline_runtime_gate.py synthetic-soak --duration-sec 90 --sample-interval-sec 5 --ready-timeout-sec 60 --min-receipts 1 --report report/pipeline_runtime/verification/2026-04-24-pipeline-runtime-synthetic-90s-soak.md`
  - 통과: `ready_ok=True`, `samples=17`, `state_counts={"RUNNING":17}`, `receipt_count=1`, `duplicate_dispatch_count=0`, `control_mismatch_samples=0`, `broken_seen=False`
- `python3 scripts/pipeline_runtime_gate.py synthetic-soak --duration-sec 300 --sample-interval-sec 5 --ready-timeout-sec 60 --min-receipts 1 --report report/pipeline_runtime/verification/2026-04-24-pipeline-runtime-synthetic-5m-soak.md`
  - 통과: `ready_ok=True`, `samples=57`, `state_counts={"RUNNING":57}`, `receipt_count=7`, `control_change_count=13`, `duplicate_dispatch_count=0`, `control_mismatch_samples=0`, `broken_seen=False`, `automation_health=ok`
- `python3 -m pipeline_runtime.cli status . --json`
  - 통과: `ok=true`; 현재 실제 project runtime은 `STOPPED`, `doctor` 대상 assets는 정상입니다.
- `python3 -m pipeline_runtime.cli doctor . --json`
  - 통과: `ok=true`, `summary={"fail":0,"warn":0,"ok":15}`
- `python3 scripts/pipeline_runtime_gate.py check-operator-classification --report report/pipeline_runtime/verification/2026-04-24-operator-classification-check.md`
  - 통과: `structured operator classification_source OK`
- `git diff --check`
  - 통과: 출력 없음

## 남은 리스크
- 이전에 남아 있던 `full unittest discover`와 `full browser/e2e` 검증 리스크는 이번 라운드에서 재실행 통과로 제거했습니다.
- 장시간 soak 리스크는 90초 synthetic gate와 5분 synthetic soak 통과로 크게 줄였지만, 실제 운영 세션을 밤새 유지하는 long live soak는 실행하지 않았습니다. 현재 실 project runtime이 `STOPPED`이고 `.pipeline/operator_request.md`가 남아 있어, live session을 임의로 재개해 operator/publish 경계를 흔들지 않았습니다.
- 5분 synthetic soak에서 `receipt_pending_samples=4`가 관측됐지만 최종 판정은 `DEGRADED/BROKEN` 없이 PASS였고, receipt 7건과 control change 13건이 정상 처리됐습니다. 이후 같은 계열 재발 시 `receipt_pending` 장기화만 별도 incident family로 분리하면 됩니다.
- 현재 남아 있는 `.pipeline/operator_request.md`는 런처 실패가 아니라 PR merge / M28 direction 계열의 정책 경계로 해석했습니다. 이번 라운드에서는 control slot을 새로 쓰거나 commit/push/PR 작업을 하지 않았습니다.
