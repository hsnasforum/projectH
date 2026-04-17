# Pipeline Office Spatial UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the monolithic controller/index.html into a zone-first isometric operator console with modular JS/CSS, tabbed sidebar, slide-in desk dashboard, and severity-staged incident zone.

**Architecture:** Decompose the existing 2,886-line index.html into ES modules (no bundler). Replace raster background with CSS/SVG isometric grid. Add semantic zones that map to runtime state fields. Extend server.py to serve css/ and js/ directories alongside existing assets/.

**Tech Stack:** Vanilla JS (ES modules), CSS3, SVG, HTML Canvas API, existing controller/server.py (Python http.server)

**Spec:** `docs/superpowers/specs/2026-04-17-pipeline-office-spatial-ux-design.md`

---

## File Structure

```
controller/
├── index.html              # HTML skeleton (~200 lines) — MODIFY
├── css/
│   └── office.css          # All styles extracted + new zone/tab/panel styles — CREATE
├── js/
│   ├── config.js           # Constants: ZONE_MAP, LANE_ROLES, STATE_COLORS, GIF paths — CREATE
│   ├���─ state.js            # PipelineState singleton: polling, change detection, event buffer — CREATE
│   ├── canvas.js           # Canvas loop, isometric background, zone rendering — CREATE
│   ├── agents.js           # Agent class: sprites, zone-bounded movement, fatigue — CREATE
│   ├── zones.js            # Zone click handlers, object rendering (board/shelf), hit testing — CREATE
│   ├── delivery.js         # Agent walk delivery + packet animation + drone — CREATE
│   ├── sidebar.js          # Tab switching, agent cards, runtime info, event log — CREATE
│   ├── panel.js            # Slide-in desk dashboard panel — CREATE
│   └── audio.js            # AmbientAudio + SoundFX — CREATE
├── server.py               # Extend _resolve_controller_asset for css/js — MODIFY
└── assets/                 # Existing sprites/GIFs — UNCHANGED
```

**Existing tests to keep passing throughout:**
- `python3 -m unittest tests.test_controller_server -v`
- `cd e2e && npx playwright test tests/controller-smoke.spec.mjs --reporter=line`

**Key E2E selectors that must be preserved:**
- `#storage-warn`, `#status-badge`, `#project-path`
- `.agent-card[data-agent="..."]`, `.agent-fatigue[data-fatigue="..."]`
- `#event-list .event-msg`, `.event-dot`
- `#log-modal`, `#lm-*` (terminal modal elements)
- `window.setAgentFatigue`, `window.getRoamBounds`, `window.testPickIdleTargets`, `window.testAntiStacking`, `window.testHistoryPenalty` (test hooks)

---

### Task 1: Extend server.py to serve css/ and js/ directories

**Files:**
- Modify: `controller/server.py:57-70` (`_resolve_controller_asset`)
- Test: `tests/test_controller_server.py`

- [ ] **Step 1: Write failing test for css/js asset serving**

Add to `tests/test_controller_server.py`:

```python
class ControllerAssetResolutionTests(unittest.TestCase):
    def test_resolve_css_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            css_dir = Path(tmp) / "css"
            css_dir.mkdir()
            css_file = css_dir / "office.css"
            css_file.write_text("body { color: red; }")
            with mock.patch.object(controller_server, "CONTROLLER_DIR", Path(tmp)):
                asset_path, content_type = controller_server._resolve_controller_asset("css/office.css")
            self.assertIsNotNone(asset_path)
            self.assertEqual(content_type, "text/css")
            self.assertEqual(asset_path.name, "office.css")

    def test_resolve_js_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            js_dir = Path(tmp) / "js"
            js_dir.mkdir()
            js_file = js_dir / "config.js"
            js_file.write_text("export const X = 1;")
            with mock.patch.object(controller_server, "CONTROLLER_DIR", Path(tmp)):
                asset_path, content_type = controller_server._resolve_controller_asset("js/config.js")
            self.assertIsNotNone(asset_path)
            self.assertEqual(content_type, "text/javascript")
            self.assertEqual(asset_path.name, "config.js")

    def test_resolve_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(controller_server, "CONTROLLER_DIR", Path(tmp)):
                asset_path, _ = controller_server._resolve_controller_asset("../server.py")
            self.assertIsNone(asset_path)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_controller_server.ControllerAssetResolutionTests -v`
Expected: FAIL — `_resolve_controller_asset` only searches under `assets/`, not `css/` or `js/`

- [ ] **Step 3: Modify _resolve_controller_asset to search css/ and js/ too**

In `controller/server.py`, replace the `_resolve_controller_asset` function:

```python
def _resolve_controller_asset(rel_path: str) -> tuple[Path | None, str | None]:
    """Resolve a controller asset from assets/, css/, or js/ subdirectories."""
    requested = str(rel_path or "").strip().lstrip("/")
    if not requested:
        return None, None

    # Allow serving from assets/, css/, and js/ subdirectories
    allowed_roots = [
        (CONTROLLER_DIR / "assets").resolve(),
        (CONTROLLER_DIR / "css").resolve(),
        (CONTROLLER_DIR / "js").resolve(),
    ]

    # Determine which root to use based on prefix
    candidate = None
    asset_root = None
    if requested.startswith("css/") or requested.startswith("js/"):
        # Direct path under controller/
        candidate = (CONTROLLER_DIR / requested).resolve()
        asset_root = (CONTROLLER_DIR / requested.split("/")[0]).resolve()
    else:
        # Default: assets/
        candidate = (allowed_roots[0] / requested).resolve()
        asset_root = allowed_roots[0]

    if asset_root is None:
        return None, None

    # Path traversal check
    try:
        candidate.relative_to(asset_root)
    except ValueError:
        return None, None
    if not candidate.is_file():
        return None, None
    content_type = mimetypes.guess_type(str(candidate))[0] or "application/octet-stream"
    return candidate, content_type
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest tests.test_controller_server -v`
Expected: ALL PASS

- [ ] **Step 5: Create empty css/ and js/ directories with placeholder files**

```bash
mkdir -p controller/css controller/js
echo "/* Pipeline Office — spatial UX styles */" > controller/css/office.css
echo "// Pipeline Office — config constants" > controller/js/config.js
```

- [ ] **Step 6: Commit**

```bash
git add controller/server.py tests/test_controller_server.py controller/css/office.css controller/js/config.js
git commit -m "feat(controller): extend asset serving to css/ and js/ directories"
```

---

### Task 2: Extract CSS into office.css

**Files:**
- Create: `controller/css/office.css`
- Modify: `controller/index.html` (remove `<style>` block, add `<link>`)

- [ ] **Step 1: Extract all CSS from index.html into office.css**

Copy the entire content between `<style>` and `</style>` (lines 7–256 of current index.html) into `controller/css/office.css`. Preserve every selector exactly.

The file should start with:

```css
/* ═��═════════════════════════════════════ */
/* Pipeline Office — Spatial UX Styles    */
/* ════════��══════════════���═══════════════ */

/* Reset & Base */
* { margin: 0; padding: 0; box-sizing: border-box; }
html, body { width: 100%; height: 100%; overflow: hidden; }
body {
  font-family: 'Noto Sans KR', -apple-system, 'Segoe UI', sans-serif;
  background: #0a0c14; color: #cdd6e4;
}
```

...through to the final `.log-modal-send-status.ok { color: #34d399; }`.

- [ ] **Step 2: Replace `<style>` block in index.html with `<link>` tag**

In `controller/index.html`, replace the entire `<style>...</style>` block with:

```html
<link rel="stylesheet" href="/controller-assets/css/office.css">
```

The `<head>` should now be approximately:

```html
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pipeline Controller — Office</title>
<link rel="stylesheet" href="/controller-assets/css/office.css">
</head>
```

- [ ] **Step 3: Verify the page loads correctly**

Run: `python3 -m unittest tests.test_controller_server -v`
Expected: ALL PASS (server can serve the CSS file)

If possible, open `http://localhost:8780/controller` and verify visual parity.

- [ ] **Step 4: Run E2E smoke**

Run: `cd e2e && npx playwright test tests/controller-smoke.spec.mjs --reporter=line`
Expected: ALL PASS (DOM selectors unchanged, only CSS delivery changed)

- [ ] **Step 5: Commit**

```bash
git add controller/css/office.css controller/index.html
git commit -m "refactor(controller): extract CSS into controller/css/office.css"
```

---

### Task 3: Extract config.js and state.js

**Files:**
- Create: `controller/js/config.js`
- Create: `controller/js/state.js`
- Modify: `controller/index.html` (remove config/state globals, add module imports)

- [ ] **Step 1: Write config.js with all constants**

```javascript
// controller/js/config.js — Pipeline Office constants
export const POLL_MS = 1000;
export const ACTION_REPOLL_MS = 300;
export const LOG_REFRESH_MS = 1000;
export const VIRTUAL_W = 1000;
export const VIRTUAL_H = 700;
export const WALK_SPEED = 120;

export const STATE_COLORS = {
  working: '#34d399', ready: '#60a5fa', booting: '#fbbf24',
  broken: '#ef4444', dead: '#991b1b', off: '#475569', unknown: '#a78bfa',
};

export const LANE_ROLES = {
  claude: 'implement', codex: 'verify', gemini: 'advisory',
};

export const STATE_GIF_ASSETS = {
  booting: '/controller-assets/BOOTING.gif',
  working: '/controller-assets/WORKING.gif',
  broken: '/controller-assets/BROKEN.gif',
  ready: '/controller-assets/READY.gif',
  dead: '/controller-assets/DEAD.gif',
};

export const AMBIGUOUS_RUNTIME_REASON = 'supervisor_missing_recent_ambiguous';
export const UNDATED_AMBIGUOUS_RUNTIME_REASON = 'supervisor_missing_snapshot_undated';
export const UNCERTAIN_RUNTIME_REASONS = new Set([AMBIGUOUS_RUNTIME_REASON, UNDATED_AMBIGUOUS_RUNTIME_REASON]);
export const INACTIVE_RUNTIME_STATES = new Set(['STOPPED', 'STOPPING', 'BROKEN']);

export const STATE_PARTICLES = { working: '💡', ready: '💤', booting: '⚡', broken: '💦', dead: '💀', off: '🌙' };
export const EVENT_PARTICLES = { ok: '✅', warn: '❗', err: '🔥', info: '💬' };

// ── Zone-first layout ──
export const ZONE_MAP = {
  claude_desk:   { x: 20,  y: 40,  w: 280, h: 250, role: 'implement', color: '#34d399', agent: 'Claude'  },
  codex_desk:    { x: 360, y: 40,  w: 280, h: 250, role: 'verify',    color: '#60a5fa', agent: 'Codex'   },
  gemini_desk:   { x: 700, y: 40,  w: 280, h: 250, role: 'advisory',  color: '#fbbf24', agent: 'Gemini'  },
  receipt_board: { x: 20,  y: 340, w: 300, h: 150, role: 'receipt',   color: '#a78bfa', agent: null       },
  archive_shelf: { x: 360, y: 340, w: 300, h: 150, role: 'archive',   color: '#818cf8', agent: null       },
  incident_zone: { x: 700, y: 340, w: 280, h: 150, role: 'incident',  color: '#ef4444', agent: null       },
};

export const CORRIDOR_Y = { top: 290, bottom: 340 };

export const SEVERITY_MAP = {
  normal:       { bg: 'transparent',           border: 'none',          sidebarForce: false },
  degraded:     { bg: 'rgba(251,191,36,0.08)', border: '#fbbf24 solid', sidebarForce: false },
  needs_op:     { bg: 'rgba(251,191,36,0.12)', border: '#fbbf24',       sidebarForce: true  },
  broken:       { bg: 'rgba(239,68,68,0.15)',  border: '#ef4444',       sidebarForce: true  },
  watcher_dead: { bg: 'rgba(153,27,27,0.2)',   border: '#991b1b',       sidebarForce: true  },
};

// Delivery event importance classification
export const DELIVERY_IMPORTANCE = {
  control_status_changed: 'high',
  receipt_changed: 'high',
  artifact_changed: 'high',
  lane_state_changed: 'low',
  lane_note_changed: 'low',
  heartbeat: 'none',
};
```

- [ ] **Step 2: Write state.js with PipelineState singleton**

```javascript
// controller/js/state.js — Runtime state polling and change detection
import { POLL_MS, INACTIVE_RUNTIME_STATES, UNCERTAIN_RUNTIME_REASONS } from './config.js';

const MAX_EVENTS = 40;

class _PipelineState {
  constructor() {
    this.data = null;
    this.eventLog = [];
    this._listeners = [];
    this._prev = { runtimeState: null, controlStatus: null, watcherStatus: null, uncertainRuntime: null, laneStates: {} };
    this._pollInFlight = false;
    this._deliveryState = {
      initialized: false, controlSeq: null,
      latestWorkPath: '', latestWorkMtime: '',
      latestVerifyPath: '', latestVerifyMtime: '',
      lastReceiptId: '',
    };
  }

  onChange(fn) { this._listeners.push(fn); }
  _notify(changeType, detail) { for (const fn of this._listeners) fn(changeType, detail); }

  pushEvent(type, msg) {
    const t = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    this.eventLog.unshift({ type, msg, time: t });
    if (this.eventLog.length > MAX_EVENTS) this.eventLog.length = MAX_EVENTS;
    this._notify('event', { type, msg, time: t });
  }

  getPresentation(data) {
    const d = data || this.data || {};
    const runtimeState = String(d.runtime_state || 'STOPPED').toUpperCase();
    const control = d.control || {};
    const watcher = d.watcher || {};
    const round = d.active_round || {};
    const degradedReasons = (d.degraded_reasons || []).filter(Boolean);
    const degradedReason = degradedReasons[0] || String(d.degraded_reason || '').trim();
    const uncertain = runtimeState === 'DEGRADED' && degradedReasons.some(r => UNCERTAIN_RUNTIME_REASONS.has(r));
    const inactive = INACTIVE_RUNTIME_STATES.has(runtimeState);
    const showLive = !inactive && !uncertain;
    const controlStatus = showLive ? (control.active_control_status || 'none') : (uncertain ? 'uncertain' : 'none');
    const roundState = showLive ? (round.state || 'IDLE') : (uncertain ? 'uncertain' : 'IDLE');
    let watcherStatus = 'Dead', watcherClass = 'dim';
    if (uncertain) { watcherStatus = 'Unknown'; watcherClass = 'warn'; }
    else if (watcher.alive) { watcherStatus = 'Alive'; watcherClass = 'ok'; }
    else if (runtimeState === 'BROKEN') { watcherClass = 'err'; }
    else if (runtimeState === 'STOPPING') { watcherClass = 'neutral'; }
    const controlClass = controlStatus === 'implement' ? 'ok'
      : controlStatus === 'needs_operator' || controlStatus === 'uncertain' ? 'warn'
      : controlStatus === 'none' ? 'dim' : 'neutral';
    const roundClass = roundState === 'uncertain' ? 'warn' : roundState === 'IDLE' ? 'dim' : 'neutral';
    const runtimeClass = runtimeState === 'RUNNING' ? 'ok' : runtimeState === 'DEGRADED' ? 'warn'
      : runtimeState === 'STOPPING' ? 'neutral' : runtimeState === 'BROKEN' ? 'err' : 'dim';
    const badgeClass = runtimeState === 'RUNNING' ? 'running' : runtimeState === 'DEGRADED' ? 'degraded'
      : runtimeState === 'STOPPING' ? 'stopping' : runtimeState === 'BROKEN' ? 'broken' : 'stopped';
    return { runtimeState, runtimeClass, badgeClass, uncertain, inactive, controlStatus, controlClass,
      roundState, roundClass, watcherStatus, watcherClass, degradedReason, degradedReasons };
  }

  detectChanges(data) {
    const p = this.getPresentation(data);
    const rs = p.runtimeState, cs = p.controlStatus, ws = p.watcherStatus;
    const uncertaintyChanged = this._prev.uncertainRuntime !== null && this._prev.uncertainRuntime !== p.uncertain;

    if (this._prev.runtimeState !== null && this._prev.runtimeState !== rs) {
      const t = rs === 'RUNNING' ? 'ok' : rs === 'DEGRADED' ? 'warn' : rs === 'BROKEN' ? 'err' : 'info';
      this.pushEvent(t, `Runtime: ${this._prev.runtimeState} → ${rs}`);
    }
    this._prev.runtimeState = rs;
    if (uncertaintyChanged) {
      this.pushEvent(p.uncertain ? 'warn' : 'info',
        p.uncertain ? `Runtime truth uncertain: ${p.degradedReason}` : 'Runtime truth restored');
    }
    this._prev.uncertainRuntime = p.uncertain;
    if (!uncertaintyChanged && this._prev.controlStatus !== null && this._prev.controlStatus !== cs) {
      const t = cs === 'implement' ? 'ok' : cs === 'needs_operator' || cs === 'uncertain' ? 'warn' : 'info';
      this.pushEvent(t, `Control: ${this._prev.controlStatus} → ${cs}`);
      this._notify('controlChange', { from: this._prev.controlStatus, to: cs });
    }
    this._prev.controlStatus = cs;
    if (!uncertaintyChanged && this._prev.watcherStatus !== null && this._prev.watcherStatus !== ws) {
      const t = ws === 'Alive' ? 'ok' : ws === 'Unknown' ? 'warn' : 'err';
      this.pushEvent(t, `Watcher: ${this._prev.watcherStatus} → ${ws}`);
    }
    this._prev.watcherStatus = ws;
    for (const lane of (data.lanes || [])) {
      const n = lane.name || '', s = (lane.state || 'off').toLowerCase(), prev = this._prev.laneStates[n];
      if (prev !== undefined && prev !== s) {
        const t = s === 'working' ? 'ok' : (s === 'broken' || s === 'dead') ? 'err' : 'info';
        this.pushEvent(t, `${n}: ${prev} → ${s}`);
        this._notify('laneChange', { name: n, from: prev, to: s });
      }
      this._prev.laneStates[n] = s;
    }
  }

  checkDeliveryTriggers(data) {
    const ds = this._deliveryState;
    const seq = (data.control || {}).active_control_seq;
    const artifacts = data.artifacts || {};
    const wP = String((artifacts.latest_work || {}).path || '').trim();
    const wM = String((artifacts.latest_work || {}).mtime || '').trim();
    const vP = String((artifacts.latest_verify || {}).path || '').trim();
    const vM = String((artifacts.latest_verify || {}).mtime || '').trim();
    const rId = String(data.last_receipt_id || ((data.last_receipt || {}).receipt_id) || '').trim();

    if (!ds.initialized) {
      Object.assign(ds, { initialized: true, controlSeq: seq, latestWorkPath: wP, latestWorkMtime: wM, latestVerifyPath: vP, latestVerifyMtime: vM, lastReceiptId: rId });
      return;
    }
    const triggers = [];
    if (seq != null && seq >= 0 && ds.controlSeq !== null && seq !== ds.controlSeq) {
      triggers.push({ type: 'control', status: (data.control || {}).active_control_status || '', seq });
    }
    if (wP && wP !== '—' && ds.latestWorkPath && (wP !== ds.latestWorkPath || (wM && wM !== ds.latestWorkMtime))) {
      triggers.push({ type: 'work', path: wP });
    }
    if (vP && vP !== '—' && ds.latestVerifyPath && (vP !== ds.latestVerifyPath || (vM && vM !== ds.latestVerifyMtime))) {
      triggers.push({ type: 'verify', path: vP });
    }
    if (ds.lastReceiptId && rId && rId !== ds.lastReceiptId) {
      triggers.push({ type: 'receipt', id: rId });
    }
    Object.assign(ds, { controlSeq: seq, latestWorkPath: wP, latestWorkMtime: wM, latestVerifyPath: vP, latestVerifyMtime: vM, lastReceiptId: rId });
    if (triggers.length) this._notify('delivery', triggers);
  }

  async poll() {
    if (this._pollInFlight) return;
    this._pollInFlight = true;
    try {
      const res = await fetch('/api/runtime/status');
      const data = await res.json();
      this.data = data;
      this.detectChanges(data);
      this.checkDeliveryTriggers(data);
      this._notify('poll', data);
    } catch (e) {
      this._notify('pollError', e);
    } finally { this._pollInFlight = false; }
  }

  startPolling() {
    this.poll();
    setInterval(() => this.poll(), POLL_MS);
  }
}

export const PipelineState = new _PipelineState();
```

- [ ] **Step 3: Verify modules parse correctly**

Run: `node --check controller/js/config.js && node --check controller/js/state.js && echo "OK"`
Expected: OK (no syntax errors)

- [ ] **Step 4: Commit**

```bash
git add controller/js/config.js controller/js/state.js
git commit -m "feat(controller): add config.js and state.js ES modules"
```

---

### Task 4: Extract audio.js

**Files:**
- Create: `controller/js/audio.js`

- [ ] **Step 1: Write audio.js**

Extract `SoundFX`, `AmbientAudio`, and `PrefStore` from index.html:

```javascript
// controller/js/audio.js — Sound effects and ambient audio

export const PrefStore = (() => {
  let _available = null;
  let _eventCallback = null;
  function _probe() {
    if (_available !== null) return _available;
    try {
      const k = '__office_storage_probe__';
      localStorage.setItem(k, '1');
      localStorage.removeItem(k);
      _available = true;
    } catch (e) {
      _available = false;
      if (_eventCallback) _eventCallback('warn', '환경 설정 저장 불가 — 새로고침 시 toolbar 설정이 초기화됩니다');
    }
    return _available;
  }
  return {
    get(key) { return _probe() ? localStorage.getItem(key) : null; },
    set(key, val) { if (_probe()) localStorage.setItem(key, val); },
    get available() { return _probe(); },
    setEventCallback(fn) { _eventCallback = fn; },
  };
})();

export const SoundFX = {
  _ctx: null, _enabled: true,
  _ensure() {
    if (!this._ctx) { try { this._ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { this._enabled = false; } }
    if (this._ctx && this._ctx.state === 'suspended') this._ctx.resume();
    return this._ctx;
  },
  _play(notes, { gain = 0.12, type = 'square' } = {}) {
    if (!this._enabled) return; const ctx = this._ensure(); if (!ctx) return;
    const now = ctx.currentTime, osc = ctx.createOscillator(), vol = ctx.createGain();
    osc.type = type; osc.connect(vol); vol.connect(ctx.destination);
    let t = now;
    for (const [freq, dur] of notes) {
      osc.frequency.setValueAtTime(freq, t); vol.gain.setValueAtTime(gain, t);
      vol.gain.setValueAtTime(gain, t + dur * 0.7); vol.gain.linearRampToValueAtTime(0, t + dur); t += dur;
    }
    osc.start(now); osc.stop(t);
  },
  click()   { this._play([[880, 0.06]], { gain: 0.08 }); },
  success() { this._play([[523, 0.08], [659, 0.08], [784, 0.12]], { gain: 0.10 }); },
  error()   { this._play([[220, 0.12], [165, 0.18]], { gain: 0.13, type: 'sawtooth' }); },
  warn()    { this._play([[440, 0.08], [0, 0.06], [440, 0.08]], { gain: 0.09 }); },
  blip()    { this._play([[660, 0.05]], { gain: 0.06 }); },
};

export const AmbientAudio = {
  _typingOsc: null, _typingGain: null, _toneOsc: null, _toneGain: null,
  _running: false, muted: false, _targetTypingVol: 0,

  toggle() {
    this.muted = !this.muted;
    const btn = document.getElementById('mute-btn');
    if (btn) { btn.textContent = this.muted ? '🔇' : '🔊'; btn.title = this.muted ? '사운드 켜기' : '음소거'; }
    PrefStore.set('office_muted', this.muted ? '1' : '0');
    if (this.muted) this._stop(); else this._start();
  },

  _start() {
    if (this._running || this.muted) return;
    const ac = SoundFX._ensure(); if (!ac) return;
    this._running = true;
    this._toneOsc = ac.createOscillator(); this._toneGain = ac.createGain();
    this._toneOsc.type = 'sine'; this._toneOsc.frequency.value = 85; this._toneGain.gain.value = 0.008;
    this._toneOsc.connect(this._toneGain); this._toneGain.connect(ac.destination); this._toneOsc.start();
    this._typingOsc = ac.createOscillator(); this._typingGain = ac.createGain();
    this._typingOsc.type = 'square'; this._typingOsc.frequency.value = 200; this._typingGain.gain.value = 0;
    this._typingOsc.connect(this._typingGain); this._typingGain.connect(ac.destination); this._typingOsc.start();
  },

  _stop() {
    try { this._toneOsc?.stop(); } catch(e) {}
    try { this._typingOsc?.stop(); } catch(e) {}
    this._running = false;
    this._toneOsc = null; this._typingOsc = null; this._toneGain = null; this._typingGain = null;
  },

  update(workingCount) {
    if (!this._running || this.muted) return;
    this._targetTypingVol = Math.min(0.015, workingCount * 0.005);
    if (this._typingGain) {
      const cur = this._typingGain.gain.value;
      this._typingGain.gain.value = cur + (this._targetTypingVol - cur) * 0.05;
    }
    if (this._typingOsc && Math.random() < 0.1) {
      this._typingOsc.frequency.value = 150 + Math.random() * 300;
    }
  },

  restore() {
    if (PrefStore.get('office_muted') === '1') {
      this.muted = true;
      const mb = document.getElementById('mute-btn');
      if (mb) { mb.textContent = '🔇'; mb.title = '사���드 켜기'; }
    }
  },
};
```

- [ ] **Step 2: Verify module parses**

Run: `node --check controller/js/audio.js && echo "OK"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add controller/js/audio.js
git commit -m "feat(controller): extract audio.js module (SoundFX, AmbientAudio, PrefStore)"
```

---

### Task 5: Extract agents.js with zone-bounded movement

**Files:**
- Create: `controller/js/agents.js`

- [ ] **Step 1: Write agents.js — Agent class with zone-based home positions**

This is the largest extraction. Port the `Agent` class, `SpriteManager`, and related particle systems. Key change: replace `LOCATIONS`, `NAV`, `WALKABLE_BOUNDS`, `DESK_RECTS`, and `IDLE_ROAM_SPOTS` with ZONE_MAP-based positioning.

```javascript
// controller/js/agents.js — Agent entities with zone-bounded movement
import { ZONE_MAP, CORRIDOR_Y, STATE_COLORS, LANE_ROLES, WALK_SPEED,
         STATE_GIF_ASSETS, STATE_PARTICLES, VIRTUAL_W } from './config.js';

// ── Sprite Manager ──
export const SpriteManager = {
  // ... (exact copy of existing SpriteManager from index.html lines 382-442)
  // No changes needed — sprite system is unchanged
  manifest: null, stateGifs: {}, frames: {}, sequences: {}, loaded: false,

  async init() {
    for (const [state, src] of Object.entries(STATE_GIF_ASSETS)) {
      const img = new Image(); img.src = src; this.stateGifs[state] = img;
    }
    this.stateGifs.off = this.stateGifs.dead || null;
    this.stateGifs.idle = this.stateGifs.ready || null;
    this.stateGifs.unknown = this.stateGifs.ready || null;
    try {
      const res = await fetch('/controller-assets/generated/office-sprite-manifest.json');
      this.manifest = await res.json();
      for (const [state, config] of Object.entries(this.manifest.states || {})) {
        this.frames[state] = (config.frames || []).map(f => { const img = new Image(); img.src = f.src; return img; });
        this.sequences[state] = { sequence: config.sequence || [0], intervalMs: config.interval_ms || 180 };
      }
      this.frames.off = this.frames.dead || []; this.frames.idle = this.frames.ready || []; this.frames.unknown = this.frames.ready || [];
      this.sequences.off = this.sequences.dead || this.sequences.ready;
      this.sequences.idle = this.sequences.ready; this.sequences.unknown = this.sequences.ready;
      this.loaded = true;
    } catch (e) { this.loaded = false; }
  },

  getAgentFrame(state, timeSeconds) {
    const gif = this.stateGifs[state] || this.stateGifs.ready || null;
    if (gif && gif.complete && gif.naturalWidth > 0) return gif;
    const frames = this.frames[state] || this.frames.ready || [];
    const seq = this.sequences[state] || this.sequences.ready;
    if (!frames.length || !seq) return null;
    const idx = Math.floor((timeSeconds * 1000 / seq.intervalMs) % seq.sequence.length);
    const frameIdx = seq.sequence[idx] || 0;
    const img = frames[frameIdx];
    return (img && img.complete && img.naturalWidth > 0) ? img : null;
  }
};

// ── Zone helpers ──
function zoneCenter(zoneKey) {
  const z = ZONE_MAP[zoneKey];
  return z ? { x: z.x + z.w / 2, y: z.y + z.h / 2 } : { x: 500, y: 350 };
}

function agentHomeZone(name) {
  const key = `${name.toLowerCase()}_desk`;
  return ZONE_MAP[key] ? key : null;
}

function clampToZone(px, py, zoneKey) {
  const z = ZONE_MAP[zoneKey];
  if (!z) return { x: px, y: py };
  return {
    x: Math.max(z.x + 10, Math.min(z.x + z.w - 10, px)),
    y: Math.max(z.y + 10, Math.min(z.y + z.h - 10, py)),
  };
}

// ── Particles (shared) ──
export const particles = [];

export class Particle {
  constructor(vx, vy, text, opts = {}) {
    this.vx = vx + (Math.random() - 0.5) * 14; this.vy = vy - 30;
    this.text = text; this.color = opts.color || '#e2e8f0';
    this.lifetime = opts.lifetime || 1.6; this.maxLife = this.lifetime;
    this.size = opts.size || 16;
    this.driftX = (Math.random() - 0.5) * 12; this.driftY = -(25 + Math.random() * 15);
    this.alive = true;
  }
  update(dt) { this.vx += this.driftX * dt; this.vy += this.driftY * dt; this.lifetime -= dt; if (this.lifetime <= 0) this.alive = false; }
  draw(ctx, scale) {
    const alpha = Math.max(0, this.lifetime / this.maxLife);
    const sx = this.vx * scale, sy = this.vy * scale, sz = this.size * scale;
    ctx.save(); ctx.globalAlpha = alpha; ctx.font = `${sz}px sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    const lifeFrac = 1 - (this.lifetime / this.maxLife);
    const pop = lifeFrac < 0.15 ? 1 + (0.15 - lifeFrac) * 3 : 1;
    ctx.translate(sx, sy); ctx.scale(pop, pop);
    ctx.fillStyle = 'rgba(0,0,0,0.4)'; ctx.fillText(this.text, 1, 1);
    ctx.fillStyle = this.color; ctx.fillText(this.text, 0, 0);
    ctx.restore();
  }
}

function truncate(s, n) { return s.length > n ? s.slice(0, n) + '…' : s; }

// ── Agent Map (shared) ──
export const agents = new Map();

export function spawnParticle(agentName, text, opts) {
  const agent = agents.get(agentName);
  if (!agent) return;
  particles.push(new Particle(agent.x, agent.y, text, opts));
}

export function spawnStateParticle(agentName, newState) {
  spawnParticle(agentName, STATE_PARTICLES[newState] || '❓', { size: 20, lifetime: 1.8 });
}

// ── Agent class (zone-bounded) ──
export class Agent {
  constructor(name) {
    this.name = name;
    this.role = LANE_ROLES[name.toLowerCase()] || '';
    this.state = 'off'; this.note = ''; this.pid = null; this.lastEventAt = '';
    // Start at home zone center
    const home = zoneCenter(agentHomeZone(name) || 'claude_desk');
    this.x = home.x; this.y = home.y; this.facingRight = true;
    this._homeZone = agentHomeZone(name);
    this._waypoints = []; this._atTarget = true;
    this.bobPhase = Math.random() * Math.PI * 2; this.blinkTimer = Math.random() * 3;
    this.isBlinking = false; this.movePhase = 0;
    this.bubble = { text: '', timer: 0 };
    this._idleCooldown = 0; this._glanceCooldown = 0; this._staleTimer = 0;
    this.fatigue = 0; this._fatigueSweatTimer = 0; this._coffeeTimer = 0; this._atCoffee = false;
    // Delivery walk state
    this._delivering = false; this._deliveryIcon = '';
    // GIF overlay
    this._gifEl = document.createElement('img');
    this._gifEl.style.cssText = 'position:absolute;pointer-events:none;image-rendering:pixelated;z-index:10;display:none;';
    this._gifState = '';
    document.querySelector('.canvas-wrap')?.appendChild(this._gifEl);
  }

  get color() { return STATE_COLORS[this.state] || STATE_COLORS.off; }
  get fatigueState() {
    if (this._atCoffee) return 'coffee';
    if (this.state === 'working' && this.fatigue >= 15) return 'fatigued';
    return '';
  }

  speak(text, duration = 3.5) { if (text) this.bubble = { text: truncate(text, 25), timer: duration }; }

  applyLaneData(lane, soundFX) {
    const prevState = this.state, prevNote = this.note;
    this.state = (lane.state || 'off').toLowerCase();
    this.note = lane.note || lane.status_note || '';
    this.pid = lane.pid || null; this.lastEventAt = lane.last_event_at || '';
    if (prevState !== this.state) {
      this._pickTarget();
      if (prevState !== 'off') {
        spawnStateParticle(this.name, this.state);
        if (soundFX) {
          if (this.state === 'working') soundFX.success();
          else if (this.state === 'broken' || this.state === 'dead') soundFX.error();
          else soundFX.blip();
        }
      }
    }
    if (this.note && prevNote !== this.note && this.state === 'working') this.speak(this.note, 4.0);
  }

  // Walk to a specific zone (for delivery)
  walkToZone(zoneKey, icon) {
    this._delivering = true;
    this._deliveryIcon = icon || '📄';
    const dest = zoneCenter(zoneKey);
    this._waypoints = [];
    // L-path via corridor
    const home = zoneCenter(this._homeZone);
    this._waypoints.push({ x: home.x, y: CORRIDOR_Y.top + (CORRIDOR_Y.bottom - CORRIDOR_Y.top) / 2 });
    this._waypoints.push({ x: dest.x, y: CORRIDOR_Y.top + (CORRIDOR_Y.bottom - CORRIDOR_Y.top) / 2 });
    this._waypoints.push(dest);
    this._atTarget = false;
  }

  // Return home from delivery
  returnHome() {
    this._delivering = false; this._deliveryIcon = '';
    const home = zoneCenter(this._homeZone);
    this._waypoints = [];
    this._waypoints.push({ x: this.x, y: CORRIDOR_Y.top + (CORRIDOR_Y.bottom - CORRIDOR_Y.top) / 2 });
    this._waypoints.push({ x: home.x, y: CORRIDOR_Y.top + (CORRIDOR_Y.bottom - CORRIDOR_Y.top) / 2 });
    this._waypoints.push(home);
    this._atTarget = false;
  }

  _pickIdleTarget() {
    // Zone-bounded idle: micro-roam within own desk zone
    const zone = this._homeZone;
    if (!zone) return zoneCenter('claude_desk');
    const z = ZONE_MAP[zone];
    const cx = z.x + z.w / 2, cy = z.y + z.h / 2;
    const rx = cx + (Math.random() - 0.5) * Math.min(z.w * 0.5, 30);
    const ry = cy + (Math.random() - 0.5) * Math.min(z.h * 0.5, 30);
    return clampToZone(rx, ry, zone);
  }

  _pickTarget() {
    if (this._delivering) return; // Don't override delivery path
    this._waypoints = [];
    const home = zoneCenter(this._homeZone);
    switch (this.state) {
      case 'working': case 'booting': this._waypoints.push(home); break;
      case 'ready': case 'idle': this._waypoints.push(this._pickIdleTarget()); break;
      case 'broken': case 'dead': this._waypoints.push({ x: home.x + 20, y: home.y + 10 }); break;
      default: this._waypoints.push(home);
    }
    this._atTarget = false;
  }

  update(dt) {
    // Fatigue
    const fatigued = this.fatigue >= 15;
    if (this.state === 'working') { this.fatigue += dt; this._atCoffee = false; }
    if (fatigued && this.state === 'working') {
      this._fatigueSweatTimer -= dt;
      if (this._fatigueSweatTimer <= 0) {
        this._fatigueSweatTimer = 1.2 + Math.random() * 0.8;
        spawnParticle(this.name, '💦', { size: 12, lifetime: 1.0 });
      }
    }
    // Walk
    const speedMult = fatigued ? 0.6 : 1.0;
    if (this._waypoints.length > 0) {
      const wp = this._waypoints[0];
      const dx = wp.x - this.x, dy = wp.y - this.y, dist = Math.sqrt(dx * dx + dy * dy);
      if (Math.abs(dx) > 2) this.facingRight = dx > 0;
      const step = WALK_SPEED * speedMult * dt;
      if (dist <= step) {
        this.x = wp.x; this.y = wp.y; this._waypoints.shift();
        if (this._waypoints.length === 0) {
          this._atTarget = true;
          if (this._delivering) { setTimeout(() => this.returnHome(), 300); }
        }
      } else { this.x += (dx / dist) * step; this.y += (dy / dist) * step; }
      this.movePhase += dt * 8; this._atTarget = false;
    } else {
      this._atTarget = true;
      if (this.movePhase > 0) this.movePhase = Math.max(0, this.movePhase - dt * 12);
    }
    // Animations
    this.bobPhase += dt * (this.state === 'working' ? 4 : 1.8);
    this.blinkTimer -= dt;
    if (this.blinkTimer <= 0) { this.isBlinking = !this.isBlinking; this.blinkTimer = this.isBlinking ? 0.12 : 2 + Math.random() * 3; }
    if (this.bubble.timer > 0) this.bubble.timer -= dt;
    // Idle wander (zone-bounded)
    if (this._atTarget && !this._atCoffee && !this._delivering && (this.state === 'ready' || this.state === 'idle')) {
      if (Math.random() < 0.06 * dt) {
        const nudge = clampToZone(this.x + (Math.random() - 0.5) * 18, this.y + (Math.random() - 0.5) * 14, this._homeZone);
        this.x = nudge.x; this.y = nudge.y;
      }
      this._glanceCooldown -= dt;
      if (this._glanceCooldown <= 0) { this._glanceCooldown = 2.5 + Math.random() * 5; if (Math.random() < 0.45) this.facingRight = !this.facingRight; }
      this._staleTimer += dt; this._idleCooldown -= dt;
      if (this._idleCooldown <= 0 || this._staleTimer > 10) {
        this._staleTimer = 0;
        const roll = Math.random();
        this._idleCooldown = roll < 0.10 ? 6 + Math.random() * 5 : roll < 0.40 ? 2.5 + Math.random() * 3 : 1.0 + Math.random() * 2.5;
        this._pickTarget();
      }
    } else { this._staleTimer = 0; }
  }

  draw(ctx, scale) {
    // ... (exact copy of existing draw method from index.html lines 892-1031)
    // This is long but structurally identical — only the label drawing at the
    // end gets an additional delivery icon badge when this._delivering is true
    const sx = this.x * scale, sy = this.y * scale;
    const bob = Math.sin(this.bobPhase) * (this.state === 'working' ? 1.5 : 2.5) * scale;
    const walk = this._atTarget ? 0 : Math.sin(this.movePhase) * 2 * scale;
    const gifSrc = STATE_GIF_ASSETS[this.state] || STATE_GIF_ASSETS.ready || '';
    const hasGif = Boolean(gifSrc);
    let headY = sy;

    if (hasGif) {
      if (this._gifState !== this.state) { this._gifEl.src = gifSrc; this._gifState = this.state; }
      this._gifEl.style.display = 'block';
      const spriteH = 90 * scale;
      const spriteW = spriteH * (this._gifEl.naturalWidth && this._gifEl.naturalHeight ? this._gifEl.naturalWidth / this._gifEl.naturalHeight : 1);
      headY = sy - spriteH + 12 * scale + bob + walk;
      this._gifEl.style.width = spriteW + 'px'; this._gifEl.style.height = spriteH + 'px';
      this._gifEl.style.left = (sx - spriteW / 2) + 'px'; this._gifEl.style.top = headY + 'px';
      this._gifEl.style.transform = this.facingRight ? 'scaleX(1)' : 'scaleX(-1)';
      this._gifEl.style.filter = (this.state === 'broken' || this.state === 'dead' || this.state === 'off') ? 'grayscale(0.9) brightness(0.7)' : '';
      // Shadow
      ctx.fillStyle = 'rgba(0,0,0,0.28)'; ctx.beginPath(); ctx.ellipse(sx, sy + 6 * scale, spriteW * 0.35, 5 * scale, 0, 0, Math.PI * 2); ctx.fill();
    } else {
      this._gifEl.style.display = 'none';
      const r = 13 * scale, bodyY = sy + bob + walk; headY = bodyY - r;
      ctx.fillStyle = 'rgba(0,0,0,0.3)'; ctx.beginPath(); ctx.ellipse(sx, sy + r + 3 * scale, r * 0.7, r * 0.22, 0, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = this.color; ctx.beginPath(); ctx.arc(sx, bodyY, r, 0, Math.PI * 2); ctx.fill();
      ctx.fillStyle = 'rgba(255,255,255,0.18)'; ctx.beginPath(); ctx.arc(sx - r * 0.25, bodyY - r * 0.3, r * 0.55, 0, Math.PI * 2); ctx.fill();
      ctx.strokeStyle = 'rgba(255,255,255,0.15)'; ctx.lineWidth = 1.2 * scale;
      ctx.beginPath(); ctx.arc(sx, bodyY, r, 0, Math.PI * 2); ctx.stroke();
      if (!this.isBlinking) {
        const eyeY = bodyY - 2 * scale, eyeOx = 4.5 * scale, eyeR = 2.2 * scale, pupR = 1.2 * scale;
        ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(sx - eyeOx, eyeY, eyeR, 0, Math.PI * 2); ctx.arc(sx + eyeOx, eyeY, eyeR, 0, Math.PI * 2); ctx.fill();
        const lookX = (this.facingRight ? 1 : -1) * 0.8 * scale;
        ctx.fillStyle = '#1a1a2e'; ctx.beginPath(); ctx.arc(sx - eyeOx + lookX, eyeY, pupR, 0, Math.PI * 2); ctx.arc(sx + eyeOx + lookX, eyeY, pupR, 0, Math.PI * 2); ctx.fill();
      } else {
        ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.4 * scale; const eyeY = bodyY - 2 * scale;
        ctx.beginPath(); ctx.moveTo(sx - 6 * scale, eyeY); ctx.lineTo(sx - 3 * scale, eyeY);
        ctx.moveTo(sx + 3 * scale, eyeY); ctx.lineTo(sx + 6 * scale, eyeY); ctx.stroke();
      }
      ctx.strokeStyle = 'rgba(255,255,255,0.5)'; ctx.lineWidth = 1 * scale;
      if (this.state === 'working') { ctx.beginPath(); ctx.moveTo(sx - 3 * scale, bodyY + 4 * scale); ctx.lineTo(sx + 3 * scale, bodyY + 4 * scale); ctx.stroke(); }
      else if (this.state === 'broken' || this.state === 'dead') { ctx.beginPath(); ctx.arc(sx, bodyY + 7 * scale, 3 * scale, Math.PI, 0); ctx.stroke(); }
      else { ctx.beginPath(); ctx.arc(sx, bodyY + 3 * scale, 3 * scale, 0, Math.PI); ctx.stroke(); }
    }

    // Name label
    const r = 13 * scale;
    ctx.font = `bold ${9.5 * scale}px 'Noto Sans KR', sans-serif`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
    ctx.fillStyle = 'rgba(0,0,0,0.6)'; ctx.fillText(this.name, sx + 1, sy - (hasGif ? 72 * scale : r + 5 * scale) + 1);
    ctx.fillStyle = '#e8ecf4'; ctx.fillText(this.name, sx, sy - (hasGif ? 72 * scale : r + 5 * scale));
    // State badge
    const stateText = this.state.toUpperCase();
    ctx.font = `bold ${7 * scale}px sans-serif`;
    const tw = ctx.measureText(stateText).width;
    const pillW = tw + 8 * scale, pillH = 12 * scale, pillX = sx - pillW / 2, pillY = sy + (hasGif ? 10 : r + 8) * scale;
    ctx.fillStyle = this.color + '33'; ctx.beginPath(); ctx.roundRect(pillX, pillY, pillW, pillH, 3 * scale); ctx.fill();
    ctx.fillStyle = this.color; ctx.textBaseline = 'middle'; ctx.fillText(stateText, sx, pillY + pillH / 2);

    // Delivery icon (transit speech bubble)
    if (this._delivering && this._deliveryIcon) {
      ctx.font = `${14 * scale}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'bottom';
      ctx.fillText(this._deliveryIcon, sx, headY - 5 * scale);
    }

    // Speech bubble
    if (this.bubble.timer > 0) {
      ctx.save();
      const padX = 10 * scale, padY = 6 * scale;
      ctx.font = `bold ${10 * scale}px 'Noto Sans KR', sans-serif`;
      const textW = ctx.measureText(this.bubble.text).width;
      const boxW = textW + padX * 2, boxH = 16 * scale + padY * 2;
      const bx = sx, by = headY - 15 * scale;
      ctx.fillStyle = 'rgba(255, 255, 255, 0.95)';
      ctx.beginPath(); ctx.moveTo(bx - 5 * scale, by - boxH + 2 * scale); ctx.lineTo(bx + 5 * scale, by - boxH + 2 * scale); ctx.lineTo(bx, by + 4 * scale); ctx.fill();
      ctx.beginPath(); ctx.roundRect(bx - boxW / 2, by - boxH, boxW, boxH, 8 * scale); ctx.fill();
      ctx.fillStyle = '#0f172a'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillText(this.bubble.text, bx, by - boxH / 2 + 1 * scale);
      ctx.restore();
    }
  }

  hitTest(vx, vy) { const dx = vx - this.x, dy = vy - this.y; return Math.sqrt(dx * dx + dy * dy) < 20; }

  cleanup() { this._gifEl?.remove(); }
}

// ── Test hooks (preserve E2E compatibility) ──
// Note: agents.js needs a reference to PipelineState for hooks that trigger re-render.
// Pass it in via init function or import directly.
import { PipelineState } from './state.js';

window.setAgentFatigue = function(name, value) {
  const agent = agents.get(name);
  if (!agent) return;
  if (value === 'coffee') { agent._atCoffee = true; agent.fatigue = 0; }
  else if (value === 'fatigued') { agent._atCoffee = false; agent.fatigue = 15; }
  else { agent._atCoffee = false; agent.fatigue = 0; }
  // Trigger sidebar re-render so E2E tests see updated data-fatigue attribute
  PipelineState._notify('fatigueChange', { name, value });
};

window.getRoamBounds = function() {
  // Zone-based: return zone map for compatibility. E2E tests need updating.
  return { zones: ZONE_MAP };
};

window.testPickIdleTargets = function(name, count) {
  const agent = agents.get(name);
  if (!agent) return [];
  const results = [];
  for (let i = 0; i < count; i++) {
    const pt = agent._pickIdleTarget();
    results.push({ x: pt.x, y: pt.y });
  }
  return results;
};
```

- [ ] **Step 2: Verify module parses**

Run: `node --check controller/js/agents.js && echo "OK"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add controller/js/agents.js
git commit -m "feat(controller): extract agents.js with zone-bounded movement"
```

---

### Task 6: Write remaining JS modules (canvas, zones, delivery, sidebar, panel)

**Files:**
- Create: `controller/js/canvas.js`
- Create: `controller/js/zones.js`
- Create: `controller/js/delivery.js`
- Create: `controller/js/sidebar.js`
- Create: `controller/js/panel.js`

This task creates all remaining modules. Each is described below.

- [ ] **Step 1: Write canvas.js — isometric background + zone rendering + main loop**

```javascript
// controller/js/canvas.js — Canvas render loop, isometric background, zone boundaries
import { ZONE_MAP, CORRIDOR_Y, VIRTUAL_W, VIRTUAL_H, SEVERITY_MAP, INACTIVE_RUNTIME_STATES } from './config.js';
import { PipelineState } from './state.js';
import { agents, particles } from './agents.js';
import { deliveryPackets, drones } from './delivery.js';
import { AmbientAudio } from './audio.js';

let _lowMotion = false;
export function isLowMotion() { return _lowMotion; }
export function setLowMotion(v) { _lowMotion = v; if (v) { particles.length = 0; deliveryPackets.length = 0; drones.length = 0; } }

const canvas = document.getElementById('office');
const ctx = canvas.getContext('2d');
let cw = 0, ch = 0, scale = 1;

export function getCanvasState() { return { canvas, ctx, cw, ch, scale }; }

export function resize() {
  const wrap = canvas.parentElement;
  const dpr = window.devicePixelRatio || 1;
  cw = wrap.clientWidth; ch = wrap.clientHeight;
  canvas.width = cw * dpr; canvas.height = ch * dpr;
  canvas.style.width = cw + 'px'; canvas.style.height = ch + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  scale = Math.min(cw / VIRTUAL_W, ch / VIRTUAL_H);
}

// ── Isometric background (SVG/CSS drawn on canvas) ──
function drawIsometricGrid(ctx, scale) {
  // Layer 1: solid base
  ctx.fillStyle = '#0a0c14';
  ctx.fillRect(0, 0, VIRTUAL_W * scale, VIRTUAL_H * scale);

  // Layer 2: isometric diamond grid
  ctx.save();
  ctx.strokeStyle = 'rgba(96,165,250,0.04)';
  ctx.lineWidth = 0.5;
  const step = 40 * scale;
  for (let gx = 0; gx < VIRTUAL_W * scale; gx += step) {
    for (let gy = 0; gy < VIRTUAL_H * scale; gy += step) {
      ctx.beginPath();
      ctx.moveTo(gx, gy + step / 2);
      ctx.lineTo(gx + step / 2, gy);
      ctx.lineTo(gx + step, gy + step / 2);
      ctx.lineTo(gx + step / 2, gy + step);
      ctx.closePath();
      ctx.stroke();
    }
  }
  ctx.restore();
}

function drawZones(ctx, scale) {
  const rd = PipelineState.data || {};
  const severity = getSeverity(rd);

  for (const [key, zone] of Object.entries(ZONE_MAP)) {
    const sx = zone.x * scale, sy = zone.y * scale;
    const sw = zone.w * scale, sh = zone.h * scale;

    // Zone floor tile
    ctx.fillStyle = zone.color + '0A'; // very subtle fill
    ctx.fillRect(sx, sy, sw, sh);

    // Zone border
    if (key === 'incident_zone') {
      ctx.setLineDash([6 * scale, 4 * scale]);
      const sev = SEVERITY_MAP[severity] || SEVERITY_MAP.normal;
      ctx.strokeStyle = severity !== 'normal' ? (sev.border || zone.color) : zone.color;
      ctx.globalAlpha = severity !== 'normal' ? 0.8 : 0.3;
      // Incident zone background based on severity
      if (severity !== 'normal') { ctx.fillStyle = sev.bg; ctx.fillRect(sx, sy, sw, sh); }
    } else {
      ctx.setLineDash([]);
      ctx.strokeStyle = zone.color;
      ctx.globalAlpha = 0.25;
    }
    ctx.lineWidth = 1.5 * scale;
    ctx.beginPath(); ctx.roundRect(sx, sy, sw, sh, 6 * scale); ctx.stroke();
    ctx.globalAlpha = 1; ctx.setLineDash([]);

    // Zone label
    ctx.font = `bold ${8 * scale}px 'Noto Sans KR', sans-serif`;
    ctx.fillStyle = zone.color;
    ctx.globalAlpha = 0.6;
    ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    const icon = key.includes('desk') ? '🖥' : key === 'receipt_board' ? '📋' : key === 'archive_shelf' ? '📚' : '🚨';
    ctx.fillText(`${icon} ${zone.role.toUpperCase()}`, sx + 8 * scale, sy + 6 * scale);
    ctx.globalAlpha = 1;

    // Isometric desk furniture (for desk zones)
    if (zone.agent) drawDeskFurniture(ctx, scale, zone);
  }

  // Corridor
  const corY = (CORRIDOR_Y.top + (CORRIDOR_Y.bottom - CORRIDOR_Y.top) / 2) * scale;
  ctx.strokeStyle = 'rgba(71,85,105,0.15)'; ctx.lineWidth = 1;
  ctx.setLineDash([4 * scale, 6 * scale]);
  ctx.beginPath(); ctx.moveTo(20 * scale, corY); ctx.lineTo((VIRTUAL_W - 20) * scale, corY); ctx.stroke();
  ctx.setLineDash([]);

  // Bottom status bar
  const barH = 24 * scale, barY = VIRTUAL_H * scale - barH;
  ctx.fillStyle = 'rgba(17,21,32,0.9)'; ctx.fillRect(0, barY, VIRTUAL_W * scale, barH);
  ctx.strokeStyle = '#1e2636'; ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(0, barY); ctx.lineTo(VIRTUAL_W * scale, barY); ctx.stroke();
  const pres = PipelineState.getPresentation();
  ctx.font = `${9 * scale}px monospace`; ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
  const ty = barY + barH / 2;
  let tx = 12 * scale;
  ctx.fillStyle = '#6b7280'; ctx.fillText('runtime: ', tx, ty); tx += ctx.measureText('runtime: ').width;
  ctx.fillStyle = pres.runtimeClass === 'ok' ? '#34d399' : pres.runtimeClass === 'warn' ? '#fbbf24' : pres.runtimeClass === 'err' ? '#ef4444' : '#6b7280';
  ctx.fillText(pres.runtimeState, tx, ty); tx += ctx.measureText(pres.runtimeState).width + 16 * scale;
  ctx.fillStyle = '#6b7280'; ctx.fillText(`round: ${pres.roundState}`, tx, ty); tx += ctx.measureText(`round: ${pres.roundState}`).width + 16 * scale;
  ctx.fillStyle = '#6b7280'; ctx.fillText(`watcher: ${pres.watcherStatus}`, tx, ty);
}

function drawDeskFurniture(ctx, scale, zone) {
  const cx = (zone.x + zone.w / 2) * scale;
  const cy = (zone.y + zone.h * 0.65) * scale;
  const dw = 40 * scale, dh = 25 * scale;
  // Isometric desk top
  ctx.strokeStyle = zone.color; ctx.lineWidth = 1 * scale; ctx.globalAlpha = 0.3;
  ctx.beginPath();
  ctx.moveTo(cx, cy - dh / 2); ctx.lineTo(cx + dw / 2, cy - dh / 4);
  ctx.lineTo(cx, cy); ctx.lineTo(cx - dw / 2, cy - dh / 4); ctx.closePath();
  ctx.stroke();
  // Desk sides
  ctx.beginPath();
  ctx.moveTo(cx - dw / 2, cy - dh / 4); ctx.lineTo(cx - dw / 2, cy + dh / 4); ctx.lineTo(cx, cy + dh / 2); ctx.lineTo(cx, cy); ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(cx + dw / 2, cy - dh / 4); ctx.lineTo(cx + dw / 2, cy + dh / 4); ctx.lineTo(cx, cy + dh / 2); ctx.lineTo(cx, cy); ctx.stroke();
  ctx.globalAlpha = 1;
}

function getSeverity(rd) {
  const rs = String(rd.runtime_state || '').toUpperCase();
  const watcher = rd.watcher || {};
  if (rs === 'BROKEN') return 'broken';
  if (!INACTIVE_RUNTIME_STATES.has(rs) && watcher.alive === false) return 'watcher_dead';
  if ((rd.control || {}).active_control_status === 'needs_operator') return 'needs_op';
  if ((rd.degraded_reasons || []).length || rd.degraded_reason) return 'degraded';
  return 'normal';
}

function drawBrokenGlow(ctx, cw, ch, severity) {
  if (severity !== 'broken' && severity !== 'watcher_dead') return;
  ctx.save();
  ctx.shadowColor = severity === 'broken' ? '#ef4444' : '#991b1b';
  ctx.shadowBlur = 20;
  ctx.strokeStyle = `rgba(239,68,68,${0.15 + Math.sin(performance.now() / 300) * 0.1})`;
  ctx.lineWidth = 3;
  ctx.strokeRect(2, 2, cw - 4, ch - 4);
  ctx.restore();
}

// ── Main render loop ──
let lastTime = performance.now();

function loop(now) {
  requestAnimationFrame(loop);
  const dt = Math.min((now - lastTime) / 1000, 0.1);
  lastTime = now;

  const rd = PipelineState.data || {};
  const workingCount = [...agents.values()].filter(a => a.state === 'working').length;
  const severity = getSeverity(rd);

  // Update entities
  for (const a of agents.values()) a.update(dt);
  if (!_lowMotion) {
    for (let i = particles.length - 1; i >= 0; i--) { particles[i].update(dt); if (!particles[i].alive) particles.splice(i, 1); }
    for (let i = deliveryPackets.length - 1; i >= 0; i--) { deliveryPackets[i].update(dt); if (!deliveryPackets[i].alive) deliveryPackets.splice(i, 1); }
    for (let i = drones.length - 1; i >= 0; i--) { drones[i].update(dt); if (!drones[i].alive) drones.splice(i, 1); }
  }
  AmbientAudio.update(workingCount);

  // Render
  ctx.clearRect(0, 0, cw, ch);
  drawIsometricGrid(ctx, scale);
  drawZones(ctx, scale);

  // Agents sorted by Y
  const sorted = [...agents.values()].sort((a, b) => a.y - b.y);
  for (const a of sorted) a.draw(ctx, scale);

  if (!_lowMotion) {
    for (const d of deliveryPackets) d.draw(ctx, scale);
    for (const dr of drones) dr.draw(ctx, scale);
    for (const p of particles) p.draw(ctx, scale);
  }

  drawBrokenGlow(ctx, cw, ch, severity);
}

export function startRenderLoop() {
  window.addEventListener('resize', resize);
  resize();
  requestAnimationFrame(loop);
}
```

- [ ] **Step 2: Write zones.js — zone click handlers + object rendering**

```javascript
// controller/js/zones.js — Zone click handlers and canvas object interactivity
import { ZONE_MAP } from './config.js';
import { agents } from './agents.js';
import { SoundFX } from './audio.js';
import { getCanvasState } from './canvas.js';
import { openPanel } from './panel.js';
import { switchTab } from './sidebar.js';

export function initZoneHandlers() {
  const { canvas } = getCanvasState();

  canvas.addEventListener('click', (e) => {
    const { scale } = getCanvasState();
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) / scale, my = (e.clientY - rect.top) / scale;

    // 1. Agent click → slide-in panel (priority)
    for (const a of agents.values()) {
      if (a.hitTest(mx, my)) { openPanel(a.name); return; }
    }

    // 2. Desk zone click → slide-in panel
    for (const [key, zone] of Object.entries(ZONE_MAP)) {
      if (zone.agent && mx >= zone.x && mx <= zone.x + zone.w && my >= zone.y && my <= zone.y + zone.h) {
        openPanel(zone.agent); SoundFX.blip(); return;
      }
    }

    // 3. Object zone click → sidebar tab switch
    if (hitZone(mx, my, 'receipt_board') || hitZone(mx, my, 'archive_shelf')) {
      switchTab('artifacts'); SoundFX.blip(); return;
    }
    if (hitZone(mx, my, 'incident_zone')) {
      switchTab('incidents'); SoundFX.blip(); return;
    }
  });

  // Tooltip on hover
  const tooltip = document.getElementById('tooltip');
  canvas.addEventListener('mousemove', (e) => {
    const { scale } = getCanvasState();
    const rect = canvas.getBoundingClientRect();
    const mx = (e.clientX - rect.left) / scale, my = (e.clientY - rect.top) / scale;
    let hit = null;
    for (const a of agents.values()) { if (a.hitTest(mx, my)) { hit = a; break; } }
    if (hit) {
      tooltip.style.display = 'block';
      tooltip.style.left = (e.clientX - rect.left + 14) + 'px';
      tooltip.style.top = (e.clientY - rect.top - 8) + 'px';
      tooltip.querySelector('.tt-name').textContent = `${hit.name} (${hit.role})`;
      tooltip.querySelector('.tt-state').textContent = hit.state.toUpperCase();
      tooltip.querySelector('.tt-state').style.color = hit.color;
      tooltip.querySelector('.tt-note').textContent = hit.note || '';
    } else { tooltip.style.display = 'none'; }
  });
  canvas.addEventListener('mouseleave', () => tooltip.style.display = 'none');
}

function hitZone(mx, my, zoneKey) {
  const z = ZONE_MAP[zoneKey];
  return z && mx >= z.x && mx <= z.x + z.w && my >= z.y && my <= z.y + z.h;
}
```

- [ ] **Step 3: Write delivery.js**

```javascript
// controller/js/delivery.js — Agent walk delivery + packet animation + drone
import { agents, spawnParticle, Particle, particles } from './agents.js';
import { SoundFX } from './audio.js';
import { ZONE_MAP, VIRTUAL_W } from './config.js';
import { PipelineState } from './state.js';

export const deliveryPackets = [];
export const drones = [];

function basename(p) { return String(p || '').split('/').filter(Boolean).pop() || '—'; }

// ── Packet (low-importance events) ──
class DeliveryPacket {
  constructor(fromZone, toZone, label) {
    const src = zoneCenter(fromZone), dst = zoneCenter(toZone);
    this.x = src.x; this.y = src.y; this.tx = dst.x; this.ty = dst.y;
    this.label = label; this.lifetime = 1.5; this.maxLife = 1.5;
    this.alive = true; this.arcY = 0;
  }
  update(dt) {
    const frac = 1 - (this.lifetime / this.maxLife);
    this.x += (this.tx - this.x) * 0.06; this.y += (this.ty - this.y) * 0.06;
    this.arcY = -Math.sin(frac * Math.PI) * 30;
    this.lifetime -= dt; if (this.lifetime <= 0) this.alive = false;
  }
  draw(ctx, scale) {
    const alpha = Math.min(1, this.lifetime / (this.maxLife * 0.3));
    const sx = this.x * scale, sy = (this.y + this.arcY) * scale;
    ctx.save(); ctx.globalAlpha = alpha;
    ctx.fillStyle = 'rgba(96,165,250,0.15)'; ctx.beginPath(); ctx.arc(sx, sy, 10 * scale, 0, Math.PI * 2); ctx.fill();
    ctx.font = `${12 * scale}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillStyle = '#fff'; ctx.fillText(this.label, sx, sy);
    ctx.restore();
  }
}

// ── Drone (unchanged from original) ──
export class Drone {
  constructor(targetZone) {
    const dest = zoneCenter(targetZone);
    this.targetZone = targetZone;
    this.x = dest.x + (Math.random() - 0.5) * 200; this.y = -50;
    this.tx = dest.x; this.ty = dest.y - 30;
    this.phase = 'arriving'; this.hoverTimer = 0; this.alive = true;
    this.propPhase = Math.random() * Math.PI * 2;
    this.exitX = dest.x + (Math.random() < 0.5 ? -300 : 300); this.exitY = -80;
  }
  update(dt) {
    this.propPhase += dt * 20;
    if (this.phase === 'arriving') {
      this.x += (this.tx - this.x) * 2.5 * dt; this.y += (this.ty - this.y) * 2.5 * dt;
      if (Math.sqrt((this.tx - this.x) ** 2 + (this.ty - this.y) ** 2) < 5) { this.phase = 'hovering'; }
    } else if (this.phase === 'hovering') {
      this.y += Math.sin(this.propPhase * 0.3) * 0.3; this.hoverTimer += dt;
      if (this.hoverTimer >= 0.6) { SoundFX.blip(); this.phase = 'departing'; }
    } else if (this.phase === 'departing') {
      this.x += (this.exitX - this.x) * 3.0 * dt; this.y += (this.exitY - this.y) * 3.0 * dt;
      if (this.y < -60) this.alive = false;
    }
  }
  draw(ctx, scale) {
    const sx = this.x * scale, sy = this.y * scale, sz = 6 * scale;
    ctx.save();
    ctx.fillStyle = `rgba(150,200,255,${0.2 + Math.sin(this.propPhase) * 0.1})`;
    ctx.beginPath(); ctx.ellipse(sx, sy - sz * 1.5, sz * 2.2, sz * 0.5, 0, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = '#2a3548'; ctx.beginPath(); ctx.roundRect(sx - sz, sy - sz, sz * 2, sz * 1.5, 2 * scale); ctx.fill();
    ctx.fillStyle = this.phase === 'hovering' ? '#34d399' : '#60a5fa';
    ctx.beginPath(); ctx.arc(sx - sz * 0.5, sy - sz * 0.3, 1.5 * scale, 0, Math.PI * 2); ctx.arc(sx + sz * 0.5, sy - sz * 0.3, 1.5 * scale, 0, Math.PI * 2); ctx.fill();
    if (this.phase !== 'departing') {
      ctx.fillStyle = '#8B6914'; ctx.fillRect(sx - 3 * scale, sy + sz * 0.5, 6 * scale, 5 * scale);
    }
    ctx.restore();
  }
}

function zoneCenter(zoneKey) {
  const z = ZONE_MAP[zoneKey]; return z ? { x: z.x + z.w / 2, y: z.y + z.h / 2 } : { x: 500, y: 350 };
}

function agentZoneKey(name) { return `${name.toLowerCase()}_desk`; }

// ── Delivery dispatcher ──
export function initDeliverySystem() {
  PipelineState.onChange((type, detail) => {
    if (type !== 'delivery') return;
    for (const trigger of detail) {
      switch (trigger.type) {
        case 'control': {
          const status = trigger.status;
          if (status === 'implement') {
            // High: document flies in from offscreen to Claude
            deliveryPackets.push(new DeliveryPacket('codex_desk', 'claude_desk', '📋'));
            speakAgent('Claude', '받았습니다', 2.5);
            PipelineState.pushEvent('info', `Implement handoff → Claude (seq ${trigger.seq})`);
          } else if (status === 'needs_operator') {
            const owner = agents.get('Claude');
            if (owner) { owner.walkToZone('incident_zone', '⚠️'); }
            PipelineState.pushEvent('warn', `Operator review requested (seq ${trigger.seq})`);
            SoundFX.warn();
          } else if (status === 'advice_ready') {
            const gemini = agents.get('Gemini');
            if (gemini) { gemini.walkToZone('codex_desk', '����'); }
            PipelineState.pushEvent('info', `Advice ready → Codex`);
          } else {
            deliveryPackets.push(new DeliveryPacket('claude_desk', 'codex_desk', '📦'));
            PipelineState.pushEvent('info', `Control changed → ${status || 'none'} (seq ${trigger.seq})`);
          }
          break;
        }
        case 'work': {
          const claude = agents.get('Claude');
          if (claude) { claude.walkToZone('archive_shelf', '📁'); }
          PipelineState.pushEvent('ok', `Work delivered → ${basename(trigger.path)}`);
          SoundFX.success();
          break;
        }
        case 'verify': {
          const codex = agents.get('Codex');
          if (codex) { codex.walkToZone('archive_shelf', '✅'); }
          PipelineState.pushEvent('info', `Verify updated → ${basename(trigger.path)}`);
          break;
        }
        case 'receipt': {
          const codex2 = agents.get('Codex');
          if (codex2) { codex2.walkToZone('receipt_board', '🧾'); }
          PipelineState.pushEvent('ok', `Receipt issued → ${trigger.id}`);
          SoundFX.success();
          break;
        }
      }
    }
  });

  // Drone on lane state → working
  PipelineState.onChange((type, detail) => {
    if (type === 'laneChange' && detail.to === 'working' && detail.from !== 'working') {
      drones.push(new Drone(agentZoneKey(detail.name)));
    }
  });
}

function speakAgent(name, text, duration) {
  const agent = agents.get(name);
  if (agent) agent.speak(text, duration);
}
```

- [ ] **Step 4: Write sidebar.js — tab-based sidebar**

```javascript
// controller/js/sidebar.js — Tab-based sidebar with event log
import { STATE_COLORS, LANE_ROLES } from './config.js';
import { PipelineState } from './state.js';
import { agents } from './agents.js';

let _activeTab = 'agents';
const TABS = ['agents', 'round', 'artifacts', 'incidents'];
const TAB_ICONS = { agents: '👥', round: '📋', artifacts: '📦', incidents: '🚨' };
let _incidentBadge = 0;

function esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function basename(p) { return String(p || '').split('/').filter(Boolean).pop() || '—'; }
function truncate(s, n) { return s.length > n ? s.slice(0, n) + '…' : s; }

export function switchTab(tabName) {
  if (!TABS.includes(tabName)) return;
  _activeTab = tabName;
  if (tabName === 'incidents') _incidentBadge = 0;
  renderSidebar();
}

export function initSidebar() {
  renderSidebar();
  PipelineState.onChange((type, detail) => {
    if (type === 'poll') renderSidebar();
    if (type === 'event') renderEvents();
    if (type === 'fatigueChange') renderSidebar(); // Re-render on test hook fatigue changes
    // Auto-switch to incidents on severity events
    if (type === 'controlChange' && detail.to === 'needs_operator') { _incidentBadge++; switchTab('incidents'); }
  });
}

function renderSidebar() {
  const data = PipelineState.data || {};
  const tabBar = document.getElementById('tab-bar');
  const tabContent = document.getElementById('tab-content');
  if (!tabBar || !tabContent) return;

  // Tab bar
  tabBar.innerHTML = TABS.map(t => {
    const active = t === _activeTab ? ' active' : '';
    const badge = t === 'incidents' && _incidentBadge > 0 ? `<span class="tab-badge">${_incidentBadge}</span>` : '';
    return `<button class="tab-btn${active}" data-tab="${t}" onclick="window.__switchTab('${t}')">${TAB_ICONS[t]}${badge}</button>`;
  }).join('');

  // Tab content
  switch (_activeTab) {
    case 'agents': tabContent.innerHTML = renderAgentsTab(data); break;
    case 'round': tabContent.innerHTML = renderRoundTab(data); break;
    case 'artifacts': tabContent.innerHTML = renderArtifactsTab(data); break;
    case 'incidents': tabContent.innerHTML = renderIncidentsTab(data); break;
  }
}

function renderAgentsTab(data) {
  const lanes = data.lanes || [];
  if (!lanes.length) return '<div style="font-size:11px;color:#3d5070">에이전트 없음</div>';
  return lanes.map(lane => {
    const s = (lane.state || 'off').toLowerCase(), color = STATE_COLORS[s] || STATE_COLORS.off;
    const role = LANE_ROLES[(lane.name || '').toLowerCase()] || '', note = lane.note || lane.status_note || '';
    const initial = (lane.name || '?')[0].toUpperCase();
    const agent = agents.get(lane.name || '');
    const fatigue = agent ? agent.fatigueState : '';
    const fatigueLabel = fatigue === 'coffee' ? '☕ 커피 충전 중' : fatigue === 'fatigued' ? '💦 피로 누적' : '';
    return `<div class="agent-card" data-agent="${esc(lane.name || '')}" data-fatigue="${fatigue}"><div class="agent-avatar" style="background:${color}">${esc(initial)}</div>
      <div class="agent-info"><div class="agent-name">${esc(lane.name || '?')}</div><div class="agent-role">${esc(role)}</div>
      ${note ? `<div class="agent-detail">${esc(truncate(note, 50))}</div>` : ''}
      ${fatigueLabel ? `<div class="agent-fatigue" data-fatigue="${fatigue}">${fatigueLabel}</div>` : ''}</div>
      <div class="agent-state-dot" style="background:${color}" title="${esc(s)}"></div></div>`;
  }).join('');
}

function renderRoundTab(data) {
  const pres = PipelineState.getPresentation(data);
  const control = data.control || {};
  return `
    <div class="info-row"><span class="info-label">상태</span><span class="info-value ${pres.runtimeClass}">${esc(pres.runtimeState)}</span></div>
    <div class="info-row"><span class="info-label">Control</span><span class="info-value ${pres.controlClass}">${esc(pres.controlStatus)}</span></div>
    <div class="info-row"><span class="info-label">Control File</span><span class="info-value dim">${esc(control.active_control_file || '—')}</span></div>
    <div class="info-row"><span class="info-label">Control Seq</span><span class="info-value dim">${control.active_control_seq >= 0 ? control.active_control_seq : '—'}</span></div>
    <div class="info-row"><span class="info-label">Round</span><span class="info-value ${pres.roundClass}">${esc(pres.roundState)}</span></div>
    <div class="info-row"><span class="info-label">Watcher</span><span class="info-value ${pres.watcherClass}">${esc(pres.watcherStatus)}</span></div>
  `;
}

function renderArtifactsTab(data) {
  const lr = data.last_receipt || {};
  const lw = (data.artifacts || {}).latest_work || {};
  const lv = (data.artifacts || {}).latest_verify || {};
  return `
    <div class="section-title">Receipt</div>
    ${lr.verify_result ? `<div class="info-row"><span class="info-label">결과</span><span class="info-value ${lr.verify_result === 'passed' ? 'ok' : 'err'}">${esc(lr.verify_result)}</span></div>
    <div class="info-row"><span class="info-label">ID</span><span class="info-value dim">${esc(lr.receipt_id || '—')}</span></div>` : '<div class="info-row"><span class="info-value dim">receipt 없��</span></div>'}
    <div class="section-title" style="margin-top:12px">Artifacts</div>
    <div class="info-row"><span class="info-label">Work</span><span class="info-value">${esc(basename(lw.path))}</span></div>
    <div class="info-row"><span class="info-label">Verify</span><span class="info-value">${esc(basename(lv.path))}</span></div>
  `;
}

function renderIncidentsTab(data) {
  const dr = (data.degraded_reasons || []).filter(Boolean);
  const pres = PipelineState.getPresentation(data);
  const watcher = data.watcher || {};
  const autonomy = data.autonomy || {};
  return `
    <div class="info-row"><span class="info-label">심각도</span><span class="info-value ${pres.runtimeClass}">${esc(pres.runtimeState)}</span></div>
    <div class="info-row"><span class="info-label">Watcher</span><span class="info-value ${pres.watcherClass}">${esc(pres.watcherStatus)}</span></div>
    ${dr.length ? dr.map(r => `<div class="info-row"><span class="info-label">Degraded</span><span class="info-value ${pres.uncertain ? 'warn' : 'err'}">${esc(r)}</span></div>`).join('') : '<div class="info-row"><span class="info-value dim">이상 없음</span></div>'}
    ${autonomy.block_reason ? `<div class="info-row"><span class="info-label">Block</span><span class="info-value warn">${esc(autonomy.block_reason)}</span></div>` : ''}
    ${autonomy.decision_required ? `<div class="info-row"><span class="info-label">Decision</span><span class="info-value warn">${esc(autonomy.decision_required)}</span></div>` : ''}
  `;
}

function renderEvents() {
  const el = document.getElementById('event-list');
  if (!el) return;
  const log = PipelineState.eventLog;
  if (!log.length) { el.innerHTML = '<div class="event-item"><span class="event-time">—</span><span class="event-msg">대기 중</span></div>'; return; }
  el.innerHTML = log.map(e => `<div class="event-item"><span class="event-time">${esc(e.time)}</span><span class="event-dot ${e.type}"></span><span class="event-msg">${esc(e.msg)}</span></div>`).join('');
}

// Global hook for tab buttons
window.__switchTab = switchTab;
```

- [ ] **Step 5: Write panel.js — slide-in desk dashboard**

```javascript
// controller/js/panel.js — Slide-in desk dashboard panel
import { PipelineState } from './state.js';
import { agents } from './agents.js';
import { SoundFX } from './audio.js';
import { STATE_COLORS, LOG_REFRESH_MS } from './config.js';

let _panelOpen = false;
let _panelLane = '';
let _tailInterval = null;
let _tailInFlight = false;
let _sendInFlight = false;

function esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function basename(p) { return String(p || '').split('/').filter(Boolean).pop() || '—'; }

export function openPanel(agentName) {
  _panelLane = agentName;
  _panelOpen = true;
  const panel = document.getElementById('desk-panel');
  if (!panel) return;
  panel.classList.add('open');
  renderPanel();
  fetchTail();
  if (_tailInterval) clearInterval(_tailInterval);
  _tailInterval = setInterval(fetchTail, 10000); // 10s refresh
  SoundFX.blip();
}

export function closePanel() {
  _panelOpen = false; _panelLane = '';
  const panel = document.getElementById('desk-panel');
  if (panel) panel.classList.remove('open');
  if (_tailInterval) { clearInterval(_tailInterval); _tailInterval = null; }
}

export function initPanel() {
  // Real-time update on poll
  PipelineState.onChange((type) => {
    if (type === 'poll' && _panelOpen) renderPanel();
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && _panelOpen) closePanel(); });

  // Input handlers
  const input = document.getElementById('panel-input');
  const sendBtn = document.getElementById('panel-send');
  if (input) {
    input.addEventListener('input', syncInputState);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendInput(); }
    });
  }
  if (sendBtn) sendBtn.addEventListener('click', sendInput);
}

function renderPanel() {
  if (!_panelOpen || !_panelLane) return;
  const agent = agents.get(_panelLane);
  const data = PipelineState.data || {};
  const lane = (data.lanes || []).find(l => l.name === _panelLane) || {};
  const control = data.control || {};
  const artifacts = data.artifacts || {};
  const color = agent ? agent.color : STATE_COLORS.off;

  document.getElementById('panel-title').textContent = `${_panelLane} Desk`;
  document.getElementById('panel-title').style.borderLeftColor = color;
  document.getElementById('panel-state').textContent = (lane.state || 'OFF').toUpperCase();
  document.getElementById('panel-state').style.color = color;
  document.getElementById('panel-pid').textContent = lane.pid || '—';
  document.getElementById('panel-fatigue').textContent = agent ? `${Math.round(agent.fatigue)}s` : '—';
  document.getElementById('panel-last-event').textContent = lane.last_event_at || '—';
  document.getElementById('panel-control-file').textContent = control.active_control_file || '—';
  document.getElementById('panel-control-seq').textContent = control.active_control_seq >= 0 ? `#${control.active_control_seq}` : '—';
  document.getElementById('panel-control-status').textContent = control.active_control_status || 'none';
  document.getElementById('panel-artifact').textContent = basename((artifacts.latest_work || {}).path);
}

async function fetchTail() {
  if (_tailInFlight || !_panelLane) return;
  _tailInFlight = true;
  const body = document.getElementById('panel-tail');
  try {
    const res = await fetch(`/api/runtime/capture-tail?lane=${encodeURIComponent(_panelLane)}&lines=15`);
    const data = await res.json();
    if (data.ok && data.text) { body.textContent = data.text; body.scrollTop = body.scrollHeight; }
    else { body.textContent = `(${_panelLane} — 활성 로그 없음)`; }
  } catch (e) { body.textContent = `(로그 조회 실패: ${e.message})`; }
  finally { _tailInFlight = false; }
}

function syncInputState() {
  const input = document.getElementById('panel-input');
  const btn = document.getElementById('panel-send');
  if (!input || !btn) return;
  btn.disabled = !_panelLane || !input.value.trim() || _sendInFlight;
  input.disabled = !_panelLane || _sendInFlight;
}

async function sendInput() {
  const input = document.getElementById('panel-input');
  const text = String(input?.value || '').trim();
  if (!_panelLane || !text || _sendInFlight) return;
  _sendInFlight = true; syncInputState();
  try {
    const res = await fetch('/api/runtime/send-input', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lane: _panelLane, text }),
    });
    const data = await res.json();
    if (!res.ok || data.ok === false) throw new Error(data.error || 'send failed');
    input.value = ''; SoundFX.blip();
    await fetchTail();
  } catch (e) { SoundFX.error(); }
  finally { _sendInFlight = false; syncInputState(); if (input) input.focus(); }
}

// Global hooks
window.__closePanel = closePanel;
```

- [ ] **Step 6: Verify all modules parse**

Run: `for f in controller/js/*.js; do node --check "$f" && echo "OK: $f" || echo "FAIL: $f"; done`
Expected: All OK

- [ ] **Step 7: Commit**

```bash
git add controller/js/canvas.js controller/js/zones.js controller/js/delivery.js controller/js/sidebar.js controller/js/panel.js
git commit -m "feat(controller): add canvas, zones, delivery, sidebar, panel modules"
```

---

### Task 7: Rewrite index.html as HTML skeleton with module imports

**Files:**
- Modify: `controller/index.html` (full rewrite — HTML structure only + module entry point)

- [ ] **Step 1: Rewrite index.html**

Replace the entire file with the HTML skeleton that imports all modules:

```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Pipeline Controller — Office</title>
<link rel="stylesheet" href="/controller-assets/css/office.css">
</head>
<body>

<!-- Toolbar -->
<div class="toolbar">
  <span class="title">Pipeline Office</span>
  <span class="badge stopped" id="status-badge">Stopped</span>
  <div class="spacer"></div>
  <button class="btn" id="btn-start">Start</button>
  <button class="btn" id="btn-stop">Stop</button>
  <button class="btn" id="btn-restart">Restart</button>
  <button class="btn" id="mute-btn" title="음소거" style="font-size:13px;padding:2px 8px">🔊</button>
  <button class="btn" id="motion-btn" title="장식 효과 줄이기" style="font-size:13px;padding:2px 8px">✨</button>
  <span class="storage-warn" id="storage-warn" title="localStorage 사용 불가 — 새로고침 시 toolbar 설정이 초기화됩니다">⚠ 설정 비저장</span>
  <span class="project-path" id="project-path">—</span>
</div>

<!-- Main -->
<div class="main">
  <div class="canvas-wrap">
    <canvas id="office"></canvas>
    <div class="canvas-tooltip" id="tooltip">
      <div class="tt-name"></div>
      <div class="tt-state"></div>
      <div class="tt-note"></div>
    </div>
  </div>

  <!-- Slide-in Desk Dashboard Panel -->
  <div class="desk-panel" id="desk-panel">
    <div class="panel-header">
      <span class="panel-title" id="panel-title" style="border-left:3px solid #60a5fa;padding-left:8px">Desk</span>
      <button class="panel-close" onclick="window.__closePanel()">✕</button>
    </div>
    <div class="panel-body">
      <div class="info-row"><span class="info-label">State</span><span class="info-value" id="panel-state">—</span></div>
      <div class="info-row"><span class="info-label">PID</span><span class="info-value dim" id="panel-pid">—</span></div>
      <div class="info-row"><span class="info-label">Fatigue</span><span class="info-value" id="panel-fatigue">—</span></div>
      <div class="info-row"><span class="info-label">Last event</span><span class="info-value dim" id="panel-last-event">—</span></div>
      <div class="panel-divider"></div>
      <div class="section-title">Current Control</div>
      <div class="info-row"><span class="info-label">File</span><span class="info-value dim" id="panel-control-file">—</span></div>
      <div class="info-row"><span class="info-label">Seq</span><span class="info-value dim" id="panel-control-seq">—</span></div>
      <div class="info-row"><span class="info-label">Status</span><span class="info-value" id="panel-control-status">—</span></div>
      <div class="panel-divider"></div>
      <div class="section-title">Terminal Tail</div>
      <div class="panel-tail" id="panel-tail">대기 중...</div>
      <div class="panel-divider"></div>
      <div class="section-title">Latest Artifact</div>
      <div class="info-row"><span class="info-value dim" id="panel-artifact">—</span></div>
    </div>
    <div class="panel-input-row">
      <input id="panel-input" type="text" placeholder="한 줄 입력" autocomplete="off" disabled>
      <button class="panel-send" id="panel-send" disabled>전송</button>
    </div>
  </div>

  <!-- Sidebar -->
  <div class="sidebar">
    <div id="tab-bar" class="tab-bar"></div>
    <div id="tab-content" class="tab-content"></div>
    <div class="event-log-section">
      <div class="section-title">이벤트</div>
      <div class="event-list" id="event-list">
        <div class="event-item"><span class="event-time">—</span><span class="event-msg">대기 중</span></div>
      </div>
    </div>
  </div>
</div>

<!-- Module entry point -->
<script type="module">
import { PipelineState } from '/controller-assets/js/state.js';
import { agents, Agent, SpriteManager } from '/controller-assets/js/agents.js';
import { startRenderLoop, resize, setLowMotion, isLowMotion } from '/controller-assets/js/canvas.js';
import { initZoneHandlers } from '/controller-assets/js/zones.js';
import { initDeliverySystem } from '/controller-assets/js/delivery.js';
import { initSidebar } from '/controller-assets/js/sidebar.js';
import { initPanel } from '/controller-assets/js/panel.js';
import { SoundFX, AmbientAudio, PrefStore } from '/controller-assets/js/audio.js';
import { ACTION_REPOLL_MS } from '/controller-assets/js/config.js';

// ── Wire PrefStore events ──
PrefStore.setEventCallback((type, msg) => PipelineState.pushEvent(type, msg));

// ── Toolbar buttons ──
async function apiPost(path) {
  SoundFX.click();
  try {
    const res = await fetch(path, { method: 'POST' });
    const data = await res.json();
    if (!res.ok || data.ok === false) { PipelineState.pushEvent('err', '요청 실패: ' + (data.error || 'unknown')); SoundFX.error(); }
    else {
      PipelineState.pushEvent('ok', path.split('/').pop() + ' 완료');
      if (path.includes('start')) SoundFX.success(); else if (path.includes('stop')) SoundFX.warn(); else SoundFX.blip();
    }
    setTimeout(() => PipelineState.poll(), ACTION_REPOLL_MS);
  } catch (e) { PipelineState.pushEvent('err', '��청 실패: ' + e.message); SoundFX.error(); }
}

document.getElementById('btn-start').onclick = () => apiPost('/api/runtime/start');
document.getElementById('btn-stop').onclick = () => apiPost('/api/runtime/stop');
document.getElementById('btn-restart').onclick = () => apiPost('/api/runtime/restart');
document.getElementById('mute-btn').onclick = () => AmbientAudio.toggle();
document.getElementById('motion-btn').onclick = () => {
  setLowMotion(!isLowMotion());
  const btn = document.getElementById('motion-btn');
  btn.textContent = isLowMotion() ? '🚫' : '✨';
  btn.title = isLowMotion() ? '장식 효과 켜기' : '장식 효과 줄이기';
  PrefStore.set('office_low_motion', isLowMotion() ? '1' : '0');
};

// ── State listeners ──
PipelineState.onChange((type, data) => {
  if (type === 'poll') {
    const pres = PipelineState.getPresentation(data);
    document.getElementById('status-badge').textContent = pres.runtimeState;
    document.getElementById('status-badge').className = 'badge ' + pres.badgeClass;
    document.getElementById('project-path').textContent = data.project_root || '—';

    // Sync agents
    const lanes = data.lanes || [];
    const seen = new Set();
    for (const lane of lanes) {
      const name = lane.name || ''; seen.add(name);
      if (!agents.has(name)) agents.set(name, new Agent(name));
      agents.get(name).applyLaneData(lane, SoundFX);
    }
    for (const [name, agent] of agents) {
      if (!seen.has(name)) { agent.cleanup(); agents.delete(name); }
    }
  }
});

// ── Boot ──
AmbientAudio.restore();
if (!PrefStore.available) {
  const sw = document.getElementById('storage-warn');
  if (sw) sw.style.display = 'inline-block';
}
if (PrefStore.get('office_low_motion') === '1') {
  setLowMotion(true);
  document.getElementById('motion-btn').textContent = '🚫';
}

SpriteManager.init();
startRenderLoop();
initZoneHandlers();
initDeliverySystem();
initSidebar();
initPanel();
PipelineState.startPolling();
</script>
</body>
</html>
```

- [ ] **Step 2: Verify page loads**

Run: `python3 -m unittest tests.test_controller_server -v`
Expected: ALL PASS

- [ ] **Step 3: Run E2E smoke**

Run: `cd e2e && npx playwright test tests/controller-smoke.spec.mjs --reporter=line`
Expected: ALL PASS (selectors preserved: #storage-warn, .agent-card, .agent-fatigue, #event-list)

- [ ] **Step 4: Commit**

```bash
git add controller/index.html
git commit -m "refactor(controller): rewrite index.html as modular HTML skeleton"
```

---

### Task 8: Add new CSS for zones, tabs, slide-in panel, and isometric theme

**Files:**
- Modify: `controller/css/office.css`

- [ ] **Step 1: Append zone, tab, panel, and isometric styles to office.css**

Add at the end of `controller/css/office.css`:

```css
/* ═══════════════════════════════════════ */
/* Tab Bar                                */
/* ══════════════════════════════════════��� */
.tab-bar {
  display: flex; gap: 2px; padding: 4px 0 8px;
  border-bottom: 1px solid #1e2636; margin-bottom: 8px;
}
.tab-btn {
  flex: 1; padding: 6px 0; border: none; border-radius: 6px 6px 0 0;
  background: transparent; color: #3d5070; font-size: 14px;
  cursor: pointer; transition: background 80ms, color 80ms;
  position: relative;
}
.tab-btn:hover { background: #1a2236; color: #8fa3b8; }
.tab-btn.active { background: #1e2636; color: #e2e8f0; }
.tab-badge {
  position: absolute; top: 2px; right: 6px;
  background: #ef4444; color: #fff; font-size: 8px; font-weight: 700;
  padding: 1px 4px; border-radius: 999px; min-width: 14px; text-align: center;
}
.tab-content {
  flex: 1; overflow-y: auto; padding: 0 2px;
}

/* ═══════════════════════════════════════ */
/* Event Log (pinned bottom)              */
/* ═══════════════════════════════════════ */
.event-log-section {
  border-top: 1px solid #1e2636; padding-top: 8px;
  flex-shrink: 0; max-height: 160px;
}

/* ═���════════════════════════════���════════ */
/* Slide-in Desk Panel                    */
/* ���═════════════════��════════════════════ */
.desk-panel {
  position: fixed; top: 44px; right: -340px; bottom: 0;
  width: 320px; background: #111520; border-left: 1px solid #1e2636;
  z-index: 500; transition: right 200ms ease;
  display: flex; flex-direction: column;
  box-shadow: -8px 0 32px rgba(0,0,0,0.4);
}
.desk-panel.open { right: 0; }
.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 14px; border-bottom: 1px solid #1e2636;
}
.panel-title { font-size: 13px; font-weight: 700; color: #e2e8f0; }
.panel-close {
  width: 28px; height: 28px; border: 1px solid #1e2a40; border-radius: 6px;
  background: transparent; color: #5a7090; font-size: 16px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.panel-close:hover { background: #1a2236; color: #ccc; }
.panel-body { flex: 1; overflow-y: auto; padding: 10px 14px; }
.panel-divider { height: 1px; background: #1e2636; margin: 10px 0; }
.panel-tail {
  font-family: 'Cascadia Code', 'Fira Code', 'Consolas', monospace;
  font-size: 10px; line-height: 1.5; color: #7a94a8;
  background: #080c14; border-radius: 6px; padding: 8px;
  max-height: 150px; overflow-y: auto; white-space: pre; word-break: keep-all;
}
.panel-input-row {
  display: flex; gap: 6px; padding: 10px 14px;
  border-top: 1px solid #1e2636; background: #0b111a;
}
.panel-input-row input {
  flex: 1; min-width: 0; height: 32px;
  border: 1px solid #1e2a40; border-radius: 6px;
  background: #08111d; color: #c9d6e6; padding: 0 8px;
  font-family: 'Cascadia Code', monospace; font-size: 11px;
}
.panel-input-row input:focus { outline: none; border-color: #2f74ff; }
.panel-send {
  height: 32px; padding: 0 10px; border-radius: 6px;
  border: 1px solid #21406c; background: #10233f; color: #9ec5ff;
  font-size: 11px; font-weight: 700; cursor: pointer;
}
.panel-send:disabled { opacity: 0.45; cursor: not-allowed; }
```

- [ ] **Step 2: Verify CSS loads**

Open `http://localhost:8780/controller` and verify:
- Tab bar visible at top of sidebar
- Desk panel slides in from right on zone click
- Isometric grid background visible on canvas

- [ ] **Step 3: Commit**

```bash
git add controller/css/office.css
git commit -m "feat(controller): add CSS for tabs, slide-in panel, and zone theming"
```

---

### Task 9: Run full test suite and fix regressions

**Files:**
- Possibly modify: any file with broken selectors or test hooks

- [ ] **Step 1: Run backend tests**

Run: `python3 -m unittest tests.test_controller_server -v`
Expected: ALL PASS

- [ ] **Step 2: Run E2E controller smoke**

Run: `cd e2e && npx playwright test tests/controller-smoke.spec.mjs --reporter=line`
Expected: ALL PASS

If any test fails, identify the specific selector or hook that broke and fix it. The most likely issues:
- `#agent-cards` container replaced by tab system → agent cards are now inside `#tab-content`
- `window.setAgentFatigue` needs to trigger sidebar re-render → already calls sidebar via `PipelineState.onChange`
- Log modal DOM removed → if E2E tests reference `#log-modal`, need to add back or update tests

- [ ] **Step 3: Fix any E2E regressions**

For each failing test, trace the selector to the new DOM structure and update either the selector in the test or the DOM in index.html. Document each change.

- [ ] **Step 4: Run full E2E suite**

Run: `cd e2e && npx playwright test --reporter=line`
Expected: ALL PASS

- [ ] **Step 5: Commit fixes**

```bash
git add -u
git commit -m "fix(controller): resolve E2E regressions from modular rewrite"
```

---

### Task 10: Manual visual verification

**Files:** None (verification only)

- [ ] **Step 1: Start the controller server**

Run: `python3 -m controller.server` (or the project's standard launch method)

- [ ] **Step 2: Verify in browser**

Open `http://localhost:8780/controller` and check:
1. Isometric grid background renders (diamond pattern on dark base)
2. Six zones visible with colored borders and labels
3. Agent sprites appear at their desk zone centers
4. Agents stay within zone boundaries during idle
5. Sidebar tabs switch correctly (Agents / Round / Artifacts / Incidents)
6. Event log pinned at sidebar bottom
7. Click desk zone → slide-in panel opens from right
8. Panel shows state, PID, fatigue, control info, terminal tail
9. Panel input sends text to lane
10. Toolbar buttons (Start/Stop/Restart/Mute/Motion) work
11. Motion toggle disables particles and delivery animations

- [ ] **Step 3: Verify delivery animations** (requires running pipeline)

If pipeline is running:
1. Control status change triggers agent walk between zones
2. New work artifact triggers Claude → archive shelf walk
3. New verify artifact triggers Codex → archive shelf walk
4. Lane state change triggers small packet animation
5. needs_operator triggers agent → incident zone walk

- [ ] **Step 4: Document any remaining issues**

Create a list of any visual or functional issues found for follow-up.

- [ ] **Step 5: Final commit**

```bash
git add -u
git commit -m "feat(controller): Pipeline Office spatial UX — zone-first isometric operator console"
```

---

## Known E2E Test Changes Required

The following E2E tests in `e2e/tests/controller-smoke.spec.mjs` rely on the free-roaming system that is replaced by zone-bounded movement. These tests need **updating** in Task 9:

- **`idle roam targets stay within walkable bounds`** — uses `window.getRoamBounds()` which returned `{walkable, desks}`. Zone system replaces this with `{zones: ZONE_MAP}`. Test should verify idle targets stay within the agent's home zone instead.
- **`idle roam avoids proximity to other idle agents (anti-stacking)`** — agents in zones don't need anti-stacking. Test should verify agents stay in separate zones.
- **`idle roam deprioritizes recently visited spots via _roamHistory penalty`** — no spot-based roaming in zone system. Test can be removed or replaced with zone-boundary verification.
- **`setAgentFatigue` hooks** — must trigger sidebar re-render. The hook in agents.js needs to call `PipelineState._notify('fatigueChange')` and sidebar.js must listen for it.

**Decorative systems removed** in zone-first redesign (not in spec):
- Weather rain/time tint
- Office pet cat NPC
- MonitorFX matrix/hologram
- Idle chatter between agents
- Coffee machine/plant easter eggs

These can be re-added as future enhancements if desired.

---

## Summary

| Task | Description | Files | Estimated Steps |
|------|-------------|-------|----------------|
| 1 | Extend server.py for css/js serving | server.py, tests | 6 |
| 2 | Extract CSS into office.css | office.css, index.html | 5 |
| 3 | Extract config.js and state.js | config.js, state.js | 4 |
| 4 | Extract audio.js | audio.js | 3 |
| 5 | Extract agents.js with zone-bounded movement | agents.js | 3 |
| 6 | Write canvas, zones, delivery, sidebar, panel modules | 5 JS files | 7 |
| 7 | Rewrite index.html as HTML skeleton | index.html | 4 |
| 8 | Add new CSS styles | office.css | 3 |
| 9 | Run full test suite, fix regressions | various | 5 |
| 10 | Manual visual verification | none | 5 |
