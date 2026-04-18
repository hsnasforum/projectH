// controller/js/config.js — Pipeline Office constants (cozy RPG theme)
export const POLL_MS = 1000;
export const ACTION_REPOLL_MS = 300;
export const LOG_REFRESH_MS = 1000;
export const VIRTUAL_W = 1000;
export const VIRTUAL_H = 700;
export const WALK_SPEED = 120;

// Warm pastel / JRPG palette — no neons
export const STATE_COLORS = {
  working: '#5c9a4a',  // forest green
  ready:   '#6aa7c9',  // soft sky
  booting: '#e0a93b',  // mustard yellow
  broken:  '#d2553a',  // tomato red
  dead:    '#8a4a30',  // burnt umber
  off:     '#9a8670',  // warm taupe
  unknown: '#a88cc5',  // lilac
};

export const LANE_ROLES = {
  claude: 'implement', codex: 'verify', gemini: 'advisory',
};

// Cozy controller ships with canvas/CSS avatars only.
export const STATE_GIF_ASSETS = Object.freeze({});

export const AMBIGUOUS_RUNTIME_REASON = 'supervisor_missing_recent_ambiguous';
export const UNDATED_AMBIGUOUS_RUNTIME_REASON = 'supervisor_missing_snapshot_undated';
export const UNCERTAIN_RUNTIME_REASONS = new Set([AMBIGUOUS_RUNTIME_REASON, UNDATED_AMBIGUOUS_RUNTIME_REASON]);
export const INACTIVE_RUNTIME_STATES = new Set(['STOPPED', 'STOPPING', 'BROKEN']);

export const STATE_PARTICLES = {
  working: '\u{1F4A1}', ready: '\u{1F4A4}', booting: '\u26A1',
  broken: '\u{1F4A6}', dead: '\u{1F480}', off: '\u{1F319}',
};
export const EVENT_PARTICLES = { ok: '\u2705', warn: '\u2757', err: '\u{1F525}', info: '\u{1F4AC}' };

// Zone layout — colors tuned to warm pastels (role hint only)
export const ZONE_MAP = {
  claude_desk:   { x: 20,  y: 40,  w: 280, h: 250, role: 'implement', color: '#5c9a4a', agent: 'Claude'  },
  codex_desk:    { x: 360, y: 40,  w: 280, h: 250, role: 'verify',    color: '#6aa7c9', agent: 'Codex'   },
  gemini_desk:   { x: 700, y: 40,  w: 280, h: 250, role: 'advisory',  color: '#e0a93b', agent: 'Gemini'  },
  receipt_board: { x: 20,  y: 340, w: 300, h: 150, role: 'receipt',   color: '#a88cc5', agent: null       },
  archive_shelf: { x: 360, y: 340, w: 300, h: 150, role: 'archive',   color: '#8a6a4a', agent: null       },
  incident_zone: { x: 700, y: 340, w: 280, h: 150, role: 'incident',  color: '#d2553a', agent: null       },
};

export const CORRIDOR_Y = { top: 290, bottom: 340 };

export const SEVERITY_MAP = {
  normal:       { bg: 'transparent',           border: 'none',          sidebarForce: false },
  degraded:     { bg: 'rgba(224,169,59,0.14)', border: '#e0a93b solid', sidebarForce: false },
  needs_op:     { bg: 'rgba(224,169,59,0.20)', border: '#e0a93b',       sidebarForce: true  },
  broken:       { bg: 'rgba(210,85,58,0.22)',  border: '#d2553a',       sidebarForce: true  },
  watcher_dead: { bg: 'rgba(138,74,48,0.28)',  border: '#8a4a30',       sidebarForce: true  },
};

export const DELIVERY_IMPORTANCE = {
  control_status_changed: 'high',
  receipt_changed: 'high',
  artifact_changed: 'high',
  lane_state_changed: 'low',
  lane_note_changed: 'low',
  heartbeat: 'none',
};
