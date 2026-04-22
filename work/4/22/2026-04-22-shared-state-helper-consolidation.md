# 2026-04-22 shared state helper consolidation

## 변경 파일
- `pipeline_runtime/schema.py`
- `pipeline_runtime/supervisor.py`
- `pipeline_runtime/turn_arbitration.py`
- `watcher_core.py`
- `watcher_prompt_assembly.py`
- `pipeline_gui/backend.py`
- `tests/test_pipeline_runtime_schema.py`
- `tests/test_pipeline_gui_backend.py`
- `work/4/22/2026-04-22-shared-state-helper-consolidation.md`

## 사용 skill
- `finalize-lite`: 구현 종료 전 검증 범위, 문서 동기화 필요성, `/work` closeout 준비 상태를 좁게 확인했습니다.
- `work-log-closeout`: 실제 변경 파일, 실행 명령, 남은 리스크만 기준으로 이 closeout을 작성했습니다.

## 변경 이유
- 사용자 요청에 따라 서브에이전트 2개를 활용해 `pipeline_runtime` shared state parsing 기반의 launcher/watcher/supervisor 자동화 정리 상태를 재점검했습니다.
- 서브에이전트 확인 결과 큰 4축 bundle은 이미 완료된 상태였고, 남은 정리성 리스크는 `CONTROL_SEQ` coercion, control header parsing, runtime status control block 생성이 여러 소비자에 흩어진 점이었습니다.
- 이번 라운드는 마일스톤 재개나 제품 slice가 아니라, 같은 control state를 watcher/supervisor/GUI가 같은 helper로 해석하게 만드는 bounded cleanup입니다.

## 핵심 변경
- `pipeline_runtime/schema.py`에 `control_seq_value()`, `snapshot_control_seq()`, `parse_control_meta_text()`, `control_block_from_snapshot()`을 추가해 control seq/header/status block 해석을 shared helper로 모았습니다.
- `RuntimeSupervisor`, `turn_arbitration`, `watcher_core`, `watcher_prompt_assembly`의 raw `int(...control_seq...)` coercion과 status block 조립을 shared helper 사용으로 바꿨습니다.
- `pipeline_gui/backend.py`의 Windows/WSL control-slot branch는 WSL file query adapter를 유지하면서 header parsing만 `parse_control_meta_text()`로 공유하게 했습니다.
- GUI Windows branch가 invalid `CONTROL_SEQ`를 만나도 같은 shared parser 규칙으로 안전하게 무시하고 valid seq slot을 우선하는 테스트를 추가했습니다.
- schema helper 단위 테스트로 bool/invalid/negative seq 처리, text header parsing, empty/active control block shape를 고정했습니다.

## 검증
- `python3 -m py_compile pipeline_runtime/schema.py pipeline_runtime/supervisor.py pipeline_runtime/turn_arbitration.py watcher_core.py watcher_prompt_assembly.py pipeline_gui/backend.py` 통과
- `python3 -m unittest tests.test_pipeline_runtime_schema tests.test_pipeline_runtime_supervisor tests.test_turn_arbitration tests.test_watcher_core tests.test_pipeline_gui_backend` 통과 (`430 tests`)
- `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q -p no:cacheprovider tests/test_pipeline_runtime_schema.py tests/test_pipeline_gui_backend.py::TestParseControlSlots tests/test_pipeline_gui_backend.py::TestParseControlSlotsWindowsBranch tests/test_watcher_core.py::ClaudeImplementBlockedTest::test_higher_control_seq_beats_newer_mtime tests/test_watcher_core.py::TransitionTurnTest::test_transition_writes_turn_state_json tests/test_pipeline_runtime_supervisor.py::RuntimeSupervisorTest::test_build_active_round_prefers_current_control_seq_match` 통과 (`64 passed`)
- `python3 -m unittest tests.test_verify_fsm` 통과 (`5 tests`)
- `git diff --check` 통과
- `python3 -c "from pathlib import Path; from pipeline_runtime.schema import parse_control_slots; r=parse_control_slots(Path('.pipeline')); print('active:', r['active']['file'], r['active']['control_seq'])"` 실행 결과: `active: advisory_advice.md 755`

## 남은 리스크
- 이번 라운드는 commit/push를 하지 않았습니다.
- 현재 dirty tree에는 이번 helper consolidation 이전에 생성된 4축 runtime bundle 변경, `/work`, `/verify`, `report/gemini`, `tests/test_verify_fsm.py` 등이 함께 남아 있습니다. 커밋 전에는 포함 범위를 다시 확인해야 합니다.
- `pipeline_gui/backend.py`의 Windows branch는 파일 조회 adapter 특성상 runtime `parse_control_slots()`를 직접 재사용하지 않고, header parsing helper만 공유합니다. 이 중복은 Windows/WSL I/O adapter를 분리할 때 추가 정리할 수 있습니다.
- active control은 검증 시점 기준 `.pipeline/advisory_advice.md` CONTROL_SEQ 755였습니다. 이 slot은 live pipeline 진행에 따라 계속 바뀔 수 있습니다.
