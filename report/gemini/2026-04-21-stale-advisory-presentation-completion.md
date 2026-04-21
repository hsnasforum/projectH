# 2026-04-21 stale advisory presentation completion

## Request
- `slice_necessity_assessment` (CONTROL_SEQ 701)
- Context: Launcher/GUI surface for `stale_advisory_pending` was stalled for 3 rounds.
- Arbitration: Is the UI surface essential, and what is the next automation slice?

## Assessment

### 1. Presentation Surface Necessity
The implementation owner (Claude) finally completed the launcher line-mode and GUI presenter surface in turn `seq 702` (referenced in latest work note).
- `pipeline-launcher.py`: Line-mode `Automation detail` now displays `stale_advisory_pending`.
- `pipeline_gui/home_presenter.py`: Console detail now displays the stale advisory status.
- Verification: 45 tests OK across launcher and presenter suites.

The question of necessity (Question A) is resolved by implementation. The automation loop (Detection -> UI Surface -> Advisory Request) is now end-to-end coherent and visually surfaced for the operator.

### 2. Next Automation Slice
The `feat/watcher-turn-state` branch has accumulated a massive "dirty worktree" (G4-G15, automation health, retriage fixes, stale control detection, UI surfaces). 
- Candidate B2 (Stale operator_request conflict policy) remains as a known edge case where Gemini might auto-write a request while an operator is already present.
- However, given the current "advisory-first" priority and the robustness of the existing idempotency guards, this is a minor stability risk compared to the risk of continuing to grow an uncommitted large-scale change bundle.

## Recommendation
**B3 (No remaining automation slice needed) is recommended.**

The automation health work stream is considered "substantially complete" and "visually surfaced". To maintain system integrity and minimize the cost of a catastrophic drift, the current bundle should be stabilized immediately.

**RECOMMEND: close family and switch axis Milestone 5 (after 6h soak)**
- Finalize the current `feat/watcher-turn-state` automation family.
- Execute the `6h synthetic soak` (Operator Gate D) to verify the large bundle.
- Proceed to Milestone 5 transition and PR stabilization.
