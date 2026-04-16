# Controller Office View projectH Adaptation Plan

> For agentic workers: keep this as a bounded `controller/index.html` refinement plan. Do not promote controller tooling into the shipped `app.web` release gate, and do not introduce a new runtime truth path outside the existing controller HTTP API.

**Goal:** Adapt the "live office map" idea from [`office-for-claude-agents`](https://github.com/percheniy/office-for-claude-agents/blob/main/README_EN.md) into a projectH-specific `3-lane war-room` for `controller/index.html`, while preserving local-first behavior, approval-first operator UX, and thin-client read-model boundaries.

**Architecture:** `controller/index.html` remains a browser read-model over `/api/runtime/status`, `/api/runtime/capture-tail`, and bounded `/api/runtime/*` commands. `controller/server.py` remains an API and asset shim only. Visual changes must not create a new status authority, new file-scan truth path, or arbitrary shell execution.

## Current Baseline

- `controller/index.html` already contains:
  - `Office View` toggle
  - fixed Claude / Codex / Gemini desk scene
  - HUD chips, `needs_operator` alert banner, event log, zoom / pan, modal inspection
  - sprite-manifest path, raw sheet fallback, CSS avatar fallback
  - typed runtime command palette mapped to bounded runtime commands
- `controller/server.py` already serves:
  - `/api/runtime/status`
  - `/api/runtime/capture-tail`
  - `/api/runtime/start|stop|restart`
  - `/controller-assets/*`
- `scripts/build_office_sprites.py` already generates `controller/assets/generated/office-sprite-manifest.json` and normalized frame PNG assets.
- Current shipped release candidate is still `python3 -m app.web`; controller runtime tooling remains outside the release gate as internal/operator tooling.

## What To Borrow From The External Reference

- a live visual map instead of only pane text dumps
- approval / attention alerts that are easy to notice
- event and side-panel context visible at a glance
- zoom / pan / fit interactions for a larger scene
- optional sprite asset pipeline with graceful fallback when assets are absent
- agent inspection from the main scene without opening a separate app

## What Not To Copy Directly

- boss seat or strict spawn-hierarchy metaphors
- GitHub TASKS sidebar as a required surface
- public share links, relay / tunnel sharing, spectator mode
- multi-daemon / remote office aggregation
- token or cost dashboards as the primary surface
- layout editor / import-export as the first slice
- any session-root watcher that becomes a second truth path outside supervisor runtime status

## projectH Adaptation Rules

1. Keep the visual model as a `3-lane war-room`, not a generic agent zoo.
2. Treat Claude / Codex / Gemini as equal pipeline stations with distinct roles:
   - Claude = implement lane
   - Codex = verify / follow-up lane
   - Gemini = advisory lane
3. Represent watcher as room infrastructure or inspector state, not as a fourth peer desk.
4. Preserve `needs_operator`, degraded state, active control, latest `/work`, latest `/verify`, and last receipt as first-class operator signals.
5. Keep the command palette bounded to existing controller API verbs only.
6. Keep sprite support local-only and optional; missing or low-quality assets must fall back cleanly.
7. Do not let the office scene outrank text/tail truth; Office View and text panes must remain two renderings of the same payload.

## Desired Outcome

After this slice, `controller/index.html` should read as a projectH runtime dashboard rather than a generic pixel-office homage:

- the main scene should communicate current round control and lane role clearly
- approval / stop / degraded signals should be visible without hunting
- latest round artifacts should be easier to inspect from the office inspector
- asset quality should improve when generated sprites are present, but the UI should remain usable without them
- all of the above should remain a thin read-model over the current runtime API

## File Scope

| File | Role | Expected Change |
|------|------|-----------------|
| `controller/index.html` | primary Office View rendering, HUD, inspector, event UX | main implementation surface |
| `controller/server.py` | controller API and asset shim | only if a small read-model field or asset route gap is discovered |
| `scripts/build_office_sprites.py` | generated sprite normalization pipeline | optional refinement if current framing / scale still feels unstable |
| `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md` | runtime UI boundary and Office View contract | update if read-model or asset rules change |
| `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md` | operator usage, sprite build flow, command palette | update if operator steps or command behavior change |
| `README.md` | top-level run instructions | update only if controller launch or usage instructions change materially |

## Implementation Plan

### Task 1. Reframe The Scene As projectH Runtime Operations

- [ ] Keep `Office View` optional and make it explicit that it is a read-model over runtime status.
- [ ] Remove any remaining impression that the room is modeling arbitrary agent hierarchy or a generic office.
- [ ] Keep working / booting lanes anchored to their projectH desk semantics, while non-working lanes may browser-locally roam between predefined room floor anchors without changing runtime truth.
- [ ] Surface `active_control_status`, current round state, watcher health, latest `/work`, latest `/verify`, and last receipt as the main room context instead of decorative metrics.

**Acceptance note:** The scene should explain the current automation state even when the operator never opens a pane tail.

### Task 2. Strengthen Operator-First Signals

- [ ] Make `needs_operator` the strongest visual interrupt in the room.
- [ ] Distinguish representative `degraded_reason` from the full `degraded_reasons` list without collapsing them into one vague warning.
- [ ] Keep lane status, current note, and recent tail preview consistent between Office View, left agent list, and pane view.
- [ ] Make room copy emphasize approval, verification, and round progression rather than ambient "team activity".

**Acceptance note:** urgent operator action should be more legible than sprite polish or general ambience.

### Task 3. Tighten The Read-Model Contract

- [ ] Keep Office View and pane view sourced from the same `poll()` payload and the same `hydrateTail()` path.
- [ ] Do not add controller-side file scanning, pane parsing, or local status derivation.
- [ ] If an additional signal is truly needed, add it to controller runtime payload deliberately rather than inferring it in the browser.
- [ ] Keep browser actions mapped only to the existing bounded controller HTTP surface (`/api/runtime/status`, `/api/runtime/capture-tail`, `/api/runtime/start|stop|restart`).

**Acceptance note:** no new truth path appears in the browser layer.

### Task 4. Harden The Asset Path Without Making It Mandatory

- [ ] Keep generated-manifest assets as the preferred path.
- [ ] Preserve raw sprite-sheet crop / trim as fallback only.
- [ ] Preserve CSS avatar fallback for zero-asset operation.
- [ ] If animation jitter remains visible, fix viewport normalization or generated frames before adding more scene complexity.
- [ ] Keep asset provenance local and explicit; do not add networked asset fetch or public-share assumptions.

**Acceptance note:** better assets improve the scene, but missing assets never break controller usability.

### Task 5. Polish Interaction Boundaries

- [ ] Keep zoom / pan / fit-screen ergonomics stable on desktop.
- [ ] Keep desk click inspection lightweight and grounded in runtime data.
- [ ] Avoid new modal workflows for routine operator decisions that already belong in the main inspector or command palette.
- [ ] If local persistence is added for `Office View` toggle or selected lane, keep it browser-local only and never treat it as shared runtime state.

**Acceptance note:** interaction polish should reduce operator friction without expanding the product surface.

## Idea Directives

Use the following directives when translating the operator's feature ideas into bounded controller work. Each item must remain a thin browser read-model over the canonical runtime payload.

### Idea 1. Data Delivery Visualization

- Treat the handoff as a visual echo of existing runtime transitions, not as a new authority path.
- Drive it from payload already present in `poll()`: lane state changes, `control.active_control_seq`, latest `/work`, latest `/verify`, and receipt metadata.
- Preferred rendering is a short-lived local asset or particle that travels from one desk to another; if assets are missing, fall back to a simple emoji or text particle.
- Keep the animation one-shot and decorative. It must not become a new click target, modal flow, or persisted scene object.
- Do not add browser-side file scanning or lane log parsing to "discover" handoffs.

**Acceptance note:** operators can feel the pass-off between lanes without changing runtime truth or inventing new causality.

### Idea 2. Drag-And-Drop Control

- Planning only for now. Do not expose draggable pause/resume affordances in the current slice.
- Current controller contract does not provide lane-level `pause` / `resume` / `restart` authority, so the UI must not fake those actions locally.
- If this is picked up later, add the backend contract first: explicit audited routes, canonical lane-state confirmation, failure handling, and matching runtime docs.
- Any future drag/drop animation must wait for canonical `/api/runtime/status` confirmation before it settles into a new visible control state.
- Until that backend exists, keep related affordances hidden or clearly disabled.

**Acceptance note:** no interactive control surface promises lane lifecycle actions that the runtime cannot actually honor.

### Idea 3. Weather And Time

- Keep weather, rain, and room-light changes decorative only; they must never become a second status channel that outranks text badges or runtime fields.
- Reuse the current Office View canvas and background fallback path instead of introducing a separate rendering app.
- Let lighting follow browser-local time if desired, but do not infer workload from untrusted heuristics such as pane text or event count.
- Particle density must stay low enough that lane labels, runtime badges, and modal text remain readable on narrow viewports.
- Provide a clean low-motion or off path if the effect starts to compete with readability or frame stability.

**Acceptance note:** the room can feel more alive while the runtime meaning still comes entirely from the controller payload.

### Idea 4. Office Pet

- Keep the pet as one browser-local NPC with no workflow authority.
- The pet may react to lane state visually, but it must never block desk clicks, alter runtime state, or stand in for watcher/control truth.
- Use one local asset family only; if the asset is absent, fall back to a minimal placeholder rather than widening the asset pipeline.
- Keep motion sparse and lightweight. Simple patrol, sofa nap, or broken-lane cleanup beats full pathfinding complexity.
- If the pet reacts to `BROKEN` or `DEGRADED`, make that clearly decorative and secondary to the actual runtime badges.

**Acceptance note:** the pet adds ambient character without making the controller harder to read or slower to use.

### Idea 5. Typing And Ambient Audio

- Extend the existing `SoundFX` / Web Audio layer rather than adding a new audio runtime or remote media dependency.
- Audio must start only after explicit browser interaction. No autoplay on load.
- Add a local mute control if ambient sound becomes persistent enough to matter, and keep that preference browser-local only.
- Base the mix on lane states already rendered in the UI. For example, more `working` lanes can slightly raise typing texture while idle leaves only a faint room tone.
- Keep sound strictly supplemental. Status meaning must still be available with audio muted.

**Acceptance note:** sound deepens the "office is alive" feeling without becoming required for operator awareness.

## Recommended Rollout Order

1. `Idea 1. Data Delivery Visualization`
2. `Idea 3. Weather And Time`
3. `Idea 4. Office Pet`
4. `Idea 5. Typing And Ambient Audio`
5. `Idea 2. Drag-And-Drop Control` only after lane-level backend authority exists

## Explicit Non-Goals

- turning controller tooling into the public product identity
- adding autonomous actions, arbitrary shell execution, or hidden write paths
- recreating the full `office-for-claude-agents` feature set
- adding GitHub issue tracking, public share links, or multi-daemon coordination
- introducing layout editing, seat hierarchy rules, or new operator workflow authority
- widening the release gate from `app.web` to controller tooling

## Verification Plan

Run the narrowest checks that match the actual implementation slice:

1. `python3 -m py_compile controller/server.py`
2. manual controller smoke:
   - start controller locally
   - confirm `/controller` loads
   - confirm pane view and Office View both render the same lane set
   - confirm `needs_operator` / degraded / latest artifact surfaces react to the runtime payload
3. if controller actions or Office View interactions change:
   - exercise `/api/runtime/start`, `/api/runtime/stop`, `/api/runtime/restart`, and log-tail inspection through `/api/runtime/capture-tail`
4. if sprite handling changes:
   - run `python3 scripts/build_office_sprites.py`
   - refresh controller and confirm generated path, raw-sheet fallback, and CSS fallback all remain usable

If the controller browser contract changes materially, add or update targeted tests rather than jumping straight to unrelated full-suite reruns.

## Doc Sync Triggers

Update these docs in the same implementation round if the behavior actually changes:

- `docs/projectH_pipeline_runtime_docs/03_기술설계_명세서.md`
  - if Office View contract, asset precedence, or read-model boundaries change
- `docs/projectH_pipeline_runtime_docs/05_운영_RUNBOOK.md`
  - if sprite build flow, command palette usage, or operator inspection flow changes
- `README.md`
  - only if controller launch or access instructions materially change

Do **not** update product-scope docs such as `docs/PRODUCT_SPEC.md` or `docs/MILESTONES.md` unless controller tooling is explicitly promoted into the shipped release gate.

## Open Questions

1. Should the watcher remain inspector-only, or should it become one small in-room ops-core object with no peer-agent framing?
2. Is browser-local persistence for `Office View` toggle and selected lane worth the added UX state, or should the controller stay purely stateless between refreshes?
3. Do we want a small controller-only smoke test later, or is manual runtime smoke sufficient while this remains internal tooling?

## Suggested First Slice For Claude

If Claude picks this up next, start with the smallest coherent reviewable bundle:

1. reframe existing Office View copy and inspector hierarchy around projectH runtime concepts
2. strengthen `needs_operator` / degraded / latest artifact visibility
3. leave sprite generation and deeper animation cleanup for a follow-up unless they block readability now

That ordering keeps the first round user-visible for operators without widening the controller contract.
