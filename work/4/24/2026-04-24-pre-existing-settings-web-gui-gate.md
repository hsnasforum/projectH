# 2026-04-24 pre-existing settings web gui gate

## 변경 파일
- `config/settings.py` (pre-existing dirty)
- `app/web.py` (pre-existing dirty)
- `scripts/pipeline_runtime_gate.py` (pre-existing dirty)
- `scripts/promote_assets.py` (pre-existing dirty)
- `pipeline_gui/setup_controller.py` (pre-existing dirty)
- `pipeline_gui/setup_executor.py` (pre-existing dirty)
- `tests/test_pipeline_runtime_gate.py` (pre-existing dirty)
- `tests/test_pipeline_gui_app.py` (pre-existing dirty)
- `tests/test_web_app.py` (pre-existing dirty + 이번 라운드 4행 회귀 수정)
- `work/4/24/2026-04-24-pre-existing-settings-web-gui-gate.md` (이번 라운드 closeout)

## 사용 skill
- `work-log-closeout`: pre-existing dirty 변경과 이번 라운드 직접 편집 범위, 실제 검증 결과, 남은 리스크를 한국어 `/work` 기록으로 정리했습니다.

## 변경 이유
- `config/settings.py`: 기본 경로 문자열을 `DEFAULT_*` 상수로 올려 다른 모듈이 default 여부를 일관되게 판정할 수 있게 했습니다.
- `app/web.py`: manual file-store override가 있을 때 `_effective_service_settings()`와 companion JSON store 격리를 적용해 tmp 경로 테스트/런타임이 기본 `data/`를 오염시키지 않게 했습니다.
- `scripts/pipeline_runtime_gate.py`: operator gate가 dispatch control 표면에서 숨겨진 상태를 mismatch로 오판하지 않도록 `_control_surface_matches_active_slot()`을 추가했습니다.
- `scripts/promote_assets.py`: correction lifecycle guard 이후에도 asset promotion이 `recorded -> confirmed -> promoted` 순서를 지키도록 `_ensure_promoted()`를 추가했습니다.
- `pipeline_gui/setup_controller.py`: orphan result만 남은 경우를 applied truth로 보지 않도록 disk cached state context 판정을 분리했습니다.
- `pipeline_gui/setup_executor.py`: setup executor background thread를 추적하고 테스트가 `wait_for_idle()`로 안정적으로 기다릴 수 있게 했습니다.
- `tests/test_pipeline_runtime_gate.py`: hidden operator gate control surface가 soak mismatch로 잡히지 않는 회귀를 검증합니다.
- `tests/test_pipeline_gui_app.py`: setup executor idle 대기와 orphan result 무시 동작을 검증합니다.
- `tests/test_web_app.py`: 기존 assertion drift를 반영했고, 이번 라운드에서 4개 external fact 테스트에 `sqlite_db_path=str(tmp_path / "test.db")`를 추가해 `_effective_service_settings()`의 JSON switch로 인한 hang을 막았습니다.

## 핵심 변경
- 이번 라운드 직접 편집은 `tests/test_web_app.py`의 4개 `AppSettings(...)`에 `sqlite_db_path=str(tmp_path / "test.db")`를 추가한 것뿐입니다.
- pre-existing 변경은 settings default 상수화, web service storage isolation, runtime gate control matching, asset promotion lifecycle 보정, setup GUI cache/thread 안정화와 그 단위 테스트입니다.
- `tests/test_web_app.py`는 같은 파일 안에 pre-existing assertion 변경과 이번 4행 regression fix가 함께 존재합니다.
- 코드 편집 없이 closeout을 남기려던 이전 검증은 socket `PermissionError`와 4개 external fact hang 리스크 때문에 막혔고, 이번 라운드는 handoff가 지정한 4개 테스트만 직접 수정했습니다.

## 검증
- `python3 -m py_compile config/settings.py app/web.py scripts/pipeline_runtime_gate.py scripts/promote_assets.py pipeline_gui/setup_controller.py pipeline_gui/setup_executor.py tests/test_web_app.py`
  - 통과: 출력 없음
- `python3 -m py_compile config/settings.py app/web.py scripts/pipeline_runtime_gate.py scripts/promote_assets.py pipeline_gui/setup_controller.py pipeline_gui/setup_executor.py tests/test_pipeline_runtime_gate.py tests/test_pipeline_gui_app.py tests/test_web_app.py`
  - 통과: 출력 없음
- `python3 -m unittest -v tests.test_pipeline_gui_app tests.test_pipeline_runtime_gate 2>&1 | tail -5`
  - 통과: exit 0. tail 출력은 soak PASS 로그였고, 별도 요약 캡처에서 `Ran 90 tests in 1.087s`, `OK` 확인
- `python3 -m unittest -v tests.test_pipeline_gui_app tests.test_pipeline_runtime_gate`
  - 통과: `Ran 90 tests in 1.087s`, `OK`
- `python3 -m unittest -v tests.test_web_app.WebAppServiceTest.test_handle_chat_external_fact_info_uses_web_search_when_enabled tests.test_web_app.WebAppServiceTest.test_handle_chat_external_fact_who_question_uses_web_search_when_enabled tests.test_web_app.WebAppServiceTest.test_handle_chat_external_fact_who_question_with_spaced_question_mark_uses_web_search_when_enabled tests.test_web_app.WebAppServiceTest.test_handle_chat_external_fact_colloquial_info_questions_use_web_search_when_enabled 2>&1 | tail -5`
  - 통과: `Ran 4 tests in 14.543s`, `OK`
- `git diff --check -- tests/test_web_app.py`
  - 통과: 출력 없음
- `git diff --check -- config/settings.py app/web.py scripts/pipeline_runtime_gate.py scripts/promote_assets.py pipeline_gui/setup_controller.py pipeline_gui/setup_executor.py tests/test_pipeline_runtime_gate.py tests/test_pipeline_gui_app.py tests/test_web_app.py`
  - 통과: 출력 없음

## 남은 리스크
- 이전 전체 `tests.test_web_app` 단독 실행에서는 socket 생성 제한으로 `LocalOnlyHTTPServer(("127.0.0.1", 0), service)` 기반 10개 테스트가 `PermissionError: [Errno 1] Operation not permitted`를 냈습니다. 이번 handoff acceptance는 해당 전체 suite가 아니라 4개 회귀 테스트만 요구했습니다.
- `make e2e-test`와 browser smoke는 handoff 범위를 넘어 실행하지 않았습니다.
- 현재 worktree에는 이번 closeout 범위 밖의 `scripts/pipeline_runtime_fake_lane.py`, `tests/test_pipeline_runtime_fake_lane.py`, `report/pipeline_runtime/verification/2026-04-24-pipeline-runtime-synthetic-5m-soak.*` dirty/untracked 항목이 남아 있습니다. 이번 라운드에서는 수정하지 않았습니다.
