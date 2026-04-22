# 2026-04-22 Milestone 7 Axis 4 Complete - Milestone 8 Entry

## Context
- Milestone 7 Axis 4 (seqs 818-819)가 성공적으로 완료되어 `candidate_review_record`에 `suggested_scope` 필드가 추가되었습니다.
- Milestone 7의 남은 항목들(scope/conflict/rollback 규칙 정의 등)은 "reviewed-memory planning"이 열려야 가능하며, 이는 시스템이 문서 작업 정합성을 충분히 증명한 후에 진행하는 것이 안전합니다.
- `docs/MILESTONES.md`의 "Next 3 Implementation Priorities" 섹션에 `edit` 등 이미 구현된 항목이 미래 작업으로 남아 있어 동기화가 필요합니다.

## Analysis of Questions
1.  **Milestone 8 entry**: **Milestone 8 (Workflow-Grade Eval Assets)로 진입하는 것이 올바른 순서입니다.** 복잡한 planning logic을 열기 전에, 현재까지의 교정/수락/거절 트레이스가 "Mistake reduction"에 기여하는지 측정할 수 있는 fixture와 contract를 정의하는 것이 `MILESTONES:442`의 원칙(Program operation follows stable memory)에 부합합니다.
2.  **Stale Priorities**: `docs/MILESTONES.md`의 stale한 우선순위 섹션은 Milestone 8 진입 전 또는 진입 슬라이스(Axis 1)에서 **반드시 정리해야 합니다.** 현재의 진척도가 문서에 정확히 반영되어야 다음 구현자의 혼선을 막을 수 있습니다.
3.  **Suggested_scope constraints**: **Milestone 8의 eval fixture 설계 단계에서 정의하는 것을 권장합니다.** 실제 테스트 시나리오와 데이터 매트릭스를 구성하면서 필요한 scope 범주(예: `message_only`, `family_scoped`, `global_preference`)를 도출하는 것이 가장 실질적이고 근거 있는 접근입니다.

## Recommendation
- **Next Slice (Axis 1 of Milestone 8 / Doc-Sync)**: 
  - `docs/MILESTONES.md`의 stale한 우선순위 섹션 최신화.
  - Milestone 8 "Fixture matrix" 및 "Core trace contract" 설계를 위한 `docs/projectH_pipeline_runtime_docs/` 또는 `eval/` 디렉터리 기반의 기초 slice 시작.
