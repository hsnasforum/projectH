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

export const STATE_PARTICLES = { working: '\u{1F4A1}', ready: '\u{1F4A4}', booting: '\u26A1', broken: '\u{1F4A6}', dead: '\u{1F480}', off: '\u{1F319}' };
export const EVENT_PARTICLES = { ok: '\u2705', warn: '\u2757', err: '\u{1F525}', info: '\u{1F4AC}' };

// Zone-first layout
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
