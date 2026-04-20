# 2026-04-19 investigation conflict status separation arbitration

## 개요
- **Arbitration 대상**: Seq 364 차기 control path 결정
- **결정**: Option A (Milestone 4 exact slice) 선택
- **Exact Slice**: `core/web_claims: CoverageStatus.CONFLICT support`

## 판단 근거
1. **Axis 전환 우선순위**: 오늘 2026-04-19에 이미 3개의 role-bound runtime-hardening 라운드가 shipped되어 하나의 coherent bundle을 형성했습니다. `GEMINI.md`의 우선순위상 same-family 리스크가 현저히 줄어든 상태이므로, 다음 상위 우선순위인 Milestone 4(Secondary-Mode Investigation Hardening) axis로의 전환이 적절합니다.
2. **Exact Slice 가독성**: 이전 Gemini advice(Seq 362)에서 Milestone 4 전환을 추천했으나 구체적인 slice가 명시되지 않아 Codex가 implementation을 시작하지 못했습니다. 이번에 제안하는 `CONFLICT` 상태 분리는 Milestone 4의 핵심인 'investigation quality hardening'을 위한 가장 작고 명확한(bounded) 시작점입니다.
3. **타 Axis 배제**: 
   - **Option B (Residual Role-bound)**: GUI label normalization은 유의미한 drift 리스크이나, 오늘 이미 3번의 라운드가 진행된 axis의 micro-slice이므로 새 axis의 첫 slice보다 우선순위가 낮습니다.
   - **Option C (Test Cleanup)**: `tests.test_pipeline_gui_backend` 실패는 supervisor 전환에 따른 truth-sync 과제이나, 이는 'internal cleanup' 범주에 해당하여 새 품질 축(Milestone 4)보다 후순위입니다.

## 추천 Slice 상세
- **Title**: `core/web_claims: CoverageStatus.CONFLICT support`
- **목적**: `CoverageStatus.WEAK`에 섞여 있는 "신뢰할 만한 근거 부족"과 "신뢰할 만한 근거 간 충돌"을 분리하여, 재조사(reinvestigation) UI에 더 정확한 상태 신호를 제공합니다.
- **범위**:
  - `core/contracts.py`: `CoverageStatus` enum에 `CONFLICT = "conflict"` 추가.
  - `core/web_claims.py`: `summarize_slot_coverage()` 내에서 `_has_competing_trusted_alternative()`가 true인 경우 `CoverageStatus.CONFLICT`를 반환하도록 수정.
  - `tests/test_smoke.py`: `test_summarize_slot_coverage_conflicting_trusted_alternative_downgrades_to_weak`를 `..._to_conflict`로 업데이트하고 새 status 검증.
- **검증**: `python3 -m unittest tests/test_smoke.py -k summarize_slot_coverage`

## 리스크 및 주의사항
- `core/agent_loop.py` 등 `summarize_slot_coverage` 호출부에서 새 status를 처리하지 못해 생길 수 있는 UI drift는 다음 UI hardening slice에서 닫는 것을 전제로 하며, 이번 slice는 core logic truth 고정에 집중합니다.
- 현재 worktree의 dirty hunk들을 유지한 채로 surgical하게 적용할 것을 권고합니다.
