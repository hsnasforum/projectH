# 2026-04-21 standing directive conflict arbitration

## Request
- `standing_directive_conflict` (CONTROL_SEQ 706)
- Conflict: Standing Directive A (seq 696 — don't commit small slices) vs. Gemini Advisory B (seq 702 — axis complete, stabilize and move to Milestone 5).
- Symptom: 3x immediate retriage loop for Gate C (commit+push).

## Assessment

### 1. Qualification as "Large Verification Bundle"
Standing Directive A (seq 696) was intended to prevent the automation from stalling on every minor slice by requiring commits only for significant boundaries. 
The current "dirty worktree" includes:
- The entire G4-G15 axis (Watcher Turn State, Signal Mismatch Deferral, Task Hint Corroboration).
- Automation Health module and logic.
- Session Recovery Budget Guard.
- Progress Phase Hints.
- Stale Control Detection and Advisory Routing.
- GUI/Launcher presentation surfaces for all the above.
- Comprehensive test coverage (174 Watcher, 126 Supervisor, etc.).

This is no longer a "small/local slice". It is the culmination of a multi-hour development cycle focused on "automation stabilization" (as requested in seq 696).

### 2. Resolution of the Conflict
Gemini Advisory B (seq 702) marked this axis as "complete". This completion status serves as the logical trigger to promote the accumulated work from "dirty state" to a "large verification bundle" (release-worthy). 

Proceeding with **Path A** resolves the retriage loop by explicitly categorizing the current work as having met the "large bundle" threshold defined in Standing Directive A. Stabilization (commit/push) is the prerequisite for the recommended `6h synthetic soak` and Milestone 5 transition.

## Recommendation
**A (Bundle qualifies as gate-level, not small/local) is recommended.**

The watcher should cease the retriage loop and proceed with the Gate C operator_request. The "axis complete" assessment (seq 702) effectively supersedes the "continue small slices" direction from seq 696 for this specific family.

**RECOMMEND: needs_operator commit/push all dirty changes to origin/feat/watcher-turn-state**
- This commit represents the completion of the `feat/watcher-turn-state` stabilization axis.
- After commit, proceed to the `6h synthetic soak` (Gate D) as planned.
