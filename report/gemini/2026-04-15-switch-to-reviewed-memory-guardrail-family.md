# Gemini Advisory: Switch to Reviewed-Memory Guardrail Family

## 개요
- **일시:** 2026-04-15
- **상태:** `markdown-container` helper direct-coverage 패밀리 종료 후 차기 슬라이스 조율
- **결정:** `markdown-container`의 잔여 edge case (indented code block, nested quote 등) 구현을 중단하고, `docs/NEXT_STEPS.md`의 최우선 순위인 `reviewed-memory boundary guardrail` 패밀리로 축 전환을 권고함.

## 판단 근거
1. **가치 대조:** `markdown-container` helper는 현재 5개 루트 문서 수준에서 필요한 분기가 모두 truthful하게 검증되었습니다. 사용되지 않는 복잡 구조에 대한 추가 matcher completeness는 우선순위 #4(internal cleanup)에 해당합니다.
2. **리스크 대조:** `reviewed-memory` 관련 기능(apply, stop-apply, reversal 등)이 설계/구현되었으나, 이들이 상위 promotion(재발 신호 승격)으로 이어지기 전 `blocked-all-required` 상태가 코드와 문서 수준에서 엄격하게 유지되고 있는지 확인하는 것은 우선순위 #1(current-risk reduction)에 해당합니다.
3. **문서 동기화:** `docs/NEXT_STEPS.md:106`, `docs/MILESTONES.md:450`, `docs/TASK_BACKLOG.md:162` 모두 동일하게 `reviewed_memory_precondition_status`를 `blocked-only`로 고정하는 guardrail을 차기 우선순위로 지목하고 있습니다.

## 권고 슬라이스: `reviewed-memory aggregate blocked-all-required stabilization`
- **목표:** `app.web` 페이로드와 `core` 모델 간의 `reviewed_memory_precondition_status` 계약을 `blocked_all_required` 상태로 동기화하고, `tests/test_smoke.py`에서 이를 엄격히 검증함.
- **범위:**
  - `app/handlers/aggregate.py`: `overall_status`가 항상 `blocked_all_required`를 반환하도록 보장.
  - `app/serializers.py`: 5개 필수 precondition(`boundary_defined`, `rollback_ready` 등)이 올바르게 노출되는지 확인.
  - `tests/test_smoke.py`: 집계(aggregate) 관련 schema-check 테스트 강화.
  - `docs/NEXT_STEPS.md`: 현재 구현 상태와 문서 간의 미세한 drift(이미 구현됨 vs 구현 예정) 정합성 확인.
- **검증:**
  - `python3 -m unittest -v tests.test_smoke` (aggregate 관련 섹션 집중 실행)
  - `make e2e-test` (UI 상에서 차단 상태가 올바르게 표시되는지 확인)

## 차기 제어권
- 이 슬라이스는 문서에 명시된 우선순위를 따르며 구현 범위가 명확하므로, Codex가 Gemini의 advice를 읽은 후 직접 `.pipeline/claude_handoff.md`를 작성하여 `STATUS: implement`로 진행할 수 있습니다. Operator 에스컬레이션은 불필요합니다.
