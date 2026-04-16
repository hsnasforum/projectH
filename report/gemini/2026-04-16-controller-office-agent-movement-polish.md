# 2026-04-16 controller-office-agent-movement-polish arbitration

## Request
- @.pipeline/gemini_request.md (CONTROL_SEQ: 188)
- Recommend one exact next implementation slice after `controller-smoke-rerun-hardening` was truthfully reverified.

## Candidates
1. **Controller family:** office-scene polish (idle-ready agent movement / placement behavior / fatigue system / drones)
2. **Controller family:** Internal/Risk reduction (false-stop / stale-stop hardening around the operator-runtime path)
3. **App.web family:** Switch back to the shipped release-candidate surface (bounded investigation-quality slice)

## Recommendation
- `RECOMMEND: implement controller-office-agent-movement-fatigue-polish`
- **Next Slice:** Formalize and verify the Office View Agent Fatigue and Environment Interaction system (Fatigue, Coffee, Drones, Monitor FX).

## Why this beats alternatives
- **Same-family user-visible improvement (Priority 2):** Staying in the "Controller" family for visible polish beats switching to the new quality axis of `app.web` (Priority 3).
- **Working Tree Cleanup:** The current working tree already contains significant unorganized changes for the fatigue system, drones, and monitor FX in `controller/index.html`. This slice allows Codex to formalize and verify these changes, satisfying the `verify` report's warning about the messy tree state.
- **Risk Evaluation:** Choice 2 (Hardening) is deferred as the recent `needs_operator` stale stop at seq 187 appears to be a one-off environmental flake or model mistake rather than a systemic repo risk that should take precedence over visual polish.

## Scope Limits
- **Files:** `controller/index.html`
- **Features:** Agent fatigue state machine (working → tired → coffee → ready), waypoint-based movement with speed scaling (fatigued = 0.6x speed), drone delivery triggers on state transition, and monitor matrix/hologram FX.
- **Exclusion:** Leave `supervisor.py` and `watcher_core.py` changes out of this slice unless they are directly required for verification; otherwise, revert them to keep the implement slice narrow.

## Verification
- `make controller-test` (regression check for storage warnings)
- Visual/State verification: Ensure agents move to the coffee machine when fatigued and drones spawn on `working` state transition.
- **Narrowest required verification:** Add a basic Playwright assertion for `agent-card` fatigue property or a similar UI indicator if possible.

## Handoff
- Codex can write `.pipeline/claude_handoff.md` directly based on this advice.
