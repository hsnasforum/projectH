# 2026-05-21 lane catalog AgentProfileSpec

## 변경 파일
- `pipeline_runtime/lane_catalog.py`
- `tests/test_pipeline_runtime_lane_catalog.py`
- `work/5/21/2026-05-21-lane-catalog-agent-profile-spec.md`

## 사용 skill
- `finalize-lite`: 실행한 검증, 미실행 범위, 문서 동기화 필요 여부, `/work` closeout 필요 여부를 정리하기 위해 사용했습니다.
- `work-log-closeout`: 변경 파일, 실제 검증, 남은 리스크를 한국어 `/work` 기록으로 남기기 위해 사용했습니다.

## 변경 이유
- `build_agent_profile_payload()`의 9개 키워드 인자를 한 곳에서 타입/기본값으로 설명할 수 있도록 `AgentProfileSpec` dataclass가 필요했습니다.
- 기존 호출 측은 그대로 유지해야 하므로 공개 `build_agent_profile_payload()` 시그니처와 반환 dict 구조는 바꾸지 않는 것이 목표였습니다.
- 새 코드나 테스트에서는 `AgentProfileSpec`을 직접 조립해 `_build_from_spec()`에 넘길 수 있어야 했습니다.

## 핵심 변경
- `pipeline_runtime/lane_catalog.py`에 `AgentProfileSpec` frozen dataclass를 추가했습니다.
- 기존 `build_agent_profile_payload()` 본문 로직을 `_build_from_spec(spec: AgentProfileSpec)`로 이동했습니다.
- `build_agent_profile_payload()`의 기존 키워드 파라미터 목록은 유지하고, 내부에서 `AgentProfileSpec`을 만들어 `_build_from_spec()`에 위임하도록 바꿨습니다.
- 반환 dict의 `schema_version`, `selected_agents`, `role_bindings`, `role_options`, `mode_flags` 구조는 변경하지 않았습니다.
- `tests/test_pipeline_runtime_lane_catalog.py`를 추가해 기존 키워드 호출 구조와 `AgentProfileSpec` 직접 경로의 동등성을 검증했습니다.

## 검증
- 통과: `python3 -m py_compile pipeline_runtime/lane_catalog.py`
  - 결과: PASS, 출력 없음.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_lane_catalog -v`
  - 결과: `Ran 2 tests in 0.000s`, `OK`.
- 통과: `python3 -c "... AgentProfileSpec, build_agent_profile_payload, _build_from_spec ..."`
  - 결과: `AgentProfileSpec OK`.
- 통과: `python3 -m unittest tests.test_pipeline_runtime_supervisor -v 2>&1 | tail -5`
  - 결과: `Ran 221 tests in 2.199s`, `OK`.
- 통과: `git diff --check -- pipeline_runtime/lane_catalog.py`
  - 결과: PASS, 출력 없음.

## 남은 리스크
- `scripts/pipeline_runtime_gate.py`와 `pipeline_gui/setup_controller.py` 호출 측은 이번 slice에서 변경하지 않았습니다. 기존 공개 함수 시그니처가 유지되어 동작 호환은 유지됩니다.
- 전체 repo unittest discover, GUI 테스트 전체, browser/E2E, live runtime/tmux 검증은 실행하지 않았습니다.
- 현재 worktree에는 이전 Claude print JSONL lane integration, turn arbitration, schema/role harness 관련 수정/기록 파일이 남아 있습니다. 이번 slice에서는 관련 없는 기존 변경을 되돌리거나 포함하지 않았습니다.
- commit, push, branch/PR publication, PR creation, merge, release, publication은 실행하지 않았습니다.
