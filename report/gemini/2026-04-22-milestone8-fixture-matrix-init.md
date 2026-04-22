# 2026-04-22 Milestone 8 Entry - Fixture Matrix Definition

## Context
- Milestone 7 Axis 1-4 (infrastructure & doc cleanup) is complete and committed/pushed (SHA `afe0f3a`).
- Milestone 7 "still later" items (scope/conflict/rollback rules) are deferred until "reviewed-memory planning" opens.
- The system is currently idle after a commit/push bundle authorization (seq 824) returned idle from retriage.
- Moving to Milestone 8 (Workflow-Grade Eval Assets) is the architectural priority to establish "Program operation follows stable memory" principles.

## Decision
- Close the Milestone 7 infrastructure family and switch to the Milestone 8 axis.
- The first implementation slice for Milestone 8 is defining the "named fixture-family matrix" and the "eval-ready artifact core trace contract".

## Recommendation
- **RECOMMEND: implement Milestone 8 Axis 1 (Fixture-Family Matrix Definition)**
- This slice should define the named fixture-family matrix for document -> grounded brief quality, including axes for correction reuse, approval friction, and reviewability.
- Suggested scope constraints (defined in M7 Axis 4) should be 도출(derived) as part of this fixture design.
- The implementation should target `docs/MILESTONES.md` or a new `eval/` documentation file to formalize the evaluation contract.
