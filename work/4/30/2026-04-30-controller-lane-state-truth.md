# 2026-04-30 Controller lane state truth

## 변경 파일

- `controller/js/cozy.js`
- `pipeline_gui/app.py`
- `pipeline_gui/backend.py`
- `pipeline_gui/home_controller.py`
- `pipeline_gui/home_presenter.py`
- `tests/test_controller_server.py`
- `tests/test_pipeline_gui_home_presenter.py`
- `work/4/30/2026-04-30-controller-lane-state-truth.md`

## 사용 skill

- `security-gate`: 런처/컨트롤러 runtime 상태 표시 경계가 실제 실행 상태를 과장하지 않는지 점검하는 데 사용
- `release-check`: 변경 범위, 검증 범위, 문서 동기화 필요 여부를 정리하는 데 사용
- `work-log-closeout`: 구현 라운드 종료 기록 형식과 실제 검증 결과 정리에 사용

## 변경 이유

- `.pipeline/runs/20260430T013013Z-p19087/status.json` 기준 `Codex` lane은 `READY`, `note=prompt_visible`, `progress_phase=work_closeout_written`인데 `turn_state.active_lane=Codex`, `turn_state.state=IMPLEMENT_ACTIVE`가 남아 있었습니다.
- `controller/js/cozy.js`의 `effectiveLaneState()`가 `ready/idle` lane을 `activeWorkLaneName()`과 일치한다는 이유만으로 `working`으로 승격해 웹 상태창이 실제 lane 상태와 다르게 보일 수 있었습니다.
- Python 런처 GUI도 `turn_state.active_lane`만으로 `IMPLEMENT_ACTIVE`를 `Codex 실행 중`으로 번역해, lane 상태가 `READY`이고 closeout이 작성된 경우에도 작업 중처럼 읽힐 수 있었습니다.

## 핵심 변경

- `effectiveLaneState()`가 `turn_state`를 이용해 `working`을 추론하지 않고, `lanes[].state`를 화면 상태의 단일 truth로 사용하게 변경했습니다.
- Python 런처의 `describe_turn_state()` / `format_control_summary()`가 `lane_details`를 함께 받아 `READY + work_closeout_written` 상태를 `Codex 실행 중`이 아니라 `Codex work 작성 완료`로 표시하게 했습니다.
- `turn_state`는 역할/컨트롤 문맥 표시에만 쓰고 lane의 실제 작업 여부를 덮어쓰지 않도록 경계를 남겼습니다.
- `tests/test_controller_server.py`에 `effectiveLaneState()`가 `activeWorkLaneName` 기반 승격을 다시 도입하지 못하게 하는 회귀 테스트를 추가했습니다.
- `tests/test_pipeline_gui_home_presenter.py`에 `IMPLEMENT_ACTIVE`라도 lane이 `READY`이고 closeout이 있으면 `실행 중`으로 표시하지 않는 회귀 테스트를 추가했습니다.
- 서버 API, watcher, runtime status 파일 생성 로직은 수정하지 않았습니다.

## 검증

- `python3 -m unittest -v tests.test_controller_server.ControllerServerLaunchGateTests.test_cozy_agent_state_uses_lane_state_as_runtime_truth tests.test_controller_server.ControllerServerLaunchGateTests.test_controller_html_polls_runtime_api_only` — PASS
- `python3 -m py_compile pipeline_gui/backend.py pipeline_gui/home_presenter.py pipeline_gui/home_controller.py pipeline_gui/app.py` — PASS
- `python3 -m unittest -v tests.test_pipeline_gui_home_presenter.PipelineGuiHomePresenterTest.test_build_control_presentation_does_not_call_ready_implement_lane_working tests.test_pipeline_gui_home_presenter.PipelineGuiHomePresenterTest.test_build_control_presentation_prefers_recovery_verify_over_compat_operator_slot tests.test_pipeline_gui_home_controller tests.test_controller_server.ControllerServerLaunchGateTests.test_cozy_agent_state_uses_lane_state_as_runtime_truth` — PASS
- `python3 -m unittest -v tests.test_pipeline_gui_home_presenter tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_backend` — PASS, 76 tests
- `python3 -m unittest -v tests.test_controller_server` — PASS, 28 tests
- `git diff --check -- controller/js/cozy.js tests/test_controller_server.py pipeline_gui/backend.py pipeline_gui/home_presenter.py pipeline_gui/home_controller.py pipeline_gui/app.py tests/test_pipeline_gui_home_presenter.py work/4/30/2026-04-30-controller-lane-state-truth.md` — PASS

## 남은 리스크

- 이미 열린 브라우저 상태창은 기존 JS를 들고 있을 수 있으므로 새 동작 확인에는 페이지 새로고침이 필요할 수 있습니다. Python 런처 GUI는 다음 화면 갱신에서 새 label helper를 사용합니다.
- 이번 수정은 컨트롤러 화면 표시 오판 방지에 한정했고, `turn_state`가 closeout 후에도 `IMPLEMENT_ACTIVE`로 남는 watcher/runtime 전이 자체는 별도 원인으로 남아 있습니다.
- 제품 문서에는 내부 런처 표시 helper 계약까지 기술되어 있지 않아 문서 변경은 하지 않았습니다.
