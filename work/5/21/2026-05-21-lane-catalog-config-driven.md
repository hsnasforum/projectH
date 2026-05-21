# 2026-05-21 lane catalog config driven

## 변경 파일
- `.pipeline/config/lanes.json` 신규 작성
- `pipeline_runtime/lane_catalog.py` 수정
- `pipeline_runtime/supervisor.py` 수정
- `tests/test_pipeline_runtime_supervisor.py` 수정
- `work/5/21/2026-05-21-lane-catalog-config-driven.md` 신규 작성

## 사용 skill
- `security-gate`: 물리 레인 구성과 agent CLI 실행 경로가 로컬 설정 기반으로 바뀌어도 operator 승인 경계와 local-first 범위가 완화되지 않는지 점검하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `Claude`, `Codex`, `Gemini` 물리 레인 스펙이 Python 상수에만 고정되어 새 agent CLI를 실험할 때 코드 수정이 필요했습니다.
- 기존 3개 레인 동작은 유지하면서, project-local `.pipeline/config/lanes.json`에서 레인 이름, pane index, 역할 가능 목록, token source, agent CLI, read-first 문서를 읽을 수 있게 하기 위해 변경했습니다.

## 핵심 변경
- `.pipeline/config/lanes.json`에 현재 3개 레인 구성을 기록했습니다.
- `load_physical_lane_specs(project_root)`를 추가해 `lanes.json`이 있으면 설정을 읽고, 없거나 깨졌거나 유효 lane이 없으면 기존 `_PHYSICAL_LANE_SPECS`로 fallback 하도록 했습니다.
- 기존 `physical_lane_specs()`, `physical_lane_order()` 인자 없는 인터페이스는 유지했습니다.
- `PhysicalLaneSpec`에 `roles`, `token_source`, `agent_cli` 필드를 추가하고, 기존 `vendor_args`, `token_source_root`, `pane_type`은 known agent 기본값으로 보강되게 했습니다.
- `build_lane_configs()`, `lane_vendor_command_parts()`, `read_first_doc_for_owner()`가 optional lane specs를 받을 수 있게 했고, 기존 호출은 default hardcoded specs를 계속 사용합니다.
- `RuntimeSupervisor`가 project root 기반 lane specs를 로드해 lane configs, vendor command, read-first doc, watcher pane target fallback에 사용하도록 연결했습니다.
- supervisor 테스트에 lanes config fallback, 설정 기반 로딩, custom lane 인식 및 custom vendor command 생성을 추가했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/lane_catalog.py pipeline_runtime/supervisor.py tests/test_pipeline_runtime_supervisor.py`
- 통과: `python3 -m unittest -v tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_load_physical_lane_specs_falls_back_without_lanes_config tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_load_physical_lane_specs_uses_lanes_config_when_present tests.test_pipeline_runtime_supervisor.RuntimeSupervisorTest.test_supervisor_recognizes_custom_lane_from_lanes_config`
  - 결과: `Ran 3 tests`, `OK`
- 통과: `python3 -m json.tool .pipeline/config/lanes.json >/tmp/projectH-lanes.json.check`
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: `Ran 219 tests`, `OK`
- 통과: `python3 -m py_compile pipeline_runtime/lane_catalog.py pipeline_runtime/supervisor.py`
- 통과: `git diff --check -- pipeline_runtime/lane_catalog.py pipeline_runtime/supervisor.py .pipeline/config/lanes.json`
- 통과: `git diff --check -- pipeline_runtime/lane_catalog.py pipeline_runtime/supervisor.py .pipeline/config/lanes.json tests/test_pipeline_runtime_supervisor.py`

## 남은 리스크
- `agent_profile.json` 및 setup GUI의 agent 선택/검증 경로는 아직 default lane order 기반입니다. 이번 handoff의 OUT_OF_SCOPE에 따라 통합하지 않았습니다.
- `watcher_core.py`는 이번 라운드에서 건드리지 않았습니다. watcher 자체 fallback은 여전히 기존 `physical_lane_specs()` default 경로를 사용합니다.
- custom lane을 실제 tmux pane으로 spawn하려면 tmux adapter pane mapping과 watcher target 옵션 확장이 추가로 필요할 수 있습니다. 이번 슬라이스는 supervisor가 config lane을 인식하고 vendor command/read-first 경로를 설정 기반으로 쓰는 범위까지입니다.
- `.pipeline/config/agent_profile.json`, runtime policy, sha256/receipt/schema, state contract, tmux adapter, 기존 `/work`/`verify` dirty 항목은 이전 슬라이스에서 이어진 변경이며 되돌리지 않았습니다.
- commit, push, PR 생성, merge, release, publication은 실행하지 않았습니다.
