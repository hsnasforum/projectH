# Pipeline Office Spatial UX Design

> DeskRPG-inspired "spatial operator console" for the Pipeline Office controller.

## Summary

Transform the existing controller/index.html from a free-roaming cyberpunk canvas into a **zone-first isometric minimal operator console** where spatial layout encodes runtime semantics. Agents are bound to their desk zones; movement between zones is reserved for meaningful pipeline events. The monolithic 2,886-line HTML is decomposed into ES modules.

## Decisions Record

| Item | Decision |
|------|----------|
| Canvas approach | Zone-first redesign — agents belong to desk zones |
| Desk interaction | Slide-in Dashboard panel (right side, 320px) |
| Sidebar | Tab-based switching + event log pinned at bottom |
| Incident display | Dedicated incident zone + subtle full glow on BROKEN only |
| Delivery animation | Mixed — important events: agent walks; routine: packet fly |
| Receipt/Archive | Canvas objects + sidebar tab linkage |
| Visual tone | Isometric minimal — CSS/SVG background, keep agent sprites |
| Architecture | Module-first — split into css/js files, no bundler |

---

## 1. Zone Architecture

### 1.1 Zone Map

Canvas size: 1000 x 700px. Six semantic zones arranged in two rows.

```
ZONE_MAP = {
  claude_desk:   { x:20,  y:40,  w:280, h:250, role:"implement",  color:"#34d399", agent:"Claude"  },
  codex_desk:    { x:360, y:40,  w:280, h:250, role:"verify",     color:"#60a5fa", agent:"Codex"   },
  gemini_desk:   { x:700, y:40,  w:280, h:250, role:"advisory",   color:"#fbbf24", agent:"Gemini"  },
  receipt_board: { x:20,  y:340, w:300, h:150, role:"receipt",     color:"#a78bfa", agent:null      },
  archive_shelf: { x:360, y:340, w:300, h:150, role:"archive",    color:"#818cf8", agent:null      },
  incident_zone: { x:700, y:340, w:280, h:150, role:"incident",   color:"#ef4444", agent:null      },
}
```

**Row 1 (y:40–290):** Agent desk zones — Claude (implement), Codex (verify), Gemini (advisory).  
**Delivery corridor (y:290–340):** Horizontal passage for agent movement and packet transit.  
**Row 2 (y:340–490):** Object zones — receipt board, archive shelf, incident zone.  
**Bottom bar (y:676–700):** Canvas-internal runtime status strip.

### 1.2 Agent–Zone Binding

- Each agent's **home position** = center of their desk zone.
- Idle behavior: micro-movement within ±15px of home (zone-bounded).
- Cross-zone movement only on high-importance events (handoff, verify result, needs_operator).
- Movement path: home → zone bottom edge → corridor → destination zone edge → destination center → reverse path home.

### 1.3 Zone → Runtime State Mapping

| Zone | Runtime fields | Active when |
|------|---------------|-------------|
| claude_desk | `lanes[Claude].state`, `control.active_control_status=="implement"` | Claude lane not OFF |
| codex_desk | `lanes[Codex].state`, verify job_state | Codex lane active |
| gemini_desk | `lanes[Gemini].state`, gemini control files | Gemini lane active |
| receipt_board | `last_receipt`, `last_receipt_id` | Receipt exists |
| archive_shelf | `artifacts.latest_work`, `artifacts.latest_verify` | artifact mtime > 0 |
| incident_zone | `runtime_state`, `degraded_reasons`, `watcher.alive` | Any of: degraded, broken, needs_operator, watcher dead |

---

## 2. Module Structure

### 2.1 File Layout

```
controller/
├── index.html              # HTML structure only (~200 lines)
├── css/
│   └── office.css          # All styles + zone theme + isometric background
├── js/
│   ├── config.js           # ZONE_MAP, LANE_ROLES, color constants, poll interval
│   ├── state.js            # Runtime status polling, change detection, event ring buffer
│   ├── canvas.js           # Canvas render loop, background, zone boundaries/labels
│   ├── agents.js           # Agent sprites, movement, fatigue, idle roam
│   ├── zones.js            # Zone highlight, click handlers, object rendering (board/shelf)
│   ├── delivery.js         # Agent walk delivery + packet animation
│   ├── sidebar.js          # Tab switching, card rendering, event log
│   ├── panel.js            # Slide-in desk dashboard panel
│   └── audio.js            # Background ambient sound (existing logic)
└── assets/                 # Existing sprites/GIFs (unchanged)
```

### 2.2 Module Dependencies

```
config.js  ← no dependencies (constants)
state.js   ← config.js
canvas.js  ← config.js, state.js, zones.js, agents.js
agents.js  ← config.js, state.js
zones.js   ← config.js, state.js
delivery.js← config.js, state.js, agents.js, zones.js
sidebar.js ← config.js, state.js
panel.js   ← config.js, state.js, sidebar.js
audio.js   ← config.js, state.js
```

### 2.3 Global State Management

- `state.js` exports a singleton `PipelineState` object.
- Other modules import `PipelineState` for read access.
- State change subscription: `PipelineState.onChange(callback)`.
- ES modules (`<script type="module">`), no bundler.
- Existing global variables (`runtimeStatus`, `agents`, `eventLog`) replaced by `PipelineState` properties.

---

## 3. Sidebar + Slide-in Panel

### 3.1 Tab-based Sidebar (260px)

```
┌─────────────────────────┐
│ [Agents] [Round] [Artifacts] [Incidents]  ← tab bar (32px)
├─────────────────────────┤
│                         │
│   (active tab content)  │  ← scrollable area
│                         │
├─────────────────────────┤
│ ● 12:03 Claude WORKING  │  ← event log (pinned, 150px)
│ ● 12:02 receipt passed   │
│ ● 12:01 Codex READY      │
└─────────────────────────┘
```

**Tabs:**
- **Agents:** 3 agent cards (state dot, role label, note truncated 50ch, fatigue bar).
- **Round:** current round state, control_seq, active_control_file, control_status.
- **Artifacts:** receipt card (receipt_id, verify_result badge) + latest work/verify (basename, relative mtime).
- **Incidents:** degraded_reasons list, watcher status, autonomy block_reason, decision_required.

**Auto-switch rules:**
- Incident occurs (degraded/broken/needs_operator) → auto-switch to Incidents tab + red badge on tab icon.
- Receipt board or archive shelf clicked on canvas → auto-switch to Artifacts tab.
- Desk zone clicked → opens slide-in panel (tabs unchanged).

### 3.2 Slide-in Desk Dashboard (320px)

Opens from right edge when a desk zone is clicked. Overlays the sidebar.

```
┌──────────────────────────────┐
│ ✕  Claude Desk Dashboard     │  header + close
├──────────────────────────────┤
│ State: WORKING    PID: 1234  │
│ Fatigue: ██████░░ 72%        │
│ Last event: 12:03:41         │
├──────────────────────────────┤
│ Current Control              │
│ claude_handoff.md SEQ#287    │
│ STATUS: implement            │
├──────────────────────────────┤
│ Terminal Tail (last 15 lines)│
│ ┌──────────────────────────┐ │
│ │ > Running verify...      │ │
│ │ > Check passed           │ │
│ └──────────────────────────┘ │
├──────────────────────────────┤
│ Latest Artifact              │
│  2026-04-17-...-work.md     │
├──────────────────────────────┤
│ [____input________________]  │  1-line input
└──────────────────────────────┘
```

- **Real-time update:** Lane info refreshed on each 1s poll cycle.
- **Terminal tail:** `/api/runtime/capture-tail` called once on open, then every 10s while panel is open.
- **Input:** Uses existing `/api/runtime/send-input` API.

---

## 4. Delivery System

### 4.1 Event Classification

| Importance | Trigger | Animation |
|-----------|---------|-----------|
| **high** | `control.active_control_status` changed | Agent walks to destination |
| **high** | `last_receipt_id` changed | Agent walks to receipt board |
| **high** | `artifacts.*.mtime` changed | Agent walks to archive shelf |
| **low** | Lane `state` changed | Small packet + zone glow |
| **low** | Lane `note` changed | Packet only (no glow) |
| **none** | Heartbeat, same state | No animation |

### 4.2 Agent Walk Delivery (high events)

1. Source agent pauses at desk (0.3s) + document pickup particle.
2. Moves to corridor (L-path: zone bottom → corridor center).
3. Moves along corridor to destination zone entrance.
4. Enters destination zone center, pause (0.3s) for document drop.
5. Returns home via reverse path.

- Speed: existing `MOVE_SPEED` (2.5px/frame).
- Speech bubble icon above agent during transit: context-dependent emoji + label.
- Collision avoidance: ±10px y-offset when 2+ agents share corridor segment.

### 4.3 Packet Animation (low events)

- Small icon (12px) flies in straight line from source zone center to destination zone center.
- Duration: 0.8s.
- On arrival: destination zone border glows for 0.5s in zone color.

### 4.4 Delivery Route Map

```
implement handoff      → canvas left edge → Claude desk (document flies in from offscreen)
verify complete        → Codex desk → receipt board (agent walks)
advice_ready           → Gemini desk → Codex desk (agent walks)
new work artifact      → Claude desk → archive shelf (agent walks)
new verify artifact    → Codex desk → archive shelf (agent walks)
needs_operator         → owner agent → incident zone (agent walks, stays)
lane state change      → within-zone packet
```

---

## 5. Incident Zone System

### 5.1 Severity Levels

```
SEVERITY_MAP = {
  normal:       { bg: "transparent",            border: "none",           sidebarForce: false },
  degraded:     { bg: "rgba(251,191,36,0.08)",  border: "#fbbf24 solid",  sidebarForce: false },
  needs_op:     { bg: "rgba(251,191,36,0.12)",  border: "#fbbf24 pulse",  sidebarForce: true  },
  broken:       { bg: "rgba(239,68,68,0.15)",   border: "#ef4444 pulse",  sidebarForce: true  },
  watcher_dead: { bg: "rgba(153,27,27,0.2)",    border: "#991b1b pulse",  sidebarForce: true  },
}
```

### 5.2 Behavior

- **normal:** Empty zone, dashed border only.
- **degraded:** Zone background amber, `degraded_reasons` text rendered.
- **needs_operator:** Zone border amber pulse + sidebar auto-switch to Incidents + badge.
- **broken:** Zone border red pulse + canvas-wide subtle red glow (`box-shadow`) + sidebar forced switch.
- **watcher_dead:** Zone shows `WATCHER DEAD` label + canvas subtle glow.

### 5.3 Agent Movement

- On `needs_operator`: the control owner agent walks to incident zone and waits there.
- On resolution: agent returns to home desk.
- On `broken` lane: agent stays at desk playing BROKEN sprite (no movement).

---

## 6. Visual Style — Isometric Minimal

### 6.1 Background Layer Stack

Replaces current `background.png` raster image with CSS/SVG layers:

```
Layer 1: Solid base          #0a0c14
Layer 2: Isometric grid      SVG <pattern> diamond lattice, opacity 0.04
Layer 3: Zone floor tiles    Per-zone iso tile pattern, zone color, opacity 0.06
Layer 4: Furniture objects   SVG isometric desk/shelf/board, stroke only, minimal fill
Layer 5: Zone labels         Top-left pinned: icon + name + role
Layer 6: Corridor            Dashed path indicator, opacity 0.15
```

### 6.2 Furniture Objects (Pure SVG)

- **Desk:** Isometric cuboid (top face + 2 side faces), zone-colored stroke.
- **Receipt Board:** Wall-mounted rectangle with pin icons. Shows status badge overlay.
- **Archive Shelf:** 3-tier horizontal shelves with file icons. Shows artifact count.
- **Incident Zone:** Dashed border + warning triangle icon.
- **Coffee Machine:** Kept as easter egg outside zones (decorative).

### 6.3 Color System (preserved from current)

```css
--color-working:  #34d399;   /* green  — Claude desk default */
--color-ready:    #60a5fa;   /* blue   — Codex desk default  */
--color-booting:  #fbbf24;   /* amber  — Gemini desk default */
--color-broken:   #ef4444;   /* red    */
--color-dead:     #991b1b;   /* dark red */
--color-off:      #475569;   /* slate  */
--color-receipt:  #a78bfa;   /* purple */
--color-archive:  #818cf8;   /* indigo */
```

### 6.4 Agent Sprites

Existing GIF/spritesheet system **unchanged**. Only additions:
- Small shadow ellipse below each agent for ground contact.
- **Idle state badge:** Mini tag above agent head showing current state (replaces emoji particles).
- **Transit speech bubble:** During cross-zone delivery walks, a context-dependent icon + label floats above the agent (e.g., `implement`, `passed`). Disappears on arrival. Distinct from the idle state badge.

---

## 7. Backend Changes

### 7.1 server.py (minimal)

```python
# Extend static file serving path:
# Current: controller/assets/ only
# Add:     controller/css/, controller/js/
# Add Content-Type: text/css, application/javascript

# No new API endpoints required.
```

### 7.2 Runtime Status Model

**No changes.** All data needed by the zone system is already present in `/api/runtime/status`:

- `lanes[].state/note/pid/last_event_at` → desk zones
- `control.*` → desk zones + delivery triggers
- `last_receipt` → receipt board
- `artifacts.*` → archive shelf
- `runtime_state`, `degraded_reasons`, `watcher` → incident zone

Thin-client boundary preserved.

---

## Constraints

- No Phaser, multiplayer, login, or character customization (per requirements item 6).
- No code/image assets copied from DeskRPG (per requirements item 7).
- No new backend APIs — all rendering is driven by existing `/api/runtime/status`.
- No bundler — ES modules loaded directly.
- Existing sprites and audio system preserved.
- Runtime observability rationale: every visual element maps to a specific runtime field, documented in zone→runtime mapping table.
