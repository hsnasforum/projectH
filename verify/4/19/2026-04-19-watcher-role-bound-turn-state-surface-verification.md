# 2026-04-19 watcher role-bound turn state surface verification

## 변경 파일
- `verify/4/19/2026-04-19-watcher-role-bound-turn-state-surface-verification.md`

## 사용 skill
- `round-handoff`: 최신 `/work`(`work/4/19/2026-04-19-watcher-role-bound-turn-state-surface.md`)를 현재 tree와 대조해 truth를 재확인하고, 같은 날 기존 `/verify` 노트를 덮지 않고 이번 라운드용 새 verification 노트를 남겼습니다.

## 변경 이유
- prompt에서 최신 `/work`를 `work/4/19/2026-04-19-watcher-role-bound-turn-state-surface.md`로 가리키고, 해당 `/work`에 매칭되는 verification이 아직 같은 날 verify 폴더에 없었습니다.
- 같은 날 최신 verify인 `verify/4/19/2026-04-19-active-context-summary-hint-basis-field-verification.md`는 다른 family(`summary_hint_basis`) 검수 결과이므로 in-place 갱신은 truth loss를 일으킬 수 있어, 이번 라운드용 새 파일을 추가했습니다.
- seq 363 `.pipeline/operator_request.md` stop 이후 runtime-hardening 축으로 3개 라운드(`operator-stop-verified-blocker-recovery-scope`, `controller-role-bound-office-view`, `watcher-role-bound-turn-state-surface`)가 실제로 shipped되었기 때문에, next-slice 판단 전에 가장 최신 라운드만이라도 truthful한지 고정해야 했습니다.

## 핵심 변경
- 최신 `/work`의 구현 주장은 현재 tree와 일치합니다.
  - `watcher_core.py`에 `active_role` / `active_lane` 관련 참조 13건이 실존하며 `_TURN_STATE_ROLES` 등 role-bound 테이블과 export 경로가 들어 있습니다.
  - `pipeline_gui/backend.py`에 `describe_turn_state(turn_state)`가 실제로 존재하고, `turn_state["active_lane"]`/`active_role`을 우선 읽고 누락 시 legacy `state_value` fallback으로 `"CLAUDE_ACTIVE" 실행 중`류 label을 구성합니다.
  - `pipeline_gui/home_controller.py`에도 `active_role` / `active_lane` 참조가 들어가 verify activity label 계산에 쓰입니다.
- focused rerun은 모두 통과했습니다.
  - `python3 -m unittest -v tests.test_pipeline_gui_backend.TestTurnStateRead tests.test_pipeline_gui_home_controller.PipelineGuiHomeControllerTest.test_build_snapshot_uses_runtime_status_as_single_source tests.test_pipeline_gui_home_presenter.PipelineGuiHomePresenterTest` → `Ran 17 tests`, `OK`
  - `python3 -m unittest tests.test_watcher_core` → `Ran 133 tests`, `OK`
  - `python3 -m py_compile watcher_core.py pipeline_gui/backend.py pipeline_gui/home_controller.py` → 출력 없음, 통과
  - `git diff --check -- watcher_core.py pipeline_gui/backend.py pipeline_gui/home_controller.py tests/test_watcher_core.py tests/test_pipeline_gui_backend.py tests/test_pipeline_gui_home_controller.py README.md docs/PRODUCT_SPEC.md docs/ARCHITECTURE.md docs/ACCEPTANCE_CRITERIA.md docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md .pipeline/README.md` → exit code `0`
- `tests.test_watcher_core`는 `/work`에 `Ran 132 tests`로 적혀 있지만 현재 재실행 결과는 `Ran 133 tests`입니다. 해당 모듈의 같은 라운드 이후 추가 변경은 파일에 없으므로 계수 drift는 round 외부(다른 dirty hunk)의 영향으로 보이며, 통과/실패 결과 자체는 `OK`로 동일합니다.

## 검증
- 직접 코드/문서 대조
  - 대상: `watcher_core.py`, `pipeline_gui/backend.py`, `pipeline_gui/home_controller.py`, `tests/test_watcher_core.py`, `tests/test_pipeline_gui_backend.py`, `tests/test_pipeline_gui_home_controller.py`, `.pipeline/README.md`, `README.md`, `docs/PRODUCT_SPEC.md`, `docs/ARCHITECTURE.md`, `docs/ACCEPTANCE_CRITERIA.md`, `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`, `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`.
  - 결과: `/work`가 설명한 watcher export `active_role`/`active_lane`, `describe_turn_state()` 추가, home-card role-bound label, README/runtime 문서의 thin-client 계약 문장이 현재 tree와 일치함을 확인했습니다.
- `python3 -m unittest -v tests.test_pipeline_gui_backend.TestTurnStateRead tests.test_pipeline_gui_home_controller.PipelineGuiHomeControllerTest.test_build_snapshot_uses_runtime_status_as_single_source tests.test_pipeline_gui_home_presenter.PipelineGuiHomePresenterTest`
  - 결과: `Ran 17 tests`, `OK`
- `python3 -m unittest tests.test_watcher_core`
  - 결과: `Ran 133 tests`, `OK`
- `python3 -m py_compile watcher_core.py pipeline_gui/backend.py pipeline_gui/home_controller.py`
  - 결과: 출력 없음, exit code `0`
- `git diff --check` on scope files above → 출력 없음, exit code `0`
- broad `tests.test_pipeline_gui_backend`, Playwright, `make e2e-test`은 이번 verify에서 다시 돌리지 않았습니다.
  - 이유: `/work`가 같은 실행에서 `TestRuntimeStatusRead` 계열 기존 failure가 이번 라운드 범위와 겹치지 않는 다른 truth-sync 과제임을 이미 기록했고, 이번 `/work`는 browser-visible 계약을 바꾸지 않았으며 공유 브라우저 helper에 손대지 않아 focused owner/service 레벨 regression이 현재 truth 판정에 충분했습니다.

## 남은 리스크
- legacy enum `CLAUDE_ACTIVE` / `CODEX_VERIFY` 자체는 유지되므로, 다른 thin client가 앞으로도 `active_role`/`active_lane`을 무시하고 enum 이름만 보면 같은 owner drift가 다시 생길 수 있습니다. 이번 verify는 watcher/backend/home-controller 경로만 고정했습니다.
- broad `tests.test_pipeline_gui_backend`에는 이번 라운드와 직접 겹치지 않는 runtime-status normalization 계열 failure가 남아 있다고 최신 `/work`에 이미 보고되어 있습니다. 이 failure는 이번 `/work` truth 판정을 뒤집지 않지만, 별도 truth-sync 라운드로 닫아야 할 dirty state로 유지됩니다.
- seq 363 `.pipeline/operator_request.md`가 제기한 `Milestone 4 exact slice` 질문은 여전히 implicit하게 열려 있습니다. 세 번의 role-bound 런타임 하드닝 라운드가 지나갔지만 Gemini advice 362의 "axis switch to Milestone 4" 추천이 exact slice로 구체화된 적은 없습니다. 다음 control은 이 저신뢰 ambiguity를 Gemini로 다시 넘겨 좁혀야 합니다.
