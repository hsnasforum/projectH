# 2026-04-16 controller undated ambiguous hardening

## 변경 파일
- `pipeline_gui/backend.py`
- `tests/test_pipeline_gui_backend.py`
- `controller/index.html`
- `tests/test_controller_server.py`
- `README.md`
- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- `work/4/16/2026-04-16-controller-undated-ambiguous-hardening.md`

## 사용 skill
- `doc-sync`: uncertain runtime reason 확장(`supervisor_missing_snapshot_undated`)을 README/runtime docs에 맞췄습니다.
- `work-log-closeout`: 이번 라운드의 실제 변경/검증/잔여 리스크를 `/work` 형식으로 정리했습니다.

## 변경 이유
- 이전 라운드 후에도 `updated_at`이 비어 있는 ambiguous snapshot은 여전히 clean `RUNNING`처럼 남을 수 있었습니다.
- watcher가 `alive=true`만 남고 `pid`가 비어 있는 half-broken payload도 live identity 근거가 애매해, watcher claim 자체를 ambiguous activity로 더 보수적으로 다룰 필요가 있었습니다.

## 핵심 변경
- `pipeline_gui/backend.py`
  - incomplete snapshot의 uncertain family를 `supervisor_missing_recent_ambiguous`와 `supervisor_missing_snapshot_undated` 두 reason으로 확장했습니다.
  - `updated_at`이 비어 있고 supervisor도 없으며 activity claim은 남아 있지만 live identity를 증명하지 못하면 `DEGRADED(supervisor_missing_snapshot_undated)`로 정규화하도록 추가했습니다.
  - watcher `alive=true` / `pid 없음`은 더 이상 quiescent 증거로 쓰지 않고, watcher claim 자체를 ambiguous activity로 포함하도록 조정했습니다.
- `tests/test_pipeline_gui_backend.py`
  - undated ambiguous snapshot 정규화 회귀 테스트와 watcher-only alive/no-pid half-broken payload의 uncertain degradation 회귀 테스트를 추가했습니다.
  - 기존 current-run pointer fixture는 supervisor alive mocking을 명시해 새 undated fallback과 충돌하지 않도록 보정했습니다.
- `controller/index.html`
  - controller UI가 uncertain runtime reason set(`recent` + `undated`)을 함께 인식하도록 확장했습니다.
- `tests/test_controller_server.py`
  - static HTML contract에 `supervisor_missing_snapshot_undated`와 `UNCERTAIN_RUNTIME_REASONS` 존재를 고정했습니다.
- `README.md`, `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - uncertain runtime이 recent ambiguous뿐 아니라 undated ambiguous snapshot까지 포함한다는 truth를 반영했습니다.

## 검증
- `python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_controller_server`
- `python3 -m py_compile pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/server.py tests/test_controller_server.py`
- `git diff --check -- pipeline_gui/backend.py tests/test_pipeline_gui_backend.py controller/index.html tests/test_controller_server.py README.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
- 실제 HTTP smoke
  - `/tmp/projecth-controller-fixture-wMOZNM` fixture 생성
  - `PROJECT_ROOT=/tmp/projecth-controller-fixture-wMOZNM CONTROLLER_HOST=127.0.0.1 CONTROLLER_PORT=8784 python3 -m controller.server`
  - `curl -fsS http://127.0.0.1:8784/api/runtime/status`
  - `curl -fsS http://127.0.0.1:8784/controller | rg -n "supervisor_missing_snapshot_undated|UNCERTAIN_RUNTIME_REASONS|getRuntimePresentation|log-modal-info"`
  - 종료 후 `Ctrl-C`로 임시 controller 정리
- 참고:
  - `npx playwright test ...`로 browser DOM smoke도 시도했지만 local `playwright` package import 실패로 성립하지 않았습니다. 검증 완료로 계산하지 않았습니다.

## 남은 리스크
- 실제 브라우저 DOM smoke는 아직 정식으로 닫히지 않았습니다. 이번 라운드는 HTTP fixture smoke까지만 확인했습니다.
- `updated_at`, watcher, lane/control field가 모두 더 심하게 손상된 payload family는 여전히 별도 hardening 후보가 남습니다.
- 현재 환경에는 기존 `127.0.0.1:8780` controller listener가 이미 떠 있어, 이번 smoke는 충돌을 피하려고 임시 `8784`에서만 수행했습니다.
