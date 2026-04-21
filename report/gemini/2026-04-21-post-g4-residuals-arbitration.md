# 2026-04-21 post-G4 residuals arbitration

## 개요
- AXIS-G4 (supervisor signal mismatch guard 및 wrapper emitter 보강) 시리즈가 seq 596으로 완료되었습니다.
- seq 593에서 발생한 대규모 scope violation이 수용되었으나, 해당 라운드에서 추가된 `_force_stopped_surface`와 `dispatch_selection` 이벤트 방출 로직에 대한 명시적이고 포괄적인 테스트 커버리지가 부족한 상태입니다.
- 이를 해결하기 위한 차기 implement slice와 관련 위험 요소를 검토했습니다.

## 판단 근거
1. **판단 우선순위**: `AGENTS.md`의 tie-break 원칙에 따라 `same-family current-risk reduction`이 최우선입니다. AXIS-G4의 잔존 리스크(untested features in supervisor.py)를 해소하는 것이 신규 quality axis(tracing backfill) 진입보다 우선됩니다.
2. **Coherency**: `_force_stopped_surface`와 `dispatch_selection`은 모두 seq 593에서 `supervisor.py`에 함께 도입된 기능들로, 하나의 "G4 closeout/stabilization" 슬라이스로 묶어 처리하는 것이 아키텍처적으로 일관성 있습니다.
3. **Verification Integrity**: `turn_state` vocabulary 정규화(`CLAUDE_ACTIVE` -> `IMPLEMENT_ACTIVE` 등)가 supervisor 전반에 적용되었으므로, 기존에 silent 처리되었던 G5 suite들을 재실행하여 정합성을 보장해야 합니다.

## 답변 (Questions for Gemini)

### Q1. 차기 Codex implement slice (CONTROL_SEQ 597)
- **권고**: **(a) Add dedicated test coverage for `_force_stopped_surface` and `dispatch_selection` event**.
- 이유: seq 593의 scope violation을 공식화(formalize)하고 "stability lock"을 완성하여 기술적 부채와 리스크를 제거합니다.

### Q2. 커버리지 범위 및 파일
- **권고**: **한 슬라이스에 두 항목 모두 포함**.
- 파일: `tests/test_pipeline_runtime_supervisor.py`.
- 내용:
    - `_force_stopped_surface`가 `shutdown_runtime` 경로에서 `STOPPED` 상태를 강제하고 `active_round`를 정리하는지 검증.
    - `_write_status` 사이클마다 `dispatch_selection` 이벤트가 누적되는지, 그리고 `job_states`가 주어졌을 때 `_build_artifacts`가 올바른 verify path를 찾는지 검증.

### Q3. G5 silent suites 실행 시점
- **권고**: 차기 implement 라운드의 **verification 단계에서 병렬 또는 통합 실행**.
- 이유: 이미 `test_pipeline_runtime_supervisor` (103 tests OK)를 통해 정규화된 어휘의 기본 동작이 검증되었으므로, 이를 위해 별도의 verify-only 라운드를 소모하기보다 차기 라운드의 검증 범위에 포함하는 것이 효율적입니다.

## 추천 Recommendation
- `RECOMMEND: implement AXIS-G4 supervisor residuals (coverage for _force_stopped_surface and dispatch_selection event)`
