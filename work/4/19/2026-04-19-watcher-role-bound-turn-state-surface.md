# 2026-04-19 watcher role-bound turn state surface

## 변경 파일
- watcher_core.py
- pipeline_gui/backend.py
- pipeline_gui/home_controller.py
- tests/test_watcher_core.py
- tests/test_pipeline_gui_backend.py
- tests/test_pipeline_gui_home_controller.py
- .pipeline/README.md
- README.md
- docs/PRODUCT_SPEC.md
- docs/ARCHITECTURE.md
- docs/ACCEPTANCE_CRITERIA.md
- docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md
- docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md

## 사용 skill
- doc-sync: watcher가 export하는 current-turn owner metadata와 pipeline GUI thin-client 계약을 README/제품 문서/runtime 문서에 함께 맞췄습니다.
- work-log-closeout: 이번 라운드 직접 수정 파일과 실제 실행한 검증만 기준으로 closeout 형식을 맞췄습니다.

## 변경 이유
- active profile을 A(`implement=Codex`, `verify=Claude`, `advisory=Gemini`)로 바꾼 뒤에도 watcher export surface와 `pipeline_gui` current-turn summary 일부는 여전히 legacy enum 이름(`CLAUDE_ACTIVE`, `CODEX_VERIFY`)을 owner처럼 읽어 `Claude/Codex`를 고정 표시할 여지가 남아 있었습니다.
- 실제 prompt dispatch와 pane target은 이미 role-bound owner를 따르는데, thin-client read model만 예전 enum 의미를 재해석하면 controller는 맞고 watcher/home card는 틀리는 surface drift가 생깁니다.

## 핵심 변경
- `watcher_core.py`가 `.pipeline/state/turn_state.json`와 runtime event payload에 legacy `state`와 함께 `active_role` / `active_lane`을 기록하도록 확장했습니다.
- `pipeline_gui/backend.py`에 `describe_turn_state()`를 추가해 current-turn label이 `turn_state.active_role` / `turn_state.active_lane`을 우선 사용하고, metadata가 없을 때만 legacy enum fallback을 쓰게 했습니다.
- `pipeline_gui/home_controller.py`가 verify activity label과 `run_summary["turn"]`를 role-bound current-turn description으로 계산하도록 바꿨습니다.
- `tests/test_watcher_core.py`에 non-default profile에서 `turn_state.json`이 actual implement owner lane을 기록하는 케이스를 추가하고, 기존 turn-state export 테스트를 `active_role` / `active_lane`까지 고정하도록 넓혔습니다.
- `tests/test_pipeline_gui_backend.py`와 `tests/test_pipeline_gui_home_controller.py`는 swapped profile 예시에서 `Claude 검증 중` 같은 role-bound label을 그대로 surface하는지 고정했습니다.
- README와 runtime/operator 문서는 thin client가 legacy enum 이름만으로 owner를 재추론하지 말고 `turn_state.active_role` / `active_lane`을 우선 읽어야 한다는 계약으로 맞췄습니다.

## 검증
- `python3 -m py_compile watcher_core.py pipeline_gui/backend.py pipeline_gui/home_controller.py tests/test_watcher_core.py tests/test_pipeline_gui_backend.py tests/test_pipeline_gui_home_controller.py` → 통과
- `python3 -m unittest -v tests.test_pipeline_gui_backend.TestTurnStateRead tests.test_pipeline_gui_home_controller.PipelineGuiHomeControllerTest.test_build_snapshot_uses_runtime_status_as_single_source tests.test_pipeline_gui_home_presenter.PipelineGuiHomePresenterTest` → Ran 17 tests, OK
- `python3 -m unittest -v tests.test_pipeline_gui_backend tests.test_pipeline_gui_home_controller tests.test_pipeline_gui_home_presenter` → FAILED (`tests.test_pipeline_gui_backend.TestRuntimeStatusRead` 계열 8 failures, 3 errors). 이번 라운드가 건드린 `TestTurnStateRead`, `PipelineGuiHomeControllerTest`, `PipelineGuiHomePresenterTest` 케이스는 같은 실행에서 통과했습니다.
- `python3 -m unittest -v tests.test_watcher_core` → Ran 132 tests, OK

## 남은 리스크
- legacy enum `CLAUDE_ACTIVE` / `CODEX_VERIFY` 자체는 유지되므로, thin client가 앞으로도 `active_role` / `active_lane`을 무시하고 enum 이름만 보면 같은 owner drift가 다시 생길 수 있습니다.
- broad `tests.test_pipeline_gui_backend`에는 이번 라운드와 직접 겹치지 않는 runtime-status normalization 계열 failure가 남아 있습니다. 다음 pipeline GUI/runtime truth-sync 라운드에서 별도로 닫아야 합니다.
- 이번 라운드는 watcher export surface와 home-card label만 고쳤습니다. 다른 internal tooling이 `turn_state.state` 문자열만 읽는 경로가 더 있으면 같은 패턴의 후속 sync가 필요할 수 있습니다.
