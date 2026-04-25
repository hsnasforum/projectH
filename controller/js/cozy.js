// controller/js/cozy.js — Cozy Pipeline Office runtime (canvas render, polling,
// sidebar rendering, log modal input/tail refresh, storage warning, idle-roam
// test hooks). Loaded as /controller-assets/js/cozy.js so the cozy controller
// runs under shared controller/js ownership instead of a standalone inline copy.

const VIRTUAL_W = 1000, VIRTUAL_H = 820;
const ZONE_MAP = {
  claude_desk:   { x: 20,  y: 40,  w: 280, h: 250, role: 'implement', color: '#5c9a4a', agent: 'Claude'  },
  codex_desk:    { x: 360, y: 40,  w: 280, h: 250, role: 'verify',    color: '#6aa7c9', agent: 'Codex'   },
  gemini_desk:   { x: 700, y: 40,  w: 280, h: 250, role: 'advisory',  color: '#e0a93b', agent: 'Gemini'  },
  receipt_board: { x: 20,  y: 340, w: 300, h: 150, role: 'receipt',   color: '#a88cc5', agent: null       },
  archive_shelf: { x: 360, y: 340, w: 300, h: 150, role: 'archive',   color: '#8a6a4a', agent: null       },
  incident_zone: { x: 700, y: 340, w: 280, h: 150, role: 'incident',  color: '#d2553a', agent: null       },
  lounge:        { x: 20,  y: 520, w: 960, h: 260, role: 'lounge',    color: '#c98a6a', agent: null       },
};
const STATE_COLORS = {
  working: '#5c9a4a', ready: '#6aa7c9', booting: '#e0a93b',
  broken: '#d2553a', dead: '#8a4a30', off: '#9a8670',
};
const STATE_ZONE_LABELS = {
  claude_desk:   '🌿 IMPLEMENT',
  codex_desk:    '📘 VERIFY',
  gemini_desk:   '✨ ADVISORY',
  receipt_board: '🧾 RECEIPT',
  archive_shelf: '📚 ARCHIVE',
  incident_zone: '🚨 INCIDENT',
  lounge:        '☕ LOUNGE',
};
const ACTION_REPOLL_MS = 300;
const POLL_MS = 1000;
const LOG_REFRESH_MS = 1000;
const EVENT_LIMIT = 40;
const INACTIVE_RUNTIME_STATES = new Set(['STOPPED', 'STOPPING', 'BROKEN']);
const UNCERTAIN_RUNTIME_REASONS = new Set(['supervisor_missing_recent_ambiguous', 'supervisor_missing_snapshot_undated']);
const TERMINAL_TURN_STATES = new Set(['', 'IDLE', 'CLOSED', 'DONE']);
const ACTIVE_ROUND_ROLE_BY_STATE = Object.freeze({
  VERIFYING: 'verify',
  RECEIPT_PENDING: 'verify',
});
const AGENT_NAMES = Object.freeze(['Claude', 'Codex', 'Gemini']);
const ROLE_NAMES = Object.freeze(['implement', 'verify', 'advisory']);
const DEFAULT_ROLE_OWNERS = Object.freeze({
  implement: 'Claude',
  verify: 'Codex',
  advisory: 'Gemini',
});
const ROLE_ZONE_KEYS = Object.freeze({
  implement: 'claude_desk',
  verify: 'codex_desk',
  advisory: 'gemini_desk',
});
const ROLE_ICONS = Object.freeze({
  implement: '🌿',
  verify: '📘',
  advisory: '✨',
});
const ROLE_OWNER_LABELS = Object.freeze({
  implement: 'Implement owner',
  verify: 'Verify owner',
  advisory: 'Advisory owner',
});
const LANE_META = {
  Claude: { role: 'implement', zone: 'claude_desk', color: '#5c9a4a' },
  Codex: { role: 'verify', zone: 'codex_desk', color: '#6aa7c9' },
  Gemini: { role: 'advisory', zone: 'gemini_desk', color: '#e0a93b' },
};
const ATTENTION_REASON_LABELS = Object.freeze({
  approval_required: '승인 필요',
  auth_login_required: '인증 로그인 필요',
  credential_required: '인증 정보 입력 필요',
  destructive_risk: '위험 작업 확인 필요',
  external_publication_boundary: '외부 공개 경계 확인',
  pr_boundary: 'PR 경계 확인',
  pr_creation_gate: 'PR 생성 승인 필요',
  pr_merge_gate: 'PR merge 승인 필요',
  publication_boundary: '공개 작업 승인 필요',
  safety_stop: '안전 중지 확인 필요',
  security_incident: '보안 사고 확인 필요',
  slice_ambiguity: '다음 작업 선택 필요',
  stale_control_advisory: '제어 슬롯 고착',
  truth_sync_required: 'truth-sync 확인 필요',
});
const AUTH_ATTENTION_MARKERS = [
  'auth',
  'credential',
  'login',
  'oauth',
  'api_key',
  'api key',
  'token',
  '인증',
  '로그인'
];
const CHARACTER_SKINS = Object.freeze({
  Codex: {
    label: '프리렌풍 엘프 마법사',
    shortLabel: 'Frieren',
    hair: '#e8ede3',
    hairShadow: '#b9c3b8',
    eye: '#66a96b',
    outfit: '#f1f2e6',
    outfitShadow: '#8a927d',
    accent: '#d7b86a',
    accessory: '#2f6c4f',
    silhouette: 'elf_mage',
  },
  Claude: {
    label: '아카네풍 배우',
    shortLabel: 'Akane',
    hair: '#273b8f',
    hairShadow: '#172357',
    eye: '#78b8ff',
    outfit: '#56305f',
    outfitShadow: '#2d1935',
    accent: '#d85c82',
    accessory: '#f2d7e3',
    silhouette: 'blue_actor',
  },
  Gemini: {
    label: '귀여운 오리지널 여캐',
    shortLabel: 'Mimi',
    hair: '#f1a7c8',
    hairShadow: '#c96b96',
    eye: '#7a5ad0',
    outfit: '#fff0f5',
    outfitShadow: '#bf6b8d',
    accent: '#7ec9b0',
    accessory: '#f6d65f',
    silhouette: 'cute_girl',
  },
});
const PATH_TILE = 20;
const PATH_OBSTACLES = Object.freeze([
  { x: 56, y: 152, w: 208, h: 46, label: 'claude_desk' },
  { x: 396, y: 152, w: 208, h: 46, label: 'codex_desk' },
  { x: 736, y: 152, w: 208, h: 46, label: 'gemini_desk' },
  { x: 54, y: 370, w: 232, h: 76, label: 'receipt_board' },
  { x: 392, y: 360, w: 236, h: 98, label: 'archive_shelf' },
  { x: 734, y: 370, w: 212, h: 74, label: 'incident_zone' },
]);
const TEAM_CLUSTER_OFFSETS = Object.freeze([
  { x: -34, y: -8 }, { x: 34, y: -8 }, { x: 0, y: 30 }, { x: -58, y: 28 }, { x: 58, y: 28 },
]);
const runtimeStateStore = {
  data: null,
  events: [],
  statusFetchFailureActive: false,
  statusFetchFailureMessage: '',
  previous: { runtimeState: null, controlStatus: null, watcherStatus: null, uncertainRuntime: null, laneStates: {}, roundState: null, approvalWait: null },
  monitor: {
    snapshot: null,
    connected: false,
    previousAgentTokens: {},
    seenCommunications: new Set(),
    previousApprovalWait: {},
    reconnectTimer: null,
  },
  inspector: {
    selectedAgent: '',
    details: null,
    loading: false,
    requestSeq: 0,
  },
  delivery: {
    initialized: false,
    controlSeq: null,
    latestWorkPath: '',
    latestWorkMtime: '',
    latestVerifyPath: '',
    latestVerifyMtime: '',
    lastReceiptId: '',
  },
};
const camera = { x: 0, y: 0 };
let lastMarqueeText = '';
let lowMotion = false;
let muted = false;
let pollInFlight = false;
let monitorFallbackInFlight = false;
let monitorSocket = null;

function cameraView(pad = 0) {
  const width = scale > 0 ? Math.min(VIRTUAL_W, cw / scale) : VIRTUAL_W;
  const height = scale > 0 ? Math.min(VIRTUAL_H, ch / scale) : VIRTUAL_H;
  return {
    x: camera.x - pad,
    y: camera.y - pad,
    w: width + pad * 2,
    h: height + pad * 2,
  };
}

function isWorldRectVisible(x, y, w, h, pad = 0) {
  const view = cameraView(pad);
  return x + w >= view.x && x <= view.x + view.w && y + h >= view.y && y <= view.y + view.h;
}

function characterSkinForAgent(name) {
  return CHARACTER_SKINS[name] || {
    label: name,
    shortLabel: name,
    hair: '#8a6a4a',
    hairShadow: '#5a3d28',
    eye: '#2a1810',
    outfit: '#fbf3dd',
    outfitShadow: '#8a6a4a',
    accent: '#e0a93b',
    accessory: '#6aa7c9',
    silhouette: 'default',
  };
}

function isIdleLikeState(state) {
  const value = String(state || '').toLowerCase();
  return value === 'ready' || value === 'idle' || value === 'off';
}

function animationStateForAgent(agent) {
  if (!agent) return 'idle';
  if (agent.path && agent.path.length) return 'walk';
  if (isIdleLikeState(agent.state) && agent.atLounge) return 'rest';
  if (agent.state === 'working') return 'work';
  if (agent.state === 'broken' || agent.state === 'dead') return 'alert';
  return 'idle';
}

function coordinationForAgent(agentName) {
  const snapshot = runtimeStateStore.monitor.snapshot || {};
  const coordination = snapshot.coordination_state || {};
  const logState = snapshot.log_state || {};
  return coordination[agentName] || logState[agentName] || {};
}

function approvalWaitingForAgent(agent) {
  if (!agent || agent.state === 'off' || agent.state === 'dead') return false;
  const coordination = coordinationForAgent(agent.name);
  if (coordination.approval_wait === true) return true;
  if (coordination.approval_wait && typeof coordination.approval_wait === 'object') {
    return Boolean(coordination.approval_wait.waiting || coordination.approval_wait.required);
  }
  const presentation = getPresentation();
  if (presentation.controlStatus !== 'needs_operator') return false;
  const activeLane = activeWorkLaneName();
  return !activeLane || activeLane === agent.name || agent.state === 'working' || /approval|operator|승인/i.test(agent.note || '');
}

function pointBlocked(x, y) {
  if (x < 8 || y < 8 || x > VIRTUAL_W - 8 || y > VIRTUAL_H - 8) return true;
  return PATH_OBSTACLES.some((rect) =>
    x >= rect.x - 8 && x <= rect.x + rect.w + 8 && y >= rect.y - 8 && y <= rect.y + rect.h + 8
  );
}

function pointToTile(point) {
  return {
    x: Math.max(0, Math.min(Math.floor(VIRTUAL_W / PATH_TILE) - 1, Math.floor(point.x / PATH_TILE))),
    y: Math.max(0, Math.min(Math.floor(VIRTUAL_H / PATH_TILE) - 1, Math.floor(point.y / PATH_TILE))),
  };
}

function tileCenter(tile) {
  return {
    x: tile.x * PATH_TILE + PATH_TILE / 2,
    y: tile.y * PATH_TILE + PATH_TILE / 2,
  };
}

function tileKey(tile) {
  return `${tile.x},${tile.y}`;
}

function tileWalkable(tile) {
  const cols = Math.floor(VIRTUAL_W / PATH_TILE);
  const rows = Math.floor(VIRTUAL_H / PATH_TILE);
  if (tile.x < 0 || tile.y < 0 || tile.x >= cols || tile.y >= rows) return false;
  const center = tileCenter(tile);
  return !pointBlocked(center.x, center.y);
}

function nearestWalkableTile(tile) {
  if (tileWalkable(tile)) return tile;
  for (let radius = 1; radius < 8; radius++) {
    for (let y = tile.y - radius; y <= tile.y + radius; y++) {
      for (let x = tile.x - radius; x <= tile.x + radius; x++) {
        const candidate = { x, y };
        if (tileWalkable(candidate)) return candidate;
      }
    }
  }
  return tile;
}

function heuristic(a, b) {
  return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
}

function reconstructPath(cameFrom, currentKey) {
  const path = [];
  let key = currentKey;
  while (cameFrom.has(key)) {
    const [x, y] = key.split(',').map(Number);
    path.unshift(tileCenter({ x, y }));
    key = cameFrom.get(key);
  }
  return path;
}

function findPath(startPoint, targetPoint) {
  const start = nearestWalkableTile(pointToTile(startPoint));
  const goal = nearestWalkableTile(pointToTile(targetPoint));
  const startKey = tileKey(start);
  const goalKey = tileKey(goal);
  if (startKey === goalKey) return [tileCenter(goal)];
  const open = [{ tile: start, key: startKey, f: heuristic(start, goal) }];
  const cameFrom = new Map();
  const gScore = new Map([[startKey, 0]]);
  const closed = new Set();
  const directions = [
    { x: 1, y: 0 }, { x: -1, y: 0 }, { x: 0, y: 1 }, { x: 0, y: -1 },
    { x: 1, y: 1 }, { x: 1, y: -1 }, { x: -1, y: 1 }, { x: -1, y: -1 },
  ];

  while (open.length) {
    open.sort((a, b) => a.f - b.f);
    const current = open.shift();
    if (!current) break;
    if (current.key === goalKey) return reconstructPath(cameFrom, current.key);
    if (closed.has(current.key)) continue;
    closed.add(current.key);

    for (const dir of directions) {
      const next = { x: current.tile.x + dir.x, y: current.tile.y + dir.y };
      if (!tileWalkable(next)) continue;
      const nextKey = tileKey(next);
      if (closed.has(nextKey)) continue;
      const diagonal = dir.x !== 0 && dir.y !== 0;
      const tentative = (gScore.get(current.key) ?? Infinity) + (diagonal ? 1.4 : 1);
      if (tentative >= (gScore.get(nextKey) ?? Infinity)) continue;
      cameFrom.set(nextKey, current.key);
      gScore.set(nextKey, tentative);
      open.push({ tile: next, key: nextKey, f: tentative + heuristic(next, goal) });
    }
  }
  return [targetPoint];
}

function setAgentDestination(agent, target, { snap = false } = {}) {
  if (!agent || !target) return;
  const endTile = nearestWalkableTile(pointToTile(target));
  const endPoint = tileCenter(endTile);
  agent.tx = endPoint.x;
  agent.ty = endPoint.y;
  agent.path = snap ? [] : findPath({ x: agent.x, y: agent.y }, endPoint);
  if (snap) {
    agent.x = endPoint.x;
    agent.y = endPoint.y;
  }
}

function loungeSeatZone(agentName) {
  const lounge = ZONE_MAP.lounge;
  const idx = Math.max(0, AGENT_NAMES.indexOf(agentName));
  const paddingX = 72;
  const paddingY = 44;
  const usableW = lounge.w - paddingX * 2;
  const seatW = usableW / AGENT_NAMES.length;
  return {
    x: lounge.x + paddingX + seatW * idx,
    y: lounge.y + paddingY,
    w: seatW,
    h: lounge.h - paddingY - 54,
  };
}

function loungeSeatTarget(agentName) {
  const zone = loungeSeatZone(agentName);
  return {
    x: zone.x + zone.w / 2,
    y: zone.y + zone.h * 0.45,
  };
}

function movementZoneForAgent(agent) {
  if (agent && isIdleLikeState(agent.state)) return loungeSeatZone(agent.name);
  const zone = agent ? ZONE_MAP[agent._homeZone] : null;
  return zone || ZONE_MAP.claude_desk;
}

function currentRoleOwners(data = runtimeStateStore.data) {
  const raw = data && typeof data.role_owners === 'object' && data.role_owners ? data.role_owners : null;
  const owners = { ...DEFAULT_ROLE_OWNERS };
  for (const role of ROLE_NAMES) {
    if (!raw || !Object.prototype.hasOwnProperty.call(raw, role)) continue;
    const owner = String(raw[role] || '').trim();
    owners[role] = AGENT_NAMES.includes(owner) ? owner : '';
  }
  return owners;
}

function roleForAgent(name, data = runtimeStateStore.data) {
  const owners = currentRoleOwners(data);
  for (const role of ROLE_NAMES) {
    if (owners[role] === name) return role;
  }
  return LANE_META[name]?.role || '';
}

function currentTurnState(data = runtimeStateStore.data) {
  if (data && data.turn_state && typeof data.turn_state === 'object') return data.turn_state;
  if (data && data.compat && data.compat.turn_state && typeof data.compat.turn_state === 'object') return data.compat.turn_state;
  return {};
}

function liveRoundState(data = runtimeStateStore.data) {
  const round = (data && data.active_round) || {};
  const turn = currentTurnState(data);
  const roundState = String(round.state || '').trim().toUpperCase();
  const turnState = String(turn.state || '').trim().toUpperCase();
  if (roundState && roundState !== 'IDLE') return roundState;
  return turnState || roundState || 'IDLE';
}

function activeWorkLaneName(data = runtimeStateStore.data) {
  const turn = currentTurnState(data);
  const activeRole = String(turn.active_role || '').trim().toLowerCase();
  const activeLane = String(turn.active_lane || '').trim();
  const turnState = String(turn.state || '').trim().toUpperCase();
  if (activeLane && AGENT_NAMES.includes(activeLane) && ROLE_NAMES.includes(activeRole) && !TERMINAL_TURN_STATES.has(turnState)) {
    return activeLane;
  }
  const role = ACTIVE_ROUND_ROLE_BY_STATE[liveRoundState(data)] || '';
  return role ? currentRoleOwners(data)[role] || '' : '';
}

function effectiveLaneState(agentName, lane, data = runtimeStateStore.data) {
  const rawState = String((lane || {}).state || 'off').toLowerCase();
  if (rawState !== 'ready' && rawState !== 'idle') return rawState;
  return agentName === activeWorkLaneName(data) ? 'working' : rawState;
}

function zoneKeyForRole(role) {
  return ROLE_ZONE_KEYS[role] || 'claude_desk';
}

function ownerForZone(zoneKey, data = runtimeStateStore.data) {
  const role = ZONE_MAP[zoneKey]?.role || '';
  if (!ROLE_NAMES.includes(role)) return '';
  return currentRoleOwners(data)[role] || '';
}

function labelForZone(zoneKey, data = runtimeStateStore.data) {
  const zone = ZONE_MAP[zoneKey];
  if (!zone) return '';
  if (!ROLE_NAMES.includes(zone.role)) {
    return STATE_ZONE_LABELS[zoneKey] || zone.role.toUpperCase();
  }
  const owner = ownerForZone(zoneKey, data);
  const icon = ROLE_ICONS[zone.role] || '';
  return owner ? `${icon} ${owner} · ${zone.role.toUpperCase()}` : `${icon} ${zone.role.toUpperCase()}`;
}

function zoneView(zoneKey, data = runtimeStateStore.data) {
  const zone = ZONE_MAP[zoneKey];
  if (!zone) return null;
  if (!ROLE_NAMES.includes(zone.role)) return zone;
  const owner = ownerForZone(zoneKey, data);
  return owner ? { ...zone, agent: owner } : { ...zone, agent: null };
}

function agentMetaForName(name, data = runtimeStateStore.data) {
  const role = roleForAgent(name, data);
  const zoneKey = zoneKeyForRole(role);
  const zone = ZONE_MAP[zoneKey] || ZONE_MAP.claude_desk;
  return { role, zoneKey, color: zone.color };
}

function monitorTeams() {
  const snapshot = runtimeStateStore.monitor.snapshot || {};
  return Array.isArray(snapshot.teams) ? snapshot.teams.filter((team) => team && Array.isArray(team.agents)) : [];
}

function teamForAgent(agentName) {
  return monitorTeams().find((team) => team.agents.includes(agentName)) || null;
}

function agentTeamIndex(team, agentName) {
  const members = Array.isArray(team?.agents) ? team.agents : [];
  return Math.max(0, members.indexOf(agentName));
}

function teamClusterTarget(agent, baseTarget) {
  const team = teamForAgent(agent.name);
  if (!team || !Array.isArray(team.agents) || team.agents.length < 2) return baseTarget;
  const memberTargets = team.agents
    .map((name) => {
      const meta = agentMetaForName(name);
      const zone = ZONE_MAP[meta.zoneKey];
      if (!zone) return null;
      return { x: zone.x + zone.w / 2, y: zone.y + zone.h * 0.7 };
    })
    .filter(Boolean);
  if (!memberTargets.length) return baseTarget;
  const anchor = memberTargets.reduce((acc, point) => ({ x: acc.x + point.x, y: acc.y + point.y }), { x: 0, y: 0 });
  anchor.x /= memberTargets.length;
  anchor.y /= memberTargets.length;
  const offset = TEAM_CLUSTER_OFFSETS[agentTeamIndex(team, agent.name) % TEAM_CLUSTER_OFFSETS.length];
  return {
    x: anchor.x + offset.x,
    y: anchor.y + offset.y,
  };
}

function applyAgentRoleBinding(agent, data = runtimeStateStore.data, { snap = false } = {}) {
  const meta = agentMetaForName(agent.name, data);
  agent.role = meta.role;
  agent.color = meta.color || agent.color;
  agent._homeZone = meta.zoneKey;
  if (isIdleLikeState(agent.state)) {
    const seat = loungeSeatTarget(agent.name);
    agent.atLounge = true;
    agent.loungeTimer = 0;
    setAgentDestination(agent, seat, { snap });
    return;
  }
  agent.atLounge = false;
  const home = ZONE_MAP[meta.zoneKey];
  if (!home) return;
  const homeX = home.x + home.w / 2;
  const homeY = home.y + home.h * 0.72;
  setAgentDestination(agent, teamClusterTarget(agent, { x: homeX, y: homeY }), { snap });
}

const canvas = document.getElementById('office');
const ctx = canvas.getContext('2d');
let cw = 0, ch = 0, scale = 1;

function resize() {
  const wrap = canvas.parentElement;
  const dpr = window.devicePixelRatio || 1;
  cw = wrap.clientWidth - 28;
  ch = wrap.clientHeight - 28;
  canvas.width = cw * dpr; canvas.height = ch * dpr;
  canvas.style.width = cw + 'px'; canvas.style.height = ch + 'px';
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  scale = Math.min(cw / VIRTUAL_W, ch / VIRTUAL_H);
  // Crisp pixels
  ctx.imageSmoothingEnabled = false;
}
window.addEventListener('resize', resize);

/* ─── Agents (mock state) ────────────────────────────────────── */
class Agent {
  constructor(name, state, note, color) {
    const meta = agentMetaForName(name);
    const resting = isIdleLikeState(state);
    this.name = name;
    this.state = state;
    this.note = note || '';
    this.color = color || meta.color;
    this.role = meta.role;
    this.pid = null;
    this.lastEventAt = '';
    this.fatigueState = '';
    this._homeZone = meta.zoneKey;
    this.bobPhase = Math.random() * Math.PI * 2;
    this.blinkTimer = Math.random() * 3;
    this.isBlinking = false;
    this.facingRight = true;
    this.bubble = { text: note || '', fullText: note || '', timer: 999, typeIdx: (note || '').length, typeTimer: 0 };
    this.workLoad = state === 'working' ? 6 : 0;
    this.tokenTotal = 0;
    this.tokenCost = 0;
    this.tokenPulse = 0;
    this.wanderTimer = 2 + Math.random() * 2;
    this.atLounge = resting;
    this.loungeTimer = 0;
    this.path = [];
    this.hasRuntimeSync = false;
    const start = resting
      ? loungeSeatTarget(name)
      : {
          x: (ZONE_MAP[meta.zoneKey] || ZONE_MAP.claude_desk).x + (ZONE_MAP[meta.zoneKey] || ZONE_MAP.claude_desk).w / 2,
          y: (ZONE_MAP[meta.zoneKey] || ZONE_MAP.claude_desk).y + (ZONE_MAP[meta.zoneKey] || ZONE_MAP.claude_desk).h * 0.58,
        };
    this.x = start.x;
    this.y = start.y;
    this.tx = this.x;
    this.ty = this.y;
  }
  setBubble(text) {
    this.bubble = { text: '', fullText: text || '', timer: 4.5, typeIdx: 0, typeTimer: 0 };
  }
  update(dt) {
    this.bobPhase += dt * (this.state === 'working' ? 3.2 : 1.8);
    this.blinkTimer -= dt;
    if (this.blinkTimer <= 0) {
      this.isBlinking = !this.isBlinking;
      this.blinkTimer = this.isBlinking ? 0.12 : 2 + Math.random() * 3;
    }

    // Wander
    this.wanderTimer -= dt;
    if (this.wanderTimer <= 0) {
      this.wanderTimer = 2 + Math.random() * 3;
      if (this.atLounge) {
        const seat = loungeSeatZone(this.name);
        setAgentDestination(this, {
          x: seat.x + 18 + Math.random() * Math.max(20, seat.w - 36),
          y: seat.y + 12 + Math.random() * Math.max(20, seat.h - 24),
        });
      } else {
        const z = ZONE_MAP[this._homeZone];
        const target = {
          x: z.x + 30 + Math.random() * (z.w - 60),
          y: z.y + z.h * 0.54 + Math.random() * (z.h * 0.28),
        };
        const clusteredTarget = teamClusterTarget(this, target);
        this.facingRight = clusteredTarget.x > this.x;
        setAgentDestination(this, clusteredTarget);
      }
    }
    const waypoint = this.path.length ? this.path[0] : { x: this.tx, y: this.ty };
    const dx = waypoint.x - this.x, dy = waypoint.y - this.y;
    const dist = Math.sqrt(dx*dx + dy*dy);
    if (dist > 1) {
      const step = (this.atLounge ? 38 : this.state === 'working' ? 46 : 32) * dt;
      this.x += (dx / dist) * Math.min(step, dist);
      this.y += (dy / dist) * Math.min(step, dist);
      this.facingRight = dx >= 0;
    } else if (this.path.length) {
      this.path.shift();
    }
    // Typewriter bubble
    if (this.bubble.timer > 0) this.bubble.timer -= dt;
    if (this.bubble.typeIdx < this.bubble.fullText.length) {
      this.bubble.typeTimer -= dt;
      if (this.bubble.typeTimer <= 0) {
        this.bubble.typeIdx++;
        this.bubble.text = this.bubble.fullText.slice(0, this.bubble.typeIdx);
        this.bubble.typeTimer = 0.045; // ~22 chars/sec
      }
    }
    if (this.state === 'working') {
      this.workLoad = Math.min(6, this.workLoad + dt * 1.2);
    } else {
      this.workLoad = Math.max(0, this.workLoad - dt * 2);
    }
    this.tokenPulse = Math.max(0, this.tokenPulse - dt);
  }
}

const agents = [
  new Agent('Claude', 'off', '', '#5c9a4a'),
  new Agent('Codex',  'off', '', '#6aa7c9'),
  new Agent('Gemini', 'off', '', '#e0a93b'),
];

/* ═══ Parchment floor + plank grid ═══ */
function drawFloor() {
  const W = VIRTUAL_W * scale, H = VIRTUAL_H * scale;
  // Base parchment wash
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, '#f9ecd0');
  g.addColorStop(1, '#ecd6ad');
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  // Wood plank floor (subtle horizontal bands in lower third)
  const plankH = 22 * scale;
  for (let y = H * 0.5; y < H; y += plankH) {
    ctx.fillStyle = `rgba(140, 95, 55, ${0.04 + Math.random() * 0.02})`;
    ctx.fillRect(0, y, W, 2);
  }

  // Pixel dot grid (subtle, cozy)
  ctx.fillStyle = 'rgba(110, 75, 40, 0.08)';
  const step = 20 * scale;
  for (let gx = 0; gx < W; gx += step) {
    for (let gy = 0; gy < H; gy += step) {
      ctx.fillRect(gx, gy, 1, 1);
    }
  }

  // Corner pixel-border
  ctx.fillStyle = '#8a6a45';
  ctx.fillRect(0, 0, W, 3);
  ctx.fillRect(0, H - 3, W, 3);
  ctx.fillRect(0, 0, 3, H);
  ctx.fillRect(W - 3, 0, 3, H);
  ctx.fillStyle = '#c9a06a';
  ctx.fillRect(3, 3, W - 6, 2);
  ctx.fillRect(3, H - 5, W - 6, 2);
  ctx.fillRect(3, 3, 2, H - 6);
  ctx.fillRect(W - 5, 3, 2, H - 6);
}

/* ═══ Zones: cozy mat + pixel-frame label plate ═══ */
function drawZones() {
  for (const key of Object.keys(ZONE_MAP)) {
    const zone = zoneView(key) || ZONE_MAP[key];
    if (!isWorldRectVisible(zone.x, zone.y, zone.w, zone.h, 80)) continue;
    const sx = zone.x * scale, sy = zone.y * scale;
    const sw = zone.w * scale, sh = zone.h * scale;

    // Zone mat (soft colored rug)
    ctx.save();
    ctx.globalAlpha = 0.18;
    ctx.fillStyle = zone.color;
    ctx.fillRect(sx + 4, sy + 4, sw - 8, sh - 8);
    ctx.restore();

    // Wood-plank floor for top 3 desk zones
    if (zone.agent) drawPlankFloor(sx, sy, sw, sh);

    // Chunky 3-layer pixel border (dark / highlight / dark)
    pixelBorder(sx, sy, sw, sh, zone.color);

    // Wall decor on desk-zone "walls" (top portion)
    if (zone.agent) drawWallDecor(zone);

    // Label plate (top-left) — JRPG menu style
    drawLabelPlate(sx + 8 * scale, sy + 8 * scale, labelForZone(key));

    // Zone-specific furniture
    if (zone.agent) { drawRug(zone); drawWoodenDesk(zone); }
    else if (key === 'archive_shelf') drawBookshelf(zone);
    else if (key === 'receipt_board') drawCorkBoard(zone);
    else if (key === 'incident_zone') drawAlarmBell(zone);
    else if (key === 'lounge') drawLounge(zone);
  }
}

function cross(o, a, b) {
  return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x);
}

function convexHull(points) {
  const sorted = [...points]
    .sort((a, b) => (a.x === b.x ? a.y - b.y : a.x - b.x))
    .filter((point, index, arr) => index === 0 || point.x !== arr[index - 1].x || point.y !== arr[index - 1].y);
  if (sorted.length <= 2) return sorted;
  const lower = [];
  for (const point of sorted) {
    while (lower.length >= 2 && cross(lower[lower.length - 2], lower[lower.length - 1], point) <= 0) lower.pop();
    lower.push(point);
  }
  const upper = [];
  for (let i = sorted.length - 1; i >= 0; i--) {
    const point = sorted[i];
    while (upper.length >= 2 && cross(upper[upper.length - 2], upper[upper.length - 1], point) <= 0) upper.pop();
    upper.push(point);
  }
  upper.pop();
  lower.pop();
  return lower.concat(upper);
}

function drawTeamHulls() {
  for (const team of monitorTeams()) {
    const members = team.agents.map((name) => getAgent(name)).filter(Boolean);
    if (members.length < 2) continue;
    const points = [];
    for (const agent of members) {
      if (!isWorldRectVisible(agent.x - 70, agent.y - 84, 140, 140, 80)) continue;
      points.push(
        { x: agent.x - 38, y: agent.y - 46 },
        { x: agent.x + 38, y: agent.y - 46 },
        { x: agent.x + 44, y: agent.y + 38 },
        { x: agent.x - 44, y: agent.y + 38 },
      );
    }
    const hull = convexHull(points);
    if (hull.length < 3) continue;
    ctx.save();
    ctx.beginPath();
    hull.forEach((point, index) => {
      const x = point.x * scale;
      const y = point.y * scale;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.closePath();
    ctx.globalAlpha = 0.12;
    ctx.fillStyle = team.color || '#6aa7c9';
    ctx.fill();
    ctx.globalAlpha = 0.72;
    ctx.strokeStyle = team.color || '#6aa7c9';
    ctx.lineWidth = Math.max(1, 2 * scale);
    ctx.setLineDash([8 * scale, 5 * scale]);
    ctx.stroke();
    ctx.restore();
  }
}

/* ─── Shared drop-shadow helper ─── */
function drawShadow(vcx, vcy, vrX, vrY = null, alpha = 0.22) {
  const rY = vrY == null ? vrX * 0.32 : vrY;
  ctx.save();
  ctx.fillStyle = `rgba(0, 0, 0, ${alpha})`;
  ctx.beginPath();
  ctx.ellipse(vcx * scale, vcy * scale, vrX * scale, rY * scale, 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

/* ─── Wood plank floor pattern ─── */
function drawPlankFloor(sx, sy, sw, sh) {
  ctx.save();
  // Start planks below the upper "wall" band so decor has breathing room
  const wallH = sh * 0.38;
  const floorTop = sy + wallH;
  const floorH = sh - wallH;
  // Base warm wash
  ctx.fillStyle = 'rgba(176, 122, 74, 0.18)';
  ctx.fillRect(sx + 4, floorTop, sw - 8, floorH - 4);
  // Plank seams (thin horizontal bands)
  const plankH = 14 * scale;
  ctx.fillStyle = 'rgba(74, 46, 24, 0.22)';
  for (let y = floorTop + plankH; y < floorTop + floorH - 4; y += plankH) {
    ctx.fillRect(sx + 6, y, sw - 12, 1 * scale);
  }
  // Subtle plank highlights
  ctx.fillStyle = 'rgba(255, 240, 210, 0.10)';
  for (let y = floorTop + 2; y < floorTop + floorH - 4; y += plankH) {
    ctx.fillRect(sx + 6, y, sw - 12, 1 * scale);
  }
  // Short vertical "plank breaks" for variety
  ctx.fillStyle = 'rgba(74, 46, 24, 0.18)';
  let offset = 0;
  for (let y = floorTop + plankH; y < floorTop + floorH - 4; y += plankH) {
    const bx = sx + 8 + ((offset * 73) % (sw - 20));
    ctx.fillRect(bx, y - plankH + 2, 1 * scale, plankH - 2);
    offset++;
  }
  ctx.restore();
}

/* ─── Wall decor: pixel clock + post-its + window + bunting per desk zone ─── */
function drawWallDecor(zone) {
  const sx = zone.x * scale, sy = zone.y * scale;
  const sw = zone.w * scale;

  // Window on the back wall (time-of-day scenery).
  drawWindow(sx + sw * 0.50, sy + 58 * scale, zone.agent);

  // Small pixel wall clock (top-right of each desk zone)
  drawPixelClock(sx + sw - 32 * scale, sy + 22 * scale);

  // Post-its on the wall, pushed to the edges so the window stays readable.
  const agentSeed = { Claude: 0, Codex: 1, Gemini: 2 }[zone.agent] ?? 0;
  const notes = [
    // Claude — yellow + green
    [
      { x: 0.10, y: 30, col: '#f0d056', txt: 'TODO' },
      { x: 0.22, y: 42, col: '#a8d89a', txt: '✓' },
      { x: 0.88, y: 52, col: '#f4a8b0', txt: '!!' },
    ],
    // Codex — blue + pink
    [
      { x: 0.10, y: 36, col: '#a8cce0', txt: 'REV' },
      { x: 0.22, y: 26, col: '#f0d056', txt: '...' },
      { x: 0.88, y: 46, col: '#f4a8b0', txt: '♥' },
    ],
    // Gemini — mustard + lilac
    [
      { x: 0.10, y: 44, col: '#d6b0e0', txt: '~~~' },
      { x: 0.22, y: 30, col: '#f0d056', txt: 'IDEA' },
      { x: 0.88, y: 40, col: '#a8d89a', txt: '✦' },
    ],
  ][agentSeed];
  notes.forEach(n => {
    const px = sx + sw * n.x;
    const py = sy + n.y * scale;
    drawPostIt(px, py, n.col, n.txt);
  });

  // A tiny bunting garland across the top of each desk zone
  drawBunting(sx + 40 * scale, sy + 4 * scale, sw - 80 * scale, zone.color);
}

function drawPixelClock(x, y) {
  const r = 14 * scale;
  // Drop shadow / mount
  ctx.fillStyle = 'rgba(0,0,0,0.25)';
  ctx.fillRect(x - r + 2, y - r + 2, r * 2, r * 2);
  // Frame (wood)
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(x - r, y - r, r * 2, r * 2);
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(x - r + 2, y - r + 2, r * 2 - 4, r * 2 - 4);
  // Face
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(x - r + 4, y - r + 4, r * 2 - 8, r * 2 - 8);
  // Outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - r - 1, y - r, 1, r * 2);
  ctx.fillRect(x + r, y - r, 1, r * 2);
  ctx.fillRect(x - r, y - r - 1, r * 2, 1);
  ctx.fillRect(x - r, y + r, r * 2, 1);
  // Tick marks (4 dots at 12/3/6/9)
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - 0.5 * scale, y - r + 5 * scale, 1 * scale, 1 * scale);       // 12
  ctx.fillRect(x + r - 6 * scale, y - 0.5 * scale, 1 * scale, 1 * scale);       // 3
  ctx.fillRect(x - 0.5 * scale, y + r - 6 * scale, 1 * scale, 1 * scale);       // 6
  ctx.fillRect(x - r + 5 * scale, y - 0.5 * scale, 1 * scale, 1 * scale);       // 9
  // Hands (real-time!)
  const now = new Date();
  const sec = now.getSeconds() + now.getMilliseconds() / 1000;
  const min = now.getMinutes() + sec / 60;
  const hr = (now.getHours() % 12) + min / 60;
  // Minute hand
  const mAng = (min / 60) * Math.PI * 2 - Math.PI / 2;
  const hAng = (hr / 12) * Math.PI * 2 - Math.PI / 2;
  const sAng = (sec / 60) * Math.PI * 2 - Math.PI / 2;
  drawClockHand(x, y, mAng, r - 6 * scale, 1 * scale, '#2a1810');
  drawClockHand(x, y, hAng, r - 9 * scale, 1.5 * scale, '#2a1810');
  drawClockHand(x, y, sAng, r - 5 * scale, 1, '#d2553a');
  // Center pin
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - 1 * scale, y - 1 * scale, 2 * scale, 2 * scale);
}
function drawClockHand(x, y, ang, len, thickness, col) {
  const steps = 8;
  ctx.fillStyle = col;
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const px = x + Math.cos(ang) * len * t;
    const py = y + Math.sin(ang) * len * t;
    ctx.fillRect(Math.round(px), Math.round(py), thickness, thickness);
  }
}

function drawPostIt(x, y, col, text) {
  const w = 20 * scale, h = 16 * scale;
  const tilt = ((x * 13) % 3 - 1) * 0.04;
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(tilt);
  // Shadow
  ctx.fillStyle = 'rgba(0,0,0,0.22)';
  ctx.fillRect(-w/2 + 2, -h/2 + 2, w, h);
  // Body
  ctx.fillStyle = col;
  ctx.fillRect(-w/2, -h/2, w, h);
  // Fold corner
  ctx.fillStyle = 'rgba(255,255,255,0.45)';
  ctx.fillRect(-w/2, -h/2, w, 2 * scale);
  ctx.fillStyle = 'rgba(0,0,0,0.18)';
  ctx.fillRect(-w/2, h/2 - 2 * scale, w, 2 * scale);
  ctx.fillRect(w/2 - 4 * scale, h/2 - 4 * scale, 4 * scale, 4 * scale);
  // Outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(-w/2 - 1, -h/2, 1, h);
  ctx.fillRect(w/2, -h/2, 1, h);
  ctx.fillRect(-w/2, -h/2 - 1, w, 1);
  ctx.fillRect(-w/2, h/2, w, 1);
  // Text
  ctx.fillStyle = '#2a1810';
  ctx.font = `${7 * scale}px 'DungGeunMo','Galmuri11',monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, 0, 1);
  // Pin
  ctx.fillStyle = '#d2553a';
  ctx.fillRect(-1 * scale, -h/2 + 1, 2 * scale, 2 * scale);
  ctx.fillStyle = '#ffffff';
  ctx.fillRect(0, -h/2 + 1, 1 * scale, 1 * scale);
  ctx.restore();
}

function drawBunting(x, y, w, accent) {
  // Gentle sine arc of small triangle flags
  const count = 7;
  const step = w / (count + 1);
  const flagColors = ['#d2553a', '#e0a93b', '#5c9a4a', '#6aa7c9', '#a88cc5', '#d98ca0', accent];
  // Draw string
  ctx.strokeStyle = '#2a1810';
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let i = 0; i <= count + 1; i++) {
    const px = x + i * step;
    const py = y + Math.sin(i * 0.8) * 1.5 * scale + 6 * scale;
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.stroke();
  // Flags
  for (let i = 1; i <= count; i++) {
    const px = x + i * step;
    const py = y + Math.sin(i * 0.8) * 1.5 * scale + 6 * scale;
    ctx.fillStyle = flagColors[i % flagColors.length];
    // Triangle flag (stacked rects)
    for (let k = 0; k < 4; k++) {
      const fw = (4 - k) * scale;
      ctx.fillRect(px - fw / 2, py + k * scale + 1, fw, 1 * scale);
    }
    // Flag outline tiny
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fillRect(px - 2 * scale, py + 4 * scale, 1, 1);
    ctx.fillRect(px + 1 * scale, py + 4 * scale, 1, 1);
  }
}

function pixelBorder(x, y, w, h, tintColor) {
  // Dark outer
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(x, y, w, 3);
  ctx.fillRect(x, y + h - 3, w, 3);
  ctx.fillRect(x, y, 3, h);
  ctx.fillRect(x + w - 3, y, 3, h);
  // Bright inner top/left
  ctx.fillStyle = tintColor + 'cc';
  ctx.fillRect(x + 3, y + 3, w - 6, 2);
  ctx.fillRect(x + 3, y + 3, 2, h - 6);
  // Dim inner bottom/right
  ctx.fillStyle = '#6a4a2e';
  ctx.fillRect(x + 3, y + h - 5, w - 6, 2);
  ctx.fillRect(x + w - 5, y + 3, 2, h - 6);
}

function drawLabelPlate(x, y, text) {
  ctx.save();
  ctx.font = `${11 * scale}px 'DungGeunMo','Galmuri11','NeoDunggeunmo',monospace`;
  const tw = ctx.measureText(text).width;
  const padX = 8 * scale, padY = 5 * scale;
  const w = tw + padX * 2, h = 20 * scale;
  // Plate background (parchment)
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(x, y, w, h);
  // Shadow ring
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(x, y, w, 2);
  ctx.fillRect(x, y + h - 2, w, 2);
  ctx.fillRect(x, y, 2, h);
  ctx.fillRect(x + w - 2, y, 2, h);
  // Bevel
  ctx.fillStyle = '#fff8e0';
  ctx.fillRect(x + 2, y + 2, w - 4, 1);
  ctx.fillStyle = '#d9b986';
  ctx.fillRect(x + 2, y + h - 3, w - 4, 1);
  // Text
  ctx.fillStyle = '#3a2a1a';
  ctx.textBaseline = 'middle';
  ctx.textAlign = 'left';
  ctx.fillText(text, x + padX, y + h / 2 + 1);
  ctx.restore();
}

/* ─── Window with time-of-day scenery ─── */
const _stars = Array.from({ length: 24 }, () => ({
  x: Math.random(),
  y: Math.random() * 0.6,
  phase: Math.random() * Math.PI * 2,
  speed: 0.8 + Math.random() * 1.8,
  bright: 0.5 + Math.random() * 0.5,
}));

const _clouds = [
  { x: 0.15, y: 0.25, w: 18, h: 6 },
  { x: 0.55, y: 0.18, w: 22, h: 7 },
  { x: 0.82, y: 0.32, w: 14, h: 5 },
];

function drawWindow(vcx, vcy, _agentName) {
  if (window.__hideWindow) return;
  const ww = 110 * scale;
  const wh = 72 * scale;
  const x = vcx - ww / 2;
  const y = vcy - wh / 2;

  let hr;
  if (window.__timeOverride != null) {
    hr = window.__timeOverride;
  } else {
    const now = new Date();
    hr = now.getHours() + now.getMinutes() / 60;
  }

  let phase;
  if (hr >= 5 && hr < 8) phase = 'dawn';
  else if (hr >= 8 && hr < 17) phase = 'day';
  else if (hr >= 17 && hr < 20) phase = 'sunset';
  else phase = 'night';

  ctx.save();
  ctx.beginPath();
  ctx.rect(x, y, ww, wh);
  ctx.clip();

  if (phase === 'day') {
    const gradient = ctx.createLinearGradient(x, y, x, y + wh);
    gradient.addColorStop(0, '#7ac0e0');
    gradient.addColorStop(1, '#b8dced');
    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, ww, wh);
    ctx.fillStyle = '#6a9a5a';
    ctx.fillRect(x, y + wh * 0.75, ww, wh * 0.25);
    ctx.fillRect(x + ww * 0.15, y + wh * 0.7, ww * 0.2, wh * 0.1);
    ctx.fillRect(x + ww * 0.55, y + wh * 0.68, ww * 0.25, wh * 0.12);
    ctx.fillStyle = '#507a42';
    ctx.fillRect(x, y + wh * 0.82, ww, wh * 0.18);
    ctx.fillStyle = '#f8e090';
    ctx.fillRect(x + ww * 0.78, y + wh * 0.15, 6 * scale, 6 * scale);
    ctx.fillRect(x + ww * 0.80, y + wh * 0.13, 2 * scale, 10 * scale);
    ctx.fillRect(x + ww * 0.76, y + wh * 0.17, 10 * scale, 2 * scale);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(x + ww * 0.79, y + wh * 0.15, 2 * scale, 2 * scale);
    const now = performance.now() / 1000;
    _clouds.forEach((cloud, index) => {
      const offset = ((now * 4 + index * 50) % (ww + 80)) - 40;
      drawCloud(x + offset, y + cloud.y * wh, cloud.w * scale, cloud.h * scale);
    });
  } else if (phase === 'dawn' || phase === 'sunset') {
    const gradient = ctx.createLinearGradient(x, y, x, y + wh);
    if (phase === 'dawn') {
      gradient.addColorStop(0, '#6a5a8a');
      gradient.addColorStop(0.5, '#e09a6a');
      gradient.addColorStop(1, '#f4c488');
    } else {
      gradient.addColorStop(0, '#3a2a5a');
      gradient.addColorStop(0.4, '#c2553a');
      gradient.addColorStop(0.75, '#e8893a');
      gradient.addColorStop(1, '#f4b84a');
    }
    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, ww, wh);
    ctx.fillStyle = '#3a2a3a';
    ctx.fillRect(x, y + wh * 0.78, ww, wh * 0.22);
    ctx.fillRect(x + ww * 0.2, y + wh * 0.72, ww * 0.2, wh * 0.1);
    ctx.fillRect(x + ww * 0.58, y + wh * 0.70, ww * 0.25, wh * 0.12);
    const sunY = phase === 'sunset' ? y + wh * 0.52 : y + wh * 0.45;
    ctx.fillStyle = '#fde0a0';
    ctx.fillRect(x + ww * 0.55, sunY, 10 * scale, 10 * scale);
    ctx.fillStyle = '#fff4c0';
    ctx.fillRect(x + ww * 0.57, sunY + 2 * scale, 6 * scale, 6 * scale);
    ctx.fillStyle = 'rgba(255, 230, 160, 0.35)';
    ctx.fillRect(x + ww * 0.5, sunY + 12 * scale, 14 * scale, 1 * scale);
    ctx.fillRect(x + ww * 0.52, sunY + 15 * scale, 10 * scale, 1 * scale);
    if (phase === 'sunset') {
      ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
      [[0.15, 0.1], [0.3, 0.15], [0.75, 0.08]].forEach(([sx, sy]) => {
        ctx.fillRect(x + sx * ww, y + sy * wh, 1, 1);
      });
    }
  } else {
    const gradient = ctx.createLinearGradient(x, y, x, y + wh);
    gradient.addColorStop(0, '#0a0f2a');
    gradient.addColorStop(1, '#1a2048');
    ctx.fillStyle = gradient;
    ctx.fillRect(x, y, ww, wh);
    const now = performance.now() / 1000;
    _stars.forEach((star) => {
      const sx = x + star.x * ww;
      const sy = y + star.y * wh;
      const twinkle = 0.4 + 0.6 * Math.max(0, Math.sin(now * star.speed + star.phase));
      ctx.fillStyle = `rgba(255, 255, 255, ${twinkle * star.bright})`;
      ctx.fillRect(sx, sy, 1, 1);
      if (twinkle > 0.85 && star.bright > 0.8) {
        ctx.fillStyle = `rgba(255, 255, 255, ${(twinkle - 0.5) * 0.8})`;
        ctx.fillRect(sx - 1, sy, 1, 1);
        ctx.fillRect(sx + 1, sy, 1, 1);
        ctx.fillRect(sx, sy - 1, 1, 1);
        ctx.fillRect(sx, sy + 1, 1, 1);
      }
    });
    const moonX = x + ww * 0.78;
    const moonY = y + wh * 0.22;
    ctx.fillStyle = '#f4e8c0';
    ctx.fillRect(moonX - 4 * scale, moonY - 4 * scale, 9 * scale, 9 * scale);
    ctx.fillRect(moonX - 3 * scale, moonY - 5 * scale, 7 * scale, 1 * scale);
    ctx.fillRect(moonX - 3 * scale, moonY + 5 * scale, 7 * scale, 1 * scale);
    ctx.fillRect(moonX - 5 * scale, moonY - 3 * scale, 1 * scale, 7 * scale);
    ctx.fillRect(moonX + 5 * scale, moonY - 3 * scale, 1 * scale, 7 * scale);
    ctx.fillStyle = '#1a2048';
    ctx.fillRect(moonX - 2 * scale, moonY - 4 * scale, 7 * scale, 9 * scale);
    ctx.fillRect(moonX - 1 * scale, moonY - 5 * scale, 6 * scale, 1 * scale);
    ctx.fillRect(moonX - 1 * scale, moonY + 5 * scale, 6 * scale, 1 * scale);
    ctx.fillRect(moonX - 3 * scale, moonY - 3 * scale, 1 * scale, 7 * scale);
    ctx.fillStyle = '#d4c090';
    ctx.fillRect(moonX - 4 * scale, moonY - 2 * scale, 1 * scale, 1 * scale);
    ctx.fillRect(moonX - 3 * scale, moonY + 2 * scale, 1 * scale, 1 * scale);
    ctx.fillStyle = '#0a0a18';
    ctx.fillRect(x, y + wh * 0.78, ww, wh * 0.22);
    ctx.fillRect(x + ww * 0.22, y + wh * 0.72, ww * 0.2, wh * 0.1);
    ctx.fillRect(x + ww * 0.58, y + wh * 0.70, ww * 0.25, wh * 0.12);
  }

  ctx.restore();

  ctx.fillStyle = '#5a3d22';
  ctx.fillRect(x - 4 * scale, y - 4 * scale, ww + 8 * scale, 4 * scale);
  ctx.fillRect(x - 4 * scale, y + wh, ww + 8 * scale, 4 * scale);
  ctx.fillRect(x - 4 * scale, y - 4 * scale, 4 * scale, wh + 8 * scale);
  ctx.fillRect(x + ww, y - 4 * scale, 4 * scale, wh + 8 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - 5 * scale, y - 5 * scale, ww + 10 * scale, 1);
  ctx.fillRect(x - 5 * scale, y + wh + 4 * scale, ww + 10 * scale, 1);
  ctx.fillRect(x - 5 * scale, y - 5 * scale, 1, wh + 10 * scale);
  ctx.fillRect(x + ww + 4 * scale, y - 5 * scale, 1, wh + 10 * scale);
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(x - 3 * scale, y - 3 * scale, ww + 6 * scale, 1);
  ctx.fillRect(x - 3 * scale, y - 3 * scale, 1, wh + 6 * scale);
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(x + ww / 2 - 1, y, 2, wh);
  ctx.fillRect(x, y + wh / 2 - 1, ww, 2);
  ctx.fillStyle = '#5a3d22';
  ctx.fillRect(x + ww / 2 - 1, y, 1, wh);
  ctx.fillRect(x, y + wh / 2 - 1, ww, 1);
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(x - 6 * scale, y + wh + 3 * scale, ww + 12 * scale, 3 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - 6 * scale, y + wh + 6 * scale, ww + 12 * scale, 1);
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(x - 6 * scale, y + wh + 3 * scale, ww + 12 * scale, 1);

  const plantX = x + ww - 8 * scale;
  const plantY = y + wh + 3 * scale;
  ctx.fillStyle = '#a85030';
  ctx.fillRect(plantX - 3 * scale, plantY, 6 * scale, 3 * scale);
  ctx.fillStyle = '#5c9a4a';
  ctx.fillRect(plantX - 2 * scale, plantY - 3 * scale, 4 * scale, 3 * scale);
  ctx.fillStyle = '#7ab867';
  ctx.fillRect(plantX - 1 * scale, plantY - 4 * scale, 2 * scale, 1 * scale);
}

function drawCloud(cx, cy, w, h) {
  ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
  ctx.fillRect(cx, cy, w, h);
  ctx.fillRect(cx + w * 0.2, cy - h * 0.4, w * 0.4, h * 0.4);
  ctx.fillRect(cx + w * 0.55, cy - h * 0.25, w * 0.3, h * 0.25);
  ctx.fillStyle = 'rgba(180, 200, 220, 0.7)';
  ctx.fillRect(cx, cy + h - 2, w, 2);
}

/* ═══ Wooden desk (replaces iso wireframe) ═══ */
function drawWoodenDesk(zone) {
  const cx = (zone.x + zone.w / 2) * scale;
  const cy = (zone.y + zone.h * 0.72) * scale;
  const dw = 120 * scale, dh = 34 * scale;

  // Floor shadow
  ctx.fillStyle = 'rgba(58, 42, 26, 0.22)';
  ctx.fillRect(cx - dw/2 + 4 * scale, cy + dh - 4 * scale, dw, 6 * scale);

  // Desk body — stacked pixel rectangles (planks)
  // Top plank (lighter)
  ctx.fillStyle = '#b98959';
  ctx.fillRect(cx - dw/2, cy - dh/2, dw, dh * 0.55);
  // Plank seams
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(cx - dw/2, cy - dh/2 + dh * 0.18, dw, 1 * scale);
  ctx.fillRect(cx - dw/2, cy - dh/2 + dh * 0.36, dw, 1 * scale);
  // Highlight edge
  ctx.fillStyle = '#d9a875';
  ctx.fillRect(cx - dw/2, cy - dh/2, dw, 2 * scale);
  // Side panel (darker)
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(cx - dw/2, cy - dh/2 + dh * 0.55, dw, dh * 0.45);
  // Leg pixels
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(cx - dw/2, cy + dh/2, 6 * scale, 8 * scale);
  ctx.fillRect(cx + dw/2 - 6 * scale, cy + dh/2, 6 * scale, 8 * scale);
  // Outer pixel frame
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(cx - dw/2 - 2, cy - dh/2 - 2, dw + 4, 2);
  ctx.fillRect(cx - dw/2 - 2, cy + dh/2, dw + 4, 2);
  ctx.fillRect(cx - dw/2 - 2, cy - dh/2 - 2, 2, dh + 4);
  ctx.fillRect(cx + dw/2, cy - dh/2 - 2, 2, dh + 4);

  // Desk-top items: dual monitors + mug + cactus (per role accent)
  const agent = agents.find(a => a.name === zone.agent);
  const working = agent && agent.state === 'working';
  const deskTopY = cy - dh/2;
  // Monitors sit behind mug/cactus (drawn first, further back)
  drawDualMonitors(cx, deskTopY, working, zone.color);
  // Mug on left of desk
  drawMug(cx - 42 * scale, deskTopY - 4 * scale, working);
  // Cactus on right
  drawCactus(cx + 42 * scale, deskTopY - 4 * scale, zone.color);

  // Paper stack (workLoad)
  if (agent && agent.workLoad > 0) {
    const px = cx + 36 * scale;
    const py = cy - dh/2;
    for (let i = 0; i < Math.min(agent.workLoad, 5); i++) {
      const offX = (i % 2 === 0 ? -1 : 1) * (i * 0.8);
      ctx.fillStyle = '#3a2a1a';
      ctx.fillRect(px + offX - 10 * scale, py - i * 3 * scale, 22 * scale, 1);
      ctx.fillStyle = '#fbf3dd';
      ctx.fillRect(px + offX - 10 * scale, py - i * 3 * scale - 2 * scale, 22 * scale, 2 * scale);
      ctx.fillStyle = '#d9b986';
      ctx.fillRect(px + offX - 10 * scale, py - i * 3 * scale, 22 * scale, 1);
    }
  }
}

function drawJournal(x, y, glow) {
  // Book cover (brown)
  ctx.fillStyle = '#5c9a4a';
  ctx.fillRect(x - 12 * scale, y, 24 * scale, 14 * scale);
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(x - 12 * scale, y - 1, 24 * scale, 1);
  ctx.fillRect(x - 12 * scale, y + 14 * scale, 24 * scale, 1);
  ctx.fillRect(x - 13 * scale, y, 1, 14 * scale);
  ctx.fillRect(x + 12 * scale, y, 1, 14 * scale);
  // Pages
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(x - 10 * scale, y + 2 * scale, 20 * scale, 10 * scale);
  ctx.fillStyle = '#8a7258';
  ctx.fillRect(x - 8 * scale, y + 4 * scale, 7 * scale, 1);
  ctx.fillRect(x - 8 * scale, y + 6 * scale, 9 * scale, 1);
  ctx.fillRect(x + 1 * scale, y + 4 * scale, 7 * scale, 1);
  ctx.fillRect(x + 1 * scale, y + 6 * scale, 6 * scale, 1);
  // Glow (writing)
  if (glow) {
    const pulse = 0.5 + Math.sin(performance.now() / 300) * 0.3;
    ctx.fillStyle = `rgba(224, 169, 59, ${pulse * 0.4})`;
    ctx.fillRect(x - 14 * scale, y - 2 * scale, 28 * scale, 18 * scale);
  }
}

function drawInkwell(x, y) {
  // Pot
  ctx.fillStyle = '#6aa7c9';
  ctx.fillRect(x - 6 * scale, y + 4 * scale, 12 * scale, 8 * scale);
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(x - 7 * scale, y + 4 * scale, 14 * scale, 1);
  ctx.fillRect(x - 7 * scale, y + 12 * scale, 14 * scale, 1);
  ctx.fillRect(x - 7 * scale, y + 4 * scale, 1, 8 * scale);
  ctx.fillRect(x + 6 * scale, y + 4 * scale, 1, 8 * scale);
  // Ink surface
  ctx.fillStyle = '#1a0f08';
  ctx.fillRect(x - 4 * scale, y + 5 * scale, 8 * scale, 2 * scale);
  // Quill
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(x + 2 * scale, y - 4 * scale, 2 * scale, 10 * scale);
  ctx.fillStyle = '#d2553a';
  ctx.fillRect(x + 1 * scale, y - 6 * scale, 4 * scale, 3 * scale);
}

function drawCandle(x, y, lit) {
  // Holder
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(x - 6 * scale, y + 10 * scale, 12 * scale, 3 * scale);
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(x - 7 * scale, y + 10 * scale, 14 * scale, 1);
  // Candle
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(x - 3 * scale, y, 6 * scale, 10 * scale);
  ctx.fillStyle = '#d9b986';
  ctx.fillRect(x + 2 * scale, y, 1 * scale, 10 * scale);
  // Flame
  if (lit) {
    const t = performance.now() / 200;
    const fw = 2.5 + Math.sin(t) * 0.5;
    ctx.fillStyle = '#e0a93b';
    ctx.fillRect(x - fw/2 * scale, y - 5 * scale, fw * scale, 4 * scale);
    ctx.fillStyle = '#fff8c0';
    ctx.fillRect(x - (fw/3) * scale, y - 3 * scale, (fw/1.5) * scale, 2 * scale);
    // Soft glow
    ctx.save();
    const grad = ctx.createRadialGradient(x, y - 4 * scale, 0, x, y - 4 * scale, 30 * scale);
    grad.addColorStop(0, 'rgba(255, 220, 130, 0.28)');
    grad.addColorStop(1, 'rgba(255, 220, 130, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(x - 30 * scale, y - 30 * scale, 60 * scale, 60 * scale);
    ctx.restore();
  }
}

/* ═══ Rug — warm pixel rug under the desk ═══ */
function drawRug(zone) {
  // Per-agent rug accent (Claude = forest, Codex = burgundy, Gemini = deep plum)
  const rugPalettes = {
    Claude: { main: '#3d6b3a', border: '#234d26', stripe: '#5c9a4a', fringe: '#e0c08a' },
    Codex:  { main: '#7a2a2a', border: '#4d1616', stripe: '#a84040', fringe: '#e0c08a' },
    Gemini: { main: '#6a3d5c', border: '#40213a', stripe: '#a86691', fringe: '#e0c08a' },
  };
  const pal = rugPalettes[zone.agent] || rugPalettes.Claude;

  const cx = (zone.x + zone.w / 2) * scale;
  const cy = (zone.y + zone.h * 0.78) * scale;
  const rw = 180 * scale;
  const rh = 60 * scale;
  const rx = cx - rw / 2;
  const ry = cy - rh / 2;

  // Fringe top/bottom (little tassels)
  ctx.fillStyle = pal.fringe;
  for (let i = 0; i < rw; i += 4 * scale) {
    ctx.fillRect(rx + i, ry - 3 * scale, 2 * scale, 3 * scale);
    ctx.fillRect(rx + i, ry + rh, 2 * scale, 3 * scale);
  }

  // Rounded rectangle corners (chip corners 3px in)
  const chip = 3 * scale;
  // Main rug body
  ctx.fillStyle = pal.main;
  ctx.fillRect(rx + chip, ry, rw - chip * 2, rh);
  ctx.fillRect(rx, ry + chip, rw, rh - chip * 2);

  // Dark outer border (also chipped)
  ctx.fillStyle = pal.border;
  // top & bottom edges
  ctx.fillRect(rx + chip, ry, rw - chip * 2, 2 * scale);
  ctx.fillRect(rx + chip, ry + rh - 2 * scale, rw - chip * 2, 2 * scale);
  // left & right
  ctx.fillRect(rx, ry + chip, 2 * scale, rh - chip * 2);
  ctx.fillRect(rx + rw - 2 * scale, ry + chip, 2 * scale, rh - chip * 2);
  // corner pixels
  ctx.fillRect(rx + chip - 1, ry + 1, 1, 1);
  ctx.fillRect(rx + rw - chip, ry + 1, 1, 1);
  ctx.fillRect(rx + chip - 1, ry + rh - 2, 1, 1);
  ctx.fillRect(rx + rw - chip, ry + rh - 2, 1, 1);

  // Inner stripe pattern — concentric rounded rect
  ctx.fillStyle = pal.stripe;
  const inset = 8 * scale;
  ctx.fillRect(rx + inset + chip, ry + inset, rw - (inset + chip) * 2, 2 * scale);
  ctx.fillRect(rx + inset + chip, ry + rh - inset - 2 * scale, rw - (inset + chip) * 2, 2 * scale);
  ctx.fillRect(rx + inset, ry + inset + chip, 2 * scale, rh - (inset + chip) * 2);
  ctx.fillRect(rx + rw - inset - 2 * scale, ry + inset + chip, 2 * scale, rh - (inset + chip) * 2);

  // Tiny diamond motifs down the middle
  ctx.fillStyle = pal.fringe;
  const diamondCount = 3;
  for (let d = 0; d < diamondCount; d++) {
    const dxC = rx + rw * (0.25 + d * 0.25);
    const dyC = ry + rh / 2;
    ctx.fillRect(dxC - 1 * scale, dyC - 3 * scale, 2 * scale, 1 * scale);
    ctx.fillRect(dxC - 2 * scale, dyC - 2 * scale, 4 * scale, 1 * scale);
    ctx.fillRect(dxC - 3 * scale, dyC - 1 * scale, 6 * scale, 2 * scale);
    ctx.fillRect(dxC - 2 * scale, dyC + 1 * scale, 4 * scale, 1 * scale);
    ctx.fillRect(dxC - 1 * scale, dyC + 2 * scale, 2 * scale, 1 * scale);
  }
}

/* ═══ Dual pixel monitors ═══ */
function drawDualMonitors(cx, topY, working, accent) {
  // Monitor geometry — two identical units side-by-side, slightly angled inward
  const mW = 34 * scale;
  const mH = 22 * scale;
  const gap = 4 * scale;
  const yTop = topY - mH - 10 * scale; // sits above desk surface
  const mL = cx - mW - gap / 2;
  const mR = cx + gap / 2;

  drawSingleMonitor(mL, yTop, mW, mH, working, accent, -1);
  drawSingleMonitor(mR, yTop, mW, mH, working, accent,  1);
}

function drawSingleMonitor(x, y, w, h, on, accent, sideSign) {
  // Shadow
  ctx.fillStyle = 'rgba(42, 24, 16, 0.25)';
  ctx.fillRect(x + 2, y + 2, w, h);

  // Bezel (dark plastic)
  ctx.fillStyle = '#1a1410';
  ctx.fillRect(x, y, w, h);

  // Gray inner bezel (thin frame)
  ctx.fillStyle = '#4a4440';
  ctx.fillRect(x + 1, y + 1, w - 2, 1);
  ctx.fillRect(x + 1, y + h - 2, w - 2, 1);
  ctx.fillRect(x + 1, y + 1, 1, h - 2);
  ctx.fillRect(x + w - 2, y + 1, 1, h - 2);

  // Screen
  const sxI = x + 3, syI = y + 3;
  const swI = w - 6, shI = h - 6;
  if (on) {
    // ON — soft glow base (accent-tinted or forest green)
    const screenCol = accent === '#6aa7c9' ? '#3a8aaa' :
                      accent === '#e0a93b' ? '#5a8a4a' :
                      '#4a7aa8';
    ctx.fillStyle = screenCol;
    ctx.fillRect(sxI, syI, swI, shI);
    // Code lines (scanline rhythm)
    ctx.fillStyle = 'rgba(255, 255, 255, 0.65)';
    const lineH = 2 * scale;
    const flick = Math.floor(performance.now() / 400) % 3;
    for (let ly = 0; ly < shI; ly += lineH * 2) {
      const lineLen = (3 + ((ly / 2 + flick) % 4)) * 4 * scale;
      ctx.fillRect(sxI + 2 * scale, syI + ly + 1, Math.min(lineLen, swI - 4 * scale), 1 * scale);
    }
    // Cursor blink
    if (Math.floor(performance.now() / 500) % 2 === 0) {
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(sxI + swI - 5 * scale, syI + shI - 4 * scale, 2 * scale, 2 * scale);
    }
    // Glow halo
    ctx.save();
    const grad = ctx.createRadialGradient(sxI + swI/2, syI + shI/2, 0, sxI + swI/2, syI + shI/2, swI);
    grad.addColorStop(0, 'rgba(200, 230, 255, 0.25)');
    grad.addColorStop(1, 'rgba(200, 230, 255, 0)');
    ctx.fillStyle = grad;
    ctx.fillRect(x - 8 * scale, y - 8 * scale, w + 16 * scale, h + 16 * scale);
    ctx.restore();
  } else {
    // OFF — dark screen with faint reflection streak
    ctx.fillStyle = '#0a0a0e';
    ctx.fillRect(sxI, syI, swI, shI);
    ctx.fillStyle = 'rgba(255,255,255,0.04)';
    ctx.fillRect(sxI + 2 * scale, syI + 1, 2 * scale, shI - 2);
  }

  // Screen inner highlight pixel (top-left)
  ctx.fillStyle = 'rgba(255,255,255,0.12)';
  ctx.fillRect(sxI, syI, 1 * scale, 1 * scale);

  // Power LED
  ctx.fillStyle = on ? '#5c9a4a' : '#6a4040';
  ctx.fillRect(x + w - 5 * scale, y + h - 4 * scale, 2 * scale, 2 * scale);

  // Stand (neck + foot)
  const standX = x + w / 2;
  ctx.fillStyle = '#2a2420';
  ctx.fillRect(standX - 1 * scale, y + h, 3 * scale, 4 * scale);
  ctx.fillStyle = '#3a3430';
  ctx.fillRect(standX - 8 * scale, y + h + 4 * scale, 16 * scale, 2 * scale);
}

/* ═══ Steaming mug ═══ */
function drawMug(x, y, hot) {
  const mW = 12 * scale;
  const mH = 14 * scale;
  const mx = x - mW / 2;
  const my = y - mH;

  // Shadow
  ctx.fillStyle = 'rgba(42, 24, 16, 0.25)';
  ctx.fillRect(mx + 2, my + mH, mW, 2 * scale);

  // Handle (behind body)
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(mx + mW, my + 3 * scale, 4 * scale, 1 * scale);
  ctx.fillRect(mx + mW + 3 * scale, my + 3 * scale, 1 * scale, 6 * scale);
  ctx.fillRect(mx + mW, my + 8 * scale, 4 * scale, 1 * scale);

  // Mug body (white/cream)
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(mx, my, mW, mH);
  // Outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(mx - 1, my, 1, mH);
  ctx.fillRect(mx + mW, my, 1, mH);
  ctx.fillRect(mx, my - 1, mW, 1);
  ctx.fillRect(mx, my + mH, mW, 1);
  // Shadow side
  ctx.fillStyle = '#d9b986';
  ctx.fillRect(mx + mW - 2 * scale, my + 1, 2 * scale, mH - 1);
  // Top rim (coffee surface)
  ctx.fillStyle = '#5a3a22';
  ctx.fillRect(mx + 1, my + 1, mW - 2, 2 * scale);
  ctx.fillStyle = '#3a2310';
  ctx.fillRect(mx + 1, my + 1, mW - 2, 1 * scale);
  // Little heart/stripe decoration
  ctx.fillStyle = '#d2553a';
  ctx.fillRect(mx + 2 * scale, my + 7 * scale, 2 * scale, 1 * scale);
  ctx.fillRect(mx + 5 * scale, my + 7 * scale, 2 * scale, 1 * scale);
  ctx.fillRect(mx + 2 * scale, my + 8 * scale, 5 * scale, 1 * scale);
  ctx.fillRect(mx + 3 * scale, my + 9 * scale, 3 * scale, 1 * scale);
  ctx.fillRect(mx + 4 * scale, my + 10 * scale, 1 * scale, 1 * scale);

  // Steam (animated wavy) — always gently, more when "hot" (working)
  const t = performance.now() / 450;
  const steamCount = hot ? 3 : 2;
  ctx.fillStyle = 'rgba(255, 255, 255, 0.78)';
  for (let i = 0; i < steamCount; i++) {
    const baseX = mx + mW * (0.3 + i * 0.25);
    for (let k = 0; k < 4; k++) {
      const wave = Math.sin(t + i * 1.2 + k * 0.6) * 2 * scale;
      const puffY = my - 3 * scale - k * 3 * scale;
      const alpha = 0.75 - k * 0.18;
      ctx.fillStyle = `rgba(255, 255, 255, ${alpha})`;
      ctx.fillRect(baseX + wave, puffY, 2 * scale, 2 * scale);
    }
  }
}

/* ═══ Cactus in terracotta pot ═══ */
function drawCactus(x, y, accent) {
  const potW = 14 * scale;
  const potH = 8 * scale;
  const px = x - potW / 2;
  const py = y - potH;

  // Shadow
  ctx.fillStyle = 'rgba(42, 24, 16, 0.25)';
  ctx.fillRect(px + 2, py + potH, potW, 2 * scale);

  // Pot body — terracotta with zone accent trim
  ctx.fillStyle = '#b26a42';
  ctx.fillRect(px, py + 2 * scale, potW, potH - 2 * scale);
  // Pot rim (wider, lighter)
  ctx.fillStyle = '#d2825a';
  ctx.fillRect(px - 1 * scale, py, potW + 2 * scale, 3 * scale);
  // Trim stripe (agent color)
  ctx.fillStyle = accent;
  ctx.fillRect(px, py + 3 * scale, potW, 1 * scale);
  // Dark outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(px - 2 * scale, py - 1, potW + 4 * scale, 1);
  ctx.fillRect(px - 2 * scale, py + 2 * scale, 1, potH - 1 * scale);
  ctx.fillRect(px + potW + 1 * scale, py + 2 * scale, 1, potH - 1 * scale);
  ctx.fillRect(px, py + potH, potW, 1);
  ctx.fillRect(px - 1 * scale, py + 2 * scale, 1, 1);
  ctx.fillRect(px + potW, py + 2 * scale, 1, 1);
  // Pot side shadow
  ctx.fillStyle = '#8a4d2a';
  ctx.fillRect(px + potW - 2 * scale, py + 2 * scale, 2 * scale, potH - 2 * scale);
  // Soil
  ctx.fillStyle = '#4a2e18';
  ctx.fillRect(px + 1 * scale, py + 1 * scale, potW - 2 * scale, 1 * scale);

  // Cactus body — chunky pixel with arm
  const cxb = x;
  const cyb = py - 1;
  // Main trunk
  ctx.fillStyle = '#5c9a4a';
  ctx.fillRect(cxb - 3 * scale, cyb - 12 * scale, 6 * scale, 12 * scale);
  // Left arm (lower)
  ctx.fillRect(cxb - 6 * scale, cyb - 8 * scale, 3 * scale, 2 * scale);
  ctx.fillRect(cxb - 7 * scale, cyb - 10 * scale, 2 * scale, 3 * scale);
  // Right arm (upper)
  ctx.fillRect(cxb + 3 * scale, cyb - 11 * scale, 3 * scale, 2 * scale);
  ctx.fillRect(cxb + 5 * scale, cyb - 13 * scale, 2 * scale, 3 * scale);
  // Highlight
  ctx.fillStyle = '#7ab867';
  ctx.fillRect(cxb - 2 * scale, cyb - 11 * scale, 1 * scale, 10 * scale);
  ctx.fillRect(cxb - 6 * scale, cyb - 9 * scale, 1 * scale, 1);
  ctx.fillRect(cxb + 5 * scale, cyb - 12 * scale, 1 * scale, 1);
  // Shadow
  ctx.fillStyle = '#3d6b32';
  ctx.fillRect(cxb + 2 * scale, cyb - 11 * scale, 1 * scale, 10 * scale);
  // Dark outline
  ctx.fillStyle = '#2a3e1a';
  ctx.fillRect(cxb - 4 * scale, cyb - 12 * scale, 1, 12 * scale);
  ctx.fillRect(cxb + 3 * scale, cyb - 12 * scale, 1, 12 * scale);
  ctx.fillRect(cxb - 3 * scale, cyb - 13 * scale, 6 * scale, 1);
  // Spines (little dots)
  ctx.fillStyle = '#e0e0b0';
  ctx.fillRect(cxb - 2 * scale, cyb - 8 * scale, 1, 1);
  ctx.fillRect(cxb, cyb - 10 * scale, 1, 1);
  ctx.fillRect(cxb + 1 * scale, cyb - 5 * scale, 1, 1);
  ctx.fillRect(cxb - 1 * scale, cyb - 3 * scale, 1, 1);
  // Flower (pink bloom on top)
  ctx.fillStyle = '#d98ca0';
  ctx.fillRect(cxb - 2 * scale, cyb - 15 * scale, 4 * scale, 2 * scale);
  ctx.fillRect(cxb - 1 * scale, cyb - 16 * scale, 2 * scale, 1 * scale);
  ctx.fillStyle = '#e0a93b';
  ctx.fillRect(cxb, cyb - 14 * scale, 1 * scale, 1 * scale);
}

/* ═══ Bookshelf (archive) — irregular books + dust motes ═══ */
// Stable per-book randomness (generated once)
const _books1 = [
  { col: '#d2553a', hOff: -2, wJ: 0,  lean: 0 },
  { col: '#e0a93b', hOff: 3,  wJ: 2,  lean: 0 },
  { col: '#5c9a4a', hOff: -4, wJ: 0,  lean: 1 },
  { col: '#6aa7c9', hOff: 1,  wJ: 1,  lean: 0 },
  { col: '#a88cc5', hOff: -3, wJ: 0,  lean: 0 },
  { col: '#d98ca0', hOff: 4,  wJ: 2,  lean: 0 },
  { col: '#8a5f35', hOff: -1, wJ: 0,  lean: -1 },
  { col: '#5c9a4a', hOff: 2,  wJ: 1,  lean: 0 },
  { col: '#e0a93b', hOff: -5, wJ: 0,  lean: 0 },
];
const _books2 = [
  { col: '#5c9a4a', hOff: 0,  wJ: 1,  lean: 0 },
  { col: '#8a5f35', hOff: -3, wJ: 0,  lean: 0 },
  { col: '#e0a93b', hOff: 2,  wJ: 2,  lean: 0 },
  { col: '#a88cc5', hOff: -2, wJ: 0,  lean: 1 },
  { col: '#6aa7c9', hOff: 3,  wJ: 1,  lean: 0 },
  { col: '#d2553a', hOff: -4, wJ: 0,  lean: 0 },
  { col: '#d98ca0', hOff: 1,  wJ: 2,  lean: 0 },
  { col: '#c39665', hOff: -1, wJ: 0,  lean: -1 },
];
// Dust particle field (generated once, positions in zone-local coords)
const _dustMotes = Array.from({ length: 18 }, (_, i) => ({
  x: Math.random(),
  y: Math.random(),
  phase: Math.random() * Math.PI * 2,
  speed: 0.3 + Math.random() * 0.6,
  size: Math.random() < 0.35 ? 1 : 2,
  bright: 0.35 + Math.random() * 0.45,
}));

function drawBookshelf(zone) {
  const bx = (zone.x + 30) * scale;
  const by = (zone.y + zone.h * 0.36) * scale;
  const bw = (zone.w - 60) * scale;
  const bh = (zone.h * 0.48) * scale;
  // Cabinet body
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(bx, by, bw, bh);
  // Back panel (darker recess)
  ctx.fillStyle = '#4a3320';
  ctx.fillRect(bx + 2, by + 2, bw - 4, bh - 4);
  // Frame outline
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(bx - 2, by - 2, bw + 4, 2);
  ctx.fillRect(bx - 2, by + bh, bw + 4, 2);
  ctx.fillRect(bx - 2, by - 2, 2, bh + 4);
  ctx.fillRect(bx + bw, by - 2, 2, bh + 4);
  // Shelves
  const shelfY1 = by + bh * 0.48;
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(bx, shelfY1, bw, 2);
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(bx, shelfY1 - 1, bw, 1);
  // Shelf bottom lip
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(bx, by + bh - 2, bw, 2);

  // Row 1 — irregular heights/widths/lean
  const rowTop1 = by + 6 * scale;
  const rowH1 = shelfY1 - rowTop1 - 1 * scale;
  const totalW = bw - 12;
  let x = bx + 6;
  const baseW1 = totalW / _books1.length;
  _books1.forEach((b, i) => {
    const w = Math.max(4 * scale, baseW1 + b.wJ * scale - 1);
    const h = Math.max(rowH1 * 0.5, rowH1 + b.hOff * scale);
    const y = shelfY1 - 1 - h;
    drawBookSpine(x, y, w - 2, h, b.col, b.lean, i);
    x += w;
  });

  // Row 2
  const rowTop2 = shelfY1 + 4;
  const rowH2 = by + bh - rowTop2 - 3;
  x = bx + 6;
  const baseW2 = totalW / _books2.length;
  _books2.forEach((b, i) => {
    const w = Math.max(4 * scale, baseW2 + b.wJ * scale - 1);
    const h = Math.max(rowH2 * 0.6, rowH2 + b.hOff * scale);
    const y = rowTop2 + (rowH2 - h);
    drawBookSpine(x, y, w - 2, h, b.col, b.lean, i + 10);
    x += w;
  });

  // A couple of books stacked flat on top of row 2 (fills gap near right)
  const stackX = bx + bw - 40 * scale;
  ctx.fillStyle = '#a88cc5';
  ctx.fillRect(stackX, shelfY1 - 10 * scale, 30 * scale, 3 * scale);
  ctx.fillStyle = '#e0a93b';
  ctx.fillRect(stackX + 2 * scale, shelfY1 - 13 * scale, 28 * scale, 3 * scale);
  ctx.fillStyle = 'rgba(0,0,0,0.25)';
  ctx.fillRect(stackX, shelfY1 - 7 * scale, 30 * scale, 1);

  // ── Dust motes drifting around the shelf ──
  const t = performance.now() / 1000;
  ctx.save();
  for (const m of _dustMotes) {
    const lx = zone.x + 20 + m.x * (zone.w - 40);
    const ly = zone.y + 20 + m.y * (zone.h - 40);
    // Slow vertical drift + gentle horizontal sway
    const dy = Math.sin(t * m.speed + m.phase) * 6;
    const dx = Math.cos(t * m.speed * 0.6 + m.phase) * 3;
    const twinkle = 0.5 + 0.5 * Math.sin(t * 2 + m.phase);
    ctx.fillStyle = `rgba(255, 245, 220, ${m.bright * (0.5 + 0.5 * twinkle)})`;
    ctx.fillRect((lx + dx) * scale, (ly + dy) * scale, m.size, m.size);
  }
  ctx.restore();
}

function drawBookSpine(x, y, w, h, col, lean, seed) {
  // Base
  ctx.fillStyle = col;
  if (lean !== 0) {
    // Slight lean: draw as parallelogram via two rects stacked w/ offset
    ctx.save();
    ctx.translate(x + w / 2, y + h / 2);
    ctx.rotate(lean * 0.08);
    ctx.fillRect(-w / 2, -h / 2, w, h);
    ctx.fillStyle = 'rgba(255,255,255,0.22)';
    ctx.fillRect(-w / 2, -h / 2, 1 * scale, h);
    ctx.fillStyle = 'rgba(0,0,0,0.25)';
    ctx.fillRect(w / 2 - 1 * scale, -h / 2, 1 * scale, h);
    // Title bands
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fillRect(-w / 2 + 1, -h / 4, w - 2, 1);
    if (h > 28) ctx.fillRect(-w / 2 + 1, h / 4, w - 2, 1);
    ctx.restore();
    return;
  }
  ctx.fillRect(x, y, w, h);
  // Highlight left edge
  ctx.fillStyle = 'rgba(255,255,255,0.22)';
  ctx.fillRect(x, y, 1 * scale, h);
  // Shadow right edge
  ctx.fillStyle = 'rgba(0,0,0,0.25)';
  ctx.fillRect(x + w - 1 * scale, y, 1 * scale, h);
  // Title bands (vary by seed)
  if (seed % 2 === 0) {
    ctx.fillStyle = 'rgba(255,255,255,0.35)';
    ctx.fillRect(x + 1, y + h * 0.2, w - 2, 1);
    if (h > 26) ctx.fillRect(x + 1, y + h * 0.55, w - 2, 1);
  }
  if (seed % 3 === 0) {
    // Gold foil dot
    ctx.fillStyle = '#e0a93b';
    ctx.fillRect(x + w / 2 - 1, y + h * 0.75, 2, 2);
  }
}

/* ═══ Cork board (receipt) — swaying receipts + fairy lights ═══ */
function drawCorkBoard(zone) {
  const bx = (zone.x + 32) * scale;
  const by = (zone.y + zone.h * 0.32) * scale;
  const bw = (zone.w - 64) * scale;
  const bh = (zone.h * 0.58) * scale;
  // Cork surface
  ctx.fillStyle = '#c39665';
  ctx.fillRect(bx, by, bw, bh);
  // Speckles (deterministic)
  for (let i = 0; i < 60; i++) {
    const r = ((i * 9301 + 49297) % 233280) / 233280;
    const r2 = ((i * 7333 + 12345) % 10007) / 10007;
    ctx.fillStyle = `rgba(${80 + r * 40}, ${50 + r2 * 30}, ${20 + r * 20}, 0.35)`;
    ctx.fillRect(bx + r * bw, by + r2 * bh, 1.5 * scale, 1.5 * scale);
  }
  // Frame
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(bx - 3, by - 3, bw + 6, 3);
  ctx.fillRect(bx - 3, by + bh, bw + 6, 3);
  ctx.fillRect(bx - 3, by - 3, 3, bh + 6);
  ctx.fillRect(bx + bw, by - 3, 3, bh + 6);
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(bx - 2, by - 2, bw + 4, 1);
  ctx.fillRect(bx - 2, by - 2, 1, bh + 4);

  const t = performance.now() / 1000;

  // ── Pinned receipts, swaying gently in the breeze ──
  const receipts = [
    { x: 0.15, y: 0.2,  rot: -0.05, col: '#fbf3dd', ph: 0.0 },
    { x: 0.52, y: 0.15, rot: 0.03,  col: '#fdf5e0', ph: 1.3 },
    { x: 0.32, y: 0.52, rot: -0.02, col: '#f7e5c0', ph: 2.5 },
    { x: 0.70, y: 0.55, rot: 0.04,  col: '#fbf3dd', ph: 3.7 },
  ];
  receipts.forEach(r => {
    const rx = bx + r.x * bw;
    const ry = by + r.y * bh;
    const rw = 50 * scale, rh = 36 * scale;
    // Sway: rotation oscillates, paper swings from pin (top center)
    const sway = Math.sin(t * 1.2 + r.ph) * 0.04 + Math.sin(t * 2.3 + r.ph) * 0.015;
    const rot = r.rot + sway;
    ctx.save();
    // Pivot at pin (top-center of paper)
    const pinX = rx + rw / 2;
    const pinY = ry + 4 * scale;
    ctx.translate(pinX, pinY);
    ctx.rotate(rot);
    // Shadow
    ctx.fillStyle = 'rgba(0,0,0,0.28)';
    ctx.fillRect(-rw / 2 + 2, -2 * scale + 2, rw, rh);
    // Paper
    ctx.fillStyle = r.col;
    ctx.fillRect(-rw / 2, -2 * scale, rw, rh);
    // Lines
    ctx.fillStyle = '#9a8670';
    ctx.fillRect(-rw / 2 + 5, -2 * scale + 6, rw - 14, 1);
    ctx.fillRect(-rw / 2 + 5, -2 * scale + 12, rw - 18, 1);
    ctx.fillRect(-rw / 2 + 5, -2 * scale + 18, rw - 10, 1);
    ctx.fillRect(-rw / 2 + 5, -2 * scale + 24, rw - 20, 1);
    // Pin
    ctx.fillStyle = '#d2553a';
    ctx.fillRect(-2, -2 * scale, 4, 4);
    ctx.fillStyle = '#fff';
    ctx.fillRect(-1, -2 * scale + 1, 1, 1);
    ctx.restore();
  });

  // ── Fairy lights strung along the frame edge ──
  const bulbCount = 22;
  const edgeInset = 6;
  // Points along the frame perimeter (top, right, bottom, left)
  for (let i = 0; i < bulbCount; i++) {
    const u = i / (bulbCount - 1);
    // Sag: tiny sine droop between frame pins
    const droop = Math.sin(u * Math.PI * 4) * 1.2 * scale;
    const px = bx - edgeInset + u * (bw + edgeInset * 2);
    const py = by - edgeInset + droop;
    // Wire
    if (i > 0) {
      const pu = (i - 1) / (bulbCount - 1);
      const pdroop = Math.sin(pu * Math.PI * 4) * 1.2 * scale;
      const ppx = bx - edgeInset + pu * (bw + edgeInset * 2);
      const ppy = by - edgeInset + pdroop;
      ctx.strokeStyle = 'rgba(42,24,16,0.7)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(ppx, ppy);
      ctx.lineTo(px, py);
      ctx.stroke();
    }
    // Twinkling bulb — phase per bulb
    const twink = 0.55 + 0.45 * Math.sin(t * 2.5 + i * 0.9);
    // Glow halo
    ctx.fillStyle = `rgba(255, 215, 110, ${0.25 * twink})`;
    ctx.beginPath();
    ctx.arc(px, py, 4 * scale, 0, Math.PI * 2);
    ctx.fill();
    // Bulb core
    ctx.fillStyle = `rgba(255, 225, 130, ${0.7 + 0.3 * twink})`;
    ctx.fillRect(px - 1 * scale, py - 1 * scale, 2 * scale, 2 * scale);
    // Hot center
    ctx.fillStyle = `rgba(255, 255, 220, ${twink})`;
    ctx.fillRect(px, py, 1, 1);
  }
}

/* ═══ Alarm bell (incident) ═══ */
function drawAlarmBell(zone) {
  const cx = (zone.x + zone.w / 2) * scale;
  const cy = (zone.y + zone.h * 0.6) * scale;
  const r = 28 * scale;
  // Stand pole
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(cx - 3 * scale, cy - r * 0.4, 6 * scale, r * 1.4);
  // Bell body (pixel-dome)
  ctx.fillStyle = '#d2553a';
  ctx.fillRect(cx - r * 0.9, cy - r * 0.2, r * 1.8, r * 0.8);
  ctx.fillRect(cx - r * 0.7, cy - r * 0.5, r * 1.4, r * 0.4);
  ctx.fillRect(cx - r * 0.5, cy - r * 0.8, r, r * 0.4);
  // Shine
  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  ctx.fillRect(cx - r * 0.65, cy - r * 0.4, 3 * scale, r * 0.6);
  // Base
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(cx - r * 0.9, cy + r * 0.6, r * 1.8, 3 * scale);
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(cx - r * 1.2, cy + r * 0.63, r * 2.4, 4 * scale);
  // "ALL QUIET" sign
  ctx.font = `${9 * scale}px 'DungGeunMo','Galmuri11',monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';
  ctx.fillStyle = '#fbf3dd';
  const signY = cy + r * 0.9;
  ctx.fillRect(cx - 32 * scale, signY, 64 * scale, 16 * scale);
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(cx - 33 * scale, signY - 1, 66 * scale, 1);
  ctx.fillRect(cx - 33 * scale, signY + 16 * scale, 66 * scale, 1);
  ctx.fillText('조용함 ✿', cx, signY + 3 * scale);
}

/* ═══ Lounge: sofa + water cooler + big plant + coffee table ═══ */
function drawLounge(zone) {
  const zx = zone.x * scale, zy = zone.y * scale;
  const zw = zone.w * scale, zh = zone.h * scale;

  // Warm lounge floor mat (big area rug)
  ctx.fillStyle = '#b07a4a';
  ctx.fillRect(zx + 40 * scale, zy + 30 * scale, zw - 80 * scale, zh - 60 * scale);
  ctx.fillStyle = '#8a5a2e';
  ctx.fillRect(zx + 40 * scale, zy + 30 * scale, zw - 80 * scale, 3 * scale);
  ctx.fillRect(zx + 40 * scale, zy + zh - 33 * scale, zw - 80 * scale, 3 * scale);
  ctx.fillRect(zx + 40 * scale, zy + 30 * scale, 3 * scale, zh - 60 * scale);
  ctx.fillRect(zx + zw - 43 * scale, zy + 30 * scale, 3 * scale, zh - 60 * scale);
  // Inner rug stripe
  ctx.fillStyle = '#d29a6a';
  ctx.fillRect(zx + 60 * scale, zy + 50 * scale, zw - 120 * scale, 2 * scale);
  ctx.fillRect(zx + 60 * scale, zy + zh - 52 * scale, zw - 120 * scale, 2 * scale);

  // Sofa (centered, pixel-chunky)
  const sofaCX = zone.x + zone.w / 2;
  const sofaCY = zone.y + zone.h * 0.55;
  drawSofa(sofaCX, sofaCY);

  // Water cooler (left side)
  drawWaterCooler(zone.x + 90, zone.y + zone.h * 0.5);

  // Big potted plant (right side)
  drawBigPlant(zone.x + zone.w - 110, zone.y + zone.h * 0.5);

  // Coffee table in front of sofa
  drawCoffeeTable(sofaCX, sofaCY + 58);

  // Floor lamp (far right end)
  drawFloorLamp(zone.x + zone.w - 40, zone.y + zone.h * 0.4);
}

function drawSofa(vcx, vcy) {
  const cx = vcx * scale, cy = vcy * scale;
  const sw = 220 * scale;  // sofa width
  const sh = 46 * scale;   // back height
  const seatH = 24 * scale;
  const x = cx - sw / 2;
  const y = cy - sh / 2;

  // Shadow
  ctx.fillStyle = 'rgba(42, 24, 16, 0.3)';
  ctx.fillRect(x + 4 * scale, y + sh + seatH + 2 * scale, sw, 4 * scale);

  // Backrest
  ctx.fillStyle = '#c45a5a';          // warm red
  ctx.fillRect(x, y, sw, sh);
  // Backrest pillow ridges (3 cushions)
  ctx.fillStyle = '#a84545';
  for (let i = 1; i < 3; i++) {
    const sx = x + (sw / 3) * i;
    ctx.fillRect(sx, y + 2 * scale, 2 * scale, sh - 4 * scale);
  }
  // Backrest bevel
  ctx.fillStyle = '#e07575';
  ctx.fillRect(x + 2, y + 2, sw - 4, 2 * scale);
  ctx.fillStyle = '#803030';
  ctx.fillRect(x + 2, y + sh - 4 * scale, sw - 4, 2 * scale);
  // Dark outline (back)
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - 2, y - 2, sw + 4, 2);
  ctx.fillRect(x - 2, y, 2, sh);
  ctx.fillRect(x + sw, y, 2, sh);

  // Seat cushions
  const sy2 = y + sh;
  ctx.fillStyle = '#d86b6b';
  ctx.fillRect(x, sy2, sw, seatH);
  // Seat seams
  ctx.fillStyle = '#a84545';
  for (let i = 1; i < 3; i++) {
    const sx = x + (sw / 3) * i;
    ctx.fillRect(sx, sy2, 2 * scale, seatH);
  }
  // Seat bevel
  ctx.fillStyle = '#f28888';
  ctx.fillRect(x + 2, sy2, sw - 4, 2 * scale);
  ctx.fillStyle = '#803030';
  ctx.fillRect(x + 2, sy2 + seatH - 3 * scale, sw - 4, 2 * scale);
  // Seat outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - 2, sy2, 2, seatH);
  ctx.fillRect(x + sw, sy2, 2, seatH);
  ctx.fillRect(x - 2, sy2 + seatH, sw + 4, 2);

  // Armrests (raised, chunky)
  const armW = 14 * scale;
  const armH = sh + seatH - 4 * scale;
  // Left arm
  ctx.fillStyle = '#b04848';
  ctx.fillRect(x - armW + 4 * scale, y + 6 * scale, armW, armH);
  ctx.fillStyle = '#d86b6b';
  ctx.fillRect(x - armW + 4 * scale, y + 6 * scale, 2 * scale, armH);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - armW + 2 * scale, y + 4 * scale, armW + 2, 2);
  ctx.fillRect(x - armW + 2 * scale, y + 6 * scale, 2, armH);
  ctx.fillRect(x - armW + 4 * scale, y + 6 * scale + armH, armW, 2);
  // Right arm
  ctx.fillStyle = '#b04848';
  ctx.fillRect(x + sw - 4 * scale, y + 6 * scale, armW, armH);
  ctx.fillStyle = '#d86b6b';
  ctx.fillRect(x + sw - 4 * scale, y + 6 * scale, 2 * scale, armH);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x + sw - 4 * scale, y + 4 * scale, armW + 2, 2);
  ctx.fillRect(x + sw + armW - 2 * scale, y + 6 * scale, 2, armH);
  ctx.fillRect(x + sw - 4 * scale, y + 6 * scale + armH, armW + 2, 2);

  // Feet
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(x + 6 * scale, sy2 + seatH, 6 * scale, 5 * scale);
  ctx.fillRect(x + sw - 12 * scale, sy2 + seatH, 6 * scale, 5 * scale);

  // Little decorative cushions on seat
  // Yellow pillow left
  ctx.fillStyle = '#e0a93b';
  ctx.fillRect(x + 26 * scale, sy2 + 4 * scale, 16 * scale, 12 * scale);
  ctx.fillStyle = '#f0c25a';
  ctx.fillRect(x + 27 * scale, sy2 + 5 * scale, 3 * scale, 2 * scale);
  ctx.fillStyle = '#a8782a';
  ctx.fillRect(x + 26 * scale, sy2 + 14 * scale, 16 * scale, 2 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x + 25 * scale, sy2 + 3 * scale, 18 * scale, 1);
  ctx.fillRect(x + 25 * scale, sy2 + 16 * scale, 18 * scale, 1);
  ctx.fillRect(x + 25 * scale, sy2 + 4 * scale, 1, 12 * scale);
  ctx.fillRect(x + 42 * scale, sy2 + 4 * scale, 1, 12 * scale);
  // Teal pillow right
  ctx.fillStyle = '#5fa8a0';
  ctx.fillRect(x + sw - 44 * scale, sy2 + 3 * scale, 18 * scale, 14 * scale);
  ctx.fillStyle = '#7fc8c0';
  ctx.fillRect(x + sw - 43 * scale, sy2 + 4 * scale, 3 * scale, 2 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x + sw - 45 * scale, sy2 + 2 * scale, 20 * scale, 1);
  ctx.fillRect(x + sw - 45 * scale, sy2 + 17 * scale, 20 * scale, 1);
  ctx.fillRect(x + sw - 45 * scale, sy2 + 3 * scale, 1, 14 * scale);
  ctx.fillRect(x + sw - 26 * scale, sy2 + 3 * scale, 1, 14 * scale);
}

function drawWaterCooler(vcx, vcy) {
  const cx = vcx * scale, cy = vcy * scale;
  const w = 28 * scale;
  const h = 80 * scale;
  const x = cx - w / 2;
  const y = cy - h / 2;

  // Shadow
  ctx.fillStyle = 'rgba(42, 24, 16, 0.28)';
  ctx.fillRect(x + 3, y + h, w, 4 * scale);

  // Bottle (upper part — blue water)
  const bottleH = 28 * scale;
  ctx.fillStyle = '#8ac8d8';
  ctx.fillRect(x + 3 * scale, y, w - 6 * scale, bottleH);
  // Bottle neck
  ctx.fillStyle = '#6ab0c2';
  ctx.fillRect(x + 10 * scale, y - 3 * scale, w - 20 * scale, 3 * scale);
  // Bubbles
  const t = performance.now() / 400;
  ctx.fillStyle = '#c0e8f0';
  for (let i = 0; i < 3; i++) {
    const by = y + bottleH - 4 * scale - ((t * 3 + i * 8) % bottleH);
    const bx = x + 8 * scale + (i * 5 * scale);
    ctx.fillRect(bx, by, 2 * scale, 2 * scale);
  }
  // Bottle outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x + 3 * scale, y - 1, w - 6 * scale, 1);
  ctx.fillRect(x + 2 * scale, y, 1, bottleH);
  ctx.fillRect(x + w - 3 * scale, y, 1, bottleH);

  // Body (white/cream)
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(x, y + bottleH, w, h - bottleH);
  ctx.fillStyle = '#d9b986';
  ctx.fillRect(x + w - 3 * scale, y + bottleH, 3 * scale, h - bottleH);
  // Outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x - 1, y + bottleH, 1, h - bottleH + 1);
  ctx.fillRect(x + w, y + bottleH, 1, h - bottleH + 1);
  ctx.fillRect(x - 1, y + h, w + 2, 1);

  // Tap buttons (red hot, blue cold)
  ctx.fillStyle = '#d2553a';
  ctx.fillRect(x + 6 * scale, y + bottleH + 8 * scale, 6 * scale, 4 * scale);
  ctx.fillStyle = '#6aa7c9';
  ctx.fillRect(x + w - 12 * scale, y + bottleH + 8 * scale, 6 * scale, 4 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x + 6 * scale, y + bottleH + 7 * scale, 6 * scale, 1);
  ctx.fillRect(x + w - 12 * scale, y + bottleH + 7 * scale, 6 * scale, 1);
  // Drip tray
  ctx.fillStyle = '#8a6a4a';
  ctx.fillRect(x + 3 * scale, y + bottleH + 18 * scale, w - 6 * scale, 4 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(x + 3 * scale, y + bottleH + 17 * scale, w - 6 * scale, 1);
  ctx.fillRect(x + 3 * scale, y + bottleH + 22 * scale, w - 6 * scale, 1);
}

function drawBigPlant(vcx, vcy) {
  const cx = vcx * scale, cy = vcy * scale;
  // Pot
  const pw = 40 * scale;
  const ph = 36 * scale;
  const px = cx - pw / 2;
  const py = cy + 6 * scale;

  // Shadow
  ctx.fillStyle = 'rgba(42, 24, 16, 0.28)';
  ctx.fillRect(px + 4, py + ph, pw, 4 * scale);

  // Pot (terracotta)
  ctx.fillStyle = '#b26a42';
  ctx.fillRect(px + 2 * scale, py + 4 * scale, pw - 4 * scale, ph - 4 * scale);
  // Rim (wider)
  ctx.fillStyle = '#d2825a';
  ctx.fillRect(px - 2 * scale, py, pw + 4 * scale, 5 * scale);
  // Side shadow
  ctx.fillStyle = '#8a4d2a';
  ctx.fillRect(px + pw - 5 * scale, py + 4 * scale, 3 * scale, ph - 4 * scale);
  // Outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(px - 3 * scale, py - 1, pw + 6 * scale, 1);
  ctx.fillRect(px - 3 * scale, py + 5 * scale, 1, ph - 5 * scale);
  ctx.fillRect(px + pw + 2 * scale, py + 5 * scale, 1, ph - 5 * scale);
  ctx.fillRect(px + 2 * scale, py + ph, pw - 4 * scale, 1);
  // Soil
  ctx.fillStyle = '#4a2e18';
  ctx.fillRect(px + 2 * scale, py + 4 * scale, pw - 4 * scale, 2 * scale);

  // Monstera-style broad leaves (layered fan)
  // Trunk / stems
  ctx.fillStyle = '#3d6b2e';
  ctx.fillRect(cx - 2 * scale, py - 14 * scale, 2 * scale, 18 * scale);
  ctx.fillRect(cx, py - 20 * scale, 2 * scale, 24 * scale);
  ctx.fillRect(cx + 2 * scale, py - 12 * scale, 2 * scale, 16 * scale);

  // Leaf 1 (left big)
  drawLeaf(cx - 12 * scale, py - 18 * scale, -1, '#4a8a3a', '#5c9a4a', '#7ab867');
  // Leaf 2 (center tall)
  drawLeaf(cx, py - 30 * scale, 0, '#5c9a4a', '#7ab867', '#a8d890');
  // Leaf 3 (right)
  drawLeaf(cx + 12 * scale, py - 22 * scale, 1, '#4a8a3a', '#5c9a4a', '#7ab867');
  // Tiny side leaf
  drawLeaf(cx - 18 * scale, py - 8 * scale, -1.3, '#3d6b2e', '#4a8a3a', '#5c9a4a');
  drawLeaf(cx + 18 * scale, py - 8 * scale, 1.3, '#3d6b2e', '#4a8a3a', '#5c9a4a');
}

function drawLeaf(cx, tipY, dir, dark, mid, light) {
  // Elongated oval leaf drawn with pixel rectangles
  // dir: -1 left, 0 up, 1 right
  const baseY = tipY + 20 * scale;
  const sway = Math.sin(performance.now() / 900 + cx * 0.01) * 1 * scale;
  const tipX = cx + dir * 10 * scale + sway;
  // Shape (stacked rects for a teardrop)
  ctx.fillStyle = dark;
  for (let i = 0; i < 10; i++) {
    const t = i / 9;
    const ly = tipY + i * 2 * scale;
    const lw = (i < 2 ? 2 + i * 2 : (i < 7 ? 8 + (7 - i) : 9 - i)) * scale;
    const lx = cx + dir * i * 1.2 * scale - lw / 2 + sway * (i / 9);
    ctx.fillRect(lx, ly, lw, 2 * scale);
  }
  // Highlight midrib
  ctx.fillStyle = light;
  for (let i = 1; i < 9; i++) {
    const ly = tipY + i * 2 * scale;
    const lx = cx + dir * i * 1.2 * scale + sway * (i / 9);
    ctx.fillRect(lx - 1 * scale, ly, 1 * scale, 1 * scale);
  }
  // Mid tone fill area
  ctx.fillStyle = mid;
  for (let i = 2; i < 8; i++) {
    const ly = tipY + i * 2 * scale + 1 * scale;
    const lw = Math.max(2, (i < 7 ? 6 + (7 - i) : 9 - i)) * scale;
    const lx = cx + dir * i * 1.2 * scale - lw / 2 + sway * (i / 9);
    ctx.fillRect(lx + 1, ly - 1 * scale, lw - 2, 1 * scale);
  }
}

function drawCoffeeTable(vcx, vcy) {
  const cx = vcx * scale, cy = vcy * scale;
  const tw = 90 * scale;
  const th = 8 * scale;
  // Top
  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(cx - tw/2, cy, tw, th);
  ctx.fillStyle = '#b08555';
  ctx.fillRect(cx - tw/2, cy, tw, 2 * scale);
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(cx - tw/2, cy + th - 2 * scale, tw, 2 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(cx - tw/2 - 1, cy - 1, tw + 2, 1);
  ctx.fillRect(cx - tw/2 - 1, cy + th, tw + 2, 1);
  ctx.fillRect(cx - tw/2 - 1, cy, 1, th);
  ctx.fillRect(cx + tw/2, cy, 1, th);
  // Legs
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(cx - tw/2 + 4 * scale, cy + th, 4 * scale, 10 * scale);
  ctx.fillRect(cx + tw/2 - 8 * scale, cy + th, 4 * scale, 10 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(cx - tw/2 + 4 * scale, cy + th + 10 * scale, 4 * scale, 1);
  ctx.fillRect(cx + tw/2 - 8 * scale, cy + th + 10 * scale, 4 * scale, 1);
  // Magazine on table
  ctx.fillStyle = '#d2553a';
  ctx.fillRect(cx - 20 * scale, cy - 2 * scale, 24 * scale, 2 * scale);
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(cx - 18 * scale, cy - 1 * scale, 6 * scale, 1);
  // Mug on table
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(cx + 18 * scale, cy - 5 * scale, 8 * scale, 6 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(cx + 17 * scale, cy - 5 * scale, 1, 6 * scale);
  ctx.fillRect(cx + 26 * scale, cy - 5 * scale, 1, 6 * scale);
  ctx.fillRect(cx + 18 * scale, cy - 6 * scale, 8 * scale, 1);
  ctx.fillStyle = '#5a3a22';
  ctx.fillRect(cx + 19 * scale, cy - 4 * scale, 6 * scale, 1 * scale);
  // Steam
  const t = performance.now() / 400;
  ctx.fillStyle = 'rgba(255,255,255,0.7)';
  for (let i = 0; i < 3; i++) {
    const wave = Math.sin(t + i) * 1 * scale;
    ctx.fillRect(cx + 20 * scale + i * 2 * scale + wave, cy - 8 * scale - i * 2 * scale, 1 * scale, 1 * scale);
  }
}

function drawFloorLamp(vcx, vcy) {
  const cx = vcx * scale, cy = vcy * scale;
  // Base
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(cx - 6 * scale, cy + 60 * scale, 12 * scale, 2 * scale);
  ctx.fillStyle = '#6a4525';
  ctx.fillRect(cx - 5 * scale, cy + 58 * scale, 10 * scale, 2 * scale);
  // Pole
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(cx - 1 * scale, cy - 20 * scale, 2 * scale, 78 * scale);
  // Shade (trapezoidal, warm yellow)
  ctx.fillStyle = '#e0a93b';
  ctx.fillRect(cx - 14 * scale, cy - 26 * scale, 28 * scale, 10 * scale);
  ctx.fillStyle = '#f0c25a';
  ctx.fillRect(cx - 10 * scale, cy - 28 * scale, 20 * scale, 2 * scale);
  ctx.fillStyle = '#a87820';
  ctx.fillRect(cx - 14 * scale, cy - 18 * scale, 28 * scale, 2 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(cx - 14 * scale, cy - 28 * scale, 28 * scale, 1);
  ctx.fillRect(cx - 14 * scale, cy - 16 * scale, 28 * scale, 1);
  ctx.fillRect(cx - 15 * scale, cy - 28 * scale, 1, 12 * scale);
  ctx.fillRect(cx + 14 * scale, cy - 28 * scale, 1, 12 * scale);
  // Glow
  ctx.save();
  const grad = ctx.createRadialGradient(cx, cy - 20 * scale, 0, cx, cy - 20 * scale, 60 * scale);
  grad.addColorStop(0, 'rgba(255, 220, 130, 0.28)');
  grad.addColorStop(1, 'rgba(255, 220, 130, 0)');
  ctx.fillStyle = grad;
  ctx.fillRect(cx - 60 * scale, cy - 80 * scale, 120 * scale, 120 * scale);
  ctx.restore();
}

/* ═══ Orange Pixel Cat NPC ═══ */
class Cat {
  constructor() {
    const lounge = ZONE_MAP.lounge;
    this.x = lounge.x + lounge.w * 0.3;
    this.y = lounge.y + lounge.h * 0.78;
    this.tx = this.x; this.ty = this.y;
    this.state = 'wander';    // wander | sleep | sit | pet
    this.stateTimer = 3 + Math.random() * 3;
    this.facingRight = true;
    this.bobPhase = Math.random() * Math.PI * 2;
    this.walkPhase = 0;
    this.zPhase = 0;
    this.petPurrPhase = 0;
    this.heartCooldown = 0;
  }
  pet(clickX) {
    this.facingRight = clickX > this.x;
    this.state = 'pet';
    this.stateTimer = 3.5;
    this.petPurrPhase = 0;
    for (let i = 0; i < 5; i++) {
      spawnRedHeart(
        this.x + (Math.random() - 0.5) * 10,
        this.y - 14 - Math.random() * 4,
      );
    }
    this.heartCooldown = 0.2;
    window.Audio8?.meow();
  }
  update(dt) {
    this.stateTimer -= dt;
    this.bobPhase += dt * 4;
    this.zPhase += dt;

    if (this.state === 'pet') {
      this.petPurrPhase += dt * 6;
      this.heartCooldown -= dt;
      if (this.heartCooldown <= 0) {
        spawnRedHeart(
          this.x + (Math.random() - 0.5) * 8,
          this.y - 14 - Math.random() * 3,
        );
        this.heartCooldown = 0.18 + Math.random() * 0.18;
      }
      if (this.stateTimer <= 0) {
        this.state = 'sit';
        this.stateTimer = 1.2;
      }
      return;
    }

    if (this.stateTimer <= 0) {
      this.pickNewAction();
    }

    if (this.state === 'wander') {
      const dx = this.tx - this.x, dy = this.ty - this.y;
      const dist = Math.sqrt(dx*dx + dy*dy);
      if (dist > 1) {
        this.walkPhase += dt * 8;
        const step = 22 * dt;
        this.x += (dx / dist) * Math.min(step, dist);
        this.y += (dy / dist) * Math.min(step, dist);
      } else if (this.stateTimer > 1) {
        // arrived, linger briefly then new target
        this.stateTimer = 0.4;
      }
    }
  }
  pickNewAction() {
    const lounge = ZONE_MAP.lounge;
    const r = Math.random();
    if (r < 0.35) {
      // Climb onto sofa to sleep
      this.state = 'sleep';
      this.tx = lounge.x + lounge.w * 0.5 + (Math.random() - 0.5) * 60;
      this.ty = lounge.y + lounge.h * 0.48;
      this.x = this.tx; this.y = this.ty;
      this.stateTimer = 8 + Math.random() * 6;
    } else if (r < 0.55) {
      // Sit and watch
      this.state = 'sit';
      this.stateTimer = 2 + Math.random() * 2;
    } else {
      // Wander somewhere new in lounge
      this.state = 'wander';
      const nx = lounge.x + 40 + Math.random() * (lounge.w - 80);
      const ny = lounge.y + lounge.h * 0.65 + Math.random() * (lounge.h * 0.25);
      this.facingRight = nx > this.x;
      this.tx = nx; this.ty = ny;
      this.stateTimer = 4 + Math.random() * 4;
    }
  }
}
const cat = new Cat();

function drawCat(c) {
  const sx = c.x * scale, sy = c.y * scale;
  const orange = '#e08a3a';
  const orangeDark = '#b8651e';
  const orangeLight = '#f0a85c';
  const cream = '#fbe4b8';

  // Shadow
  ctx.fillStyle = 'rgba(42, 24, 16, 0.3)';
  ctx.beginPath();
  ctx.ellipse(sx, sy + 5 * scale, 10 * scale, 3 * scale, 0, 0, Math.PI * 2);
  ctx.fill();

  if (c.state === 'sleep') {
    // Curled up ball shape
    const cx = sx, cy = sy;
    // Body (oval-ish, curled)
    ctx.fillStyle = orange;
    ctx.fillRect(cx - 10 * scale, cy - 6 * scale, 20 * scale, 10 * scale);
    ctx.fillRect(cx - 8 * scale, cy - 8 * scale, 16 * scale, 2 * scale);
    ctx.fillRect(cx - 12 * scale, cy - 4 * scale, 24 * scale, 6 * scale);
    ctx.fillRect(cx - 10 * scale, cy + 2 * scale, 20 * scale, 4 * scale);
    // Stripes
    ctx.fillStyle = orangeDark;
    ctx.fillRect(cx - 8 * scale, cy - 6 * scale, 1 * scale, 4 * scale);
    ctx.fillRect(cx - 4 * scale, cy - 8 * scale, 1 * scale, 4 * scale);
    ctx.fillRect(cx + 1 * scale, cy - 7 * scale, 1 * scale, 4 * scale);
    ctx.fillRect(cx + 6 * scale, cy - 6 * scale, 1 * scale, 4 * scale);
    // Highlight
    ctx.fillStyle = orangeLight;
    ctx.fillRect(cx - 10 * scale, cy - 5 * scale, 20 * scale, 1 * scale);
    // Tail curled
    ctx.fillStyle = orange;
    ctx.fillRect(cx + 8 * scale, cy - 3 * scale, 4 * scale, 3 * scale);
    ctx.fillRect(cx + 10 * scale, cy - 1 * scale, 2 * scale, 2 * scale);
    ctx.fillStyle = orangeDark;
    ctx.fillRect(cx + 9 * scale, cy - 2 * scale, 1 * scale, 1 * scale);
    // Ear tip visible
    ctx.fillStyle = orange;
    ctx.fillRect(cx - 8 * scale, cy - 9 * scale, 3 * scale, 2 * scale);
    ctx.fillRect(cx - 10 * scale, cy - 7 * scale, 2 * scale, 2 * scale);
    // Closed eye
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(cx - 5 * scale, cy - 4 * scale, 2 * scale, 1 * scale);
    // Outline
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(cx - 12 * scale, cy - 4 * scale, 1, 6 * scale);
    ctx.fillRect(cx + 12 * scale, cy - 3 * scale, 1, 5 * scale);
    ctx.fillRect(cx - 10 * scale, cy - 9 * scale, 3 * scale, 1);
    ctx.fillRect(cx - 10 * scale, cy + 6 * scale, 20 * scale, 1);

    // Zzz particles
    const zt = c.zPhase;
    for (let i = 0; i < 3; i++) {
      const phase = (zt - i * 0.7) % 3;
      if (phase < 0 || phase > 2.5) continue;
      const zAlpha = phase < 0.3 ? phase / 0.3 : (phase > 2 ? (2.5 - phase) / 0.5 : 1);
      const zy = cy - 12 * scale - phase * 12 * scale;
      const zx = cx + 6 * scale + Math.sin(phase * 2) * 2 * scale;
      ctx.save();
      ctx.globalAlpha = zAlpha * 0.85;
      ctx.fillStyle = '#6aa7c9';
      // Pixel Z
      const zs = (4 + i) * scale * 0.8;
      ctx.fillRect(zx, zy, zs, 1 * scale);
      ctx.fillRect(zx, zy + zs - 1 * scale, zs, 1 * scale);
      // diagonal
      for (let k = 0; k < 4; k++) {
        ctx.fillRect(zx + (zs - 1 * scale) - k * (zs / 4), zy + 1 * scale + k * (zs / 4 - 0.5), 1 * scale, 1 * scale);
      }
      ctx.restore();
    }
  } else {
    // Standing / sitting cat
    const bob = c.state === 'wander' ? Math.sin(c.walkPhase) * 1 * scale : 0;
    const cx = sx, cy = sy + bob;
    const flip = c.facingRight ? 1 : -1;

    // Body
    ctx.fillStyle = orange;
    const bw = 14 * scale, bh = 10 * scale;
    ctx.fillRect(cx - bw/2, cy - 2 * scale, bw, bh);
    // Head
    const hw = 10 * scale, hh = 9 * scale;
    ctx.fillRect(cx - hw/2 + flip * 3 * scale, cy - 10 * scale, hw, hh);
    // Ears (triangular)
    ctx.fillRect(cx - 4 * scale + flip * 3 * scale, cy - 13 * scale, 3 * scale, 3 * scale);
    ctx.fillRect(cx + 1 * scale + flip * 3 * scale, cy - 13 * scale, 3 * scale, 3 * scale);
    ctx.fillRect(cx - 3 * scale + flip * 3 * scale, cy - 14 * scale, 1 * scale, 1 * scale);
    ctx.fillRect(cx + 3 * scale + flip * 3 * scale, cy - 14 * scale, 1 * scale, 1 * scale);
    // Inner ears (pink)
    ctx.fillStyle = '#d98ca0';
    ctx.fillRect(cx - 3 * scale + flip * 3 * scale, cy - 12 * scale, 1 * scale, 1 * scale);
    ctx.fillRect(cx + 2 * scale + flip * 3 * scale, cy - 12 * scale, 1 * scale, 1 * scale);
    // Legs
    ctx.fillStyle = orange;
    if (c.state === 'wander') {
      const legOff = Math.sin(c.walkPhase) * 1 * scale;
      ctx.fillRect(cx - 5 * scale, cy + 8 * scale, 3 * scale, 3 * scale + legOff);
      ctx.fillRect(cx + 2 * scale, cy + 8 * scale, 3 * scale, 3 * scale - legOff);
    } else {
      // sitting
      ctx.fillRect(cx - 5 * scale, cy + 7 * scale, 3 * scale, 4 * scale);
      ctx.fillRect(cx + 2 * scale, cy + 7 * scale, 3 * scale, 4 * scale);
    }
    // Stripes
    ctx.fillStyle = orangeDark;
    ctx.fillRect(cx - 5 * scale, cy - 1 * scale, 1 * scale, 4 * scale);
    ctx.fillRect(cx - 1 * scale, cy - 2 * scale, 1 * scale, 6 * scale);
    ctx.fillRect(cx + 3 * scale, cy - 1 * scale, 1 * scale, 5 * scale);
    // Chest cream
    ctx.fillStyle = cream;
    ctx.fillRect(cx - 2 * scale, cy + 2 * scale, 4 * scale, 4 * scale);
    ctx.fillRect(cx - 1 * scale + flip * 3 * scale, cy - 5 * scale, 2 * scale, 3 * scale);
    // Eyes
    ctx.fillStyle = '#2a1810';
    const isBlink = Math.floor(performance.now() / 2800) % 10 === 0;
    if (!isBlink) {
      ctx.fillRect(cx - 2 * scale + flip * 3 * scale, cy - 7 * scale, 1 * scale, 2 * scale);
      ctx.fillRect(cx + 1 * scale + flip * 3 * scale, cy - 7 * scale, 1 * scale, 2 * scale);
      ctx.fillStyle = '#5c9a4a';
      ctx.fillRect(cx - 2 * scale + flip * 3 * scale, cy - 7 * scale, 1 * scale, 1 * scale);
      ctx.fillRect(cx + 1 * scale + flip * 3 * scale, cy - 7 * scale, 1 * scale, 1 * scale);
    } else {
      ctx.fillRect(cx - 2 * scale + flip * 3 * scale, cy - 6 * scale, 1 * scale, 1 * scale);
      ctx.fillRect(cx + 1 * scale + flip * 3 * scale, cy - 6 * scale, 1 * scale, 1 * scale);
    }
    // Nose + mouth
    ctx.fillStyle = '#d98ca0';
    ctx.fillRect(cx + flip * 3 * scale, cy - 4 * scale, 1 * scale, 1 * scale);
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(cx - 1 * scale + flip * 3 * scale, cy - 3 * scale, 1 * scale, 1 * scale);
    ctx.fillRect(cx + 1 * scale + flip * 3 * scale, cy - 3 * scale, 1 * scale, 1 * scale);
    // Whiskers
    ctx.fillStyle = 'rgba(42,24,16,0.55)';
    ctx.fillRect(cx - 6 * scale + flip * 3 * scale, cy - 4 * scale, 2 * scale, 1);
    ctx.fillRect(cx + 4 * scale + flip * 3 * scale, cy - 4 * scale, 2 * scale, 1);
    // Tail (curly)
    ctx.fillStyle = orange;
    const tailX = cx - flip * bw/2;
    ctx.fillRect(tailX - flip * 2 * scale, cy - 4 * scale, 2 * scale, 2 * scale);
    ctx.fillRect(tailX - flip * 4 * scale, cy - 6 * scale, 2 * scale, 2 * scale);
    ctx.fillRect(tailX - flip * 5 * scale, cy - 9 * scale, 2 * scale, 3 * scale);
    // Outline
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(cx - bw/2 - 1, cy - 2 * scale, 1, bh);
    ctx.fillRect(cx + bw/2, cy - 2 * scale, 1, bh);
    ctx.fillRect(cx - bw/2, cy - 3 * scale, bw, 1);
    ctx.fillRect(cx - bw/2, cy + bh - 2 * scale, bw, 1);
  }
}

/* ═══ Agent sprite (chibi circle + hat) ═══ */
function drawSkinBackLayer(skin, sx, bodyY, headY, r) {
  ctx.fillStyle = skin.hairShadow;
  if (skin.silhouette === 'elf_mage') {
    ctx.fillRect(sx - 13 * scale, headY + 3 * scale, 26 * scale, 34 * scale);
    ctx.fillRect(sx - 16 * scale, headY + 14 * scale, 5 * scale, 25 * scale);
    ctx.fillRect(sx + 11 * scale, headY + 14 * scale, 5 * scale, 25 * scale);
    ctx.fillRect(sx - 20 * scale, bodyY - 5 * scale, 6 * scale, 3 * scale);
    ctx.fillRect(sx + 14 * scale, bodyY - 5 * scale, 6 * scale, 3 * scale);
    ctx.fillStyle = '#f1d8ba';
    ctx.fillRect(sx - 22 * scale, bodyY - 4 * scale, 5 * scale, 3 * scale);
    ctx.fillRect(sx + 17 * scale, bodyY - 4 * scale, 5 * scale, 3 * scale);
  } else if (skin.silhouette === 'blue_actor') {
    ctx.fillRect(sx - 16 * scale, headY + 2 * scale, 32 * scale, 30 * scale);
    ctx.fillRect(sx - 18 * scale, headY + 12 * scale, 6 * scale, 22 * scale);
    ctx.fillRect(sx + 12 * scale, headY + 10 * scale, 6 * scale, 24 * scale);
  } else if (skin.silhouette === 'cute_girl') {
    ctx.fillRect(sx - 24 * scale, headY + 2 * scale, 11 * scale, 11 * scale);
    ctx.fillRect(sx + 13 * scale, headY + 2 * scale, 11 * scale, 11 * scale);
    ctx.fillRect(sx - 14 * scale, headY + 5 * scale, 28 * scale, 28 * scale);
  } else {
    ctx.fillRect(sx - r, headY + 2 * scale, r * 2, 26 * scale);
  }
}

function drawSkinBangs(skin, sx, bodyY, headY) {
  ctx.fillStyle = skin.hair;
  if (skin.silhouette === 'elf_mage') {
    ctx.fillRect(sx - 13 * scale, headY + 1 * scale, 26 * scale, 8 * scale);
    ctx.fillRect(sx - 10 * scale, headY + 8 * scale, 5 * scale, 10 * scale);
    ctx.fillRect(sx - 3 * scale, headY + 7 * scale, 6 * scale, 9 * scale);
    ctx.fillRect(sx + 5 * scale, headY + 8 * scale, 5 * scale, 10 * scale);
    ctx.fillStyle = skin.hairShadow;
    ctx.fillRect(sx - 15 * scale, bodyY + 5 * scale, 4 * scale, 22 * scale);
    ctx.fillRect(sx + 11 * scale, bodyY + 5 * scale, 4 * scale, 22 * scale);
  } else if (skin.silhouette === 'blue_actor') {
    ctx.fillRect(sx - 15 * scale, headY + 2 * scale, 30 * scale, 9 * scale);
    ctx.fillRect(sx - 12 * scale, headY + 9 * scale, 7 * scale, 12 * scale);
    ctx.fillRect(sx - 4 * scale, headY + 8 * scale, 7 * scale, 9 * scale);
    ctx.fillRect(sx + 4 * scale, headY + 9 * scale, 8 * scale, 12 * scale);
    ctx.fillStyle = skin.accent;
    ctx.fillRect(sx + 10 * scale, headY + 5 * scale, 7 * scale, 2 * scale);
  } else if (skin.silhouette === 'cute_girl') {
    ctx.fillRect(sx - 11 * scale, headY + 2 * scale, 22 * scale, 8 * scale);
    ctx.fillRect(sx - 9 * scale, headY + 9 * scale, 6 * scale, 9 * scale);
    ctx.fillRect(sx + 3 * scale, headY + 9 * scale, 6 * scale, 9 * scale);
    ctx.fillStyle = skin.accessory;
    ctx.fillRect(sx - 4 * scale, headY - 3 * scale, 8 * scale, 4 * scale);
    ctx.fillRect(sx - 7 * scale, headY - 1 * scale, 3 * scale, 3 * scale);
    ctx.fillRect(sx + 4 * scale, headY - 1 * scale, 3 * scale, 3 * scale);
  }
}

function drawSkinAccessory(skin, sx, bodyY, headY) {
  if (skin.silhouette === 'elf_mage') {
    ctx.fillStyle = skin.accent;
    ctx.fillRect(sx - 8 * scale, headY + 1 * scale, 16 * scale, 2 * scale);
    ctx.fillStyle = skin.accessory;
    ctx.fillRect(sx + 18 * scale, bodyY - 20 * scale, 2 * scale, 42 * scale);
    ctx.fillStyle = skin.accent;
    ctx.fillRect(sx + 16 * scale, bodyY - 23 * scale, 6 * scale, 6 * scale);
    ctx.fillStyle = '#fbf3dd';
    ctx.fillRect(sx + 18 * scale, bodyY - 21 * scale, 2 * scale, 2 * scale);
  } else if (skin.silhouette === 'blue_actor') {
    ctx.fillStyle = skin.accessory;
    ctx.fillRect(sx - 10 * scale, headY + 3 * scale, 5 * scale, 2 * scale);
    ctx.fillStyle = skin.accent;
    ctx.fillRect(sx - 12 * scale, headY + 1 * scale, 3 * scale, 6 * scale);
    ctx.fillRect(sx + 2 * scale, bodyY + 6 * scale, 7 * scale, 2 * scale);
  } else if (skin.silhouette === 'cute_girl') {
    ctx.fillStyle = skin.accent;
    ctx.fillRect(sx - 8 * scale, bodyY + 2 * scale, 16 * scale, 3 * scale);
    ctx.fillRect(sx - 5 * scale, bodyY + 6 * scale, 10 * scale, 3 * scale);
    ctx.fillStyle = skin.accessory;
    ctx.fillRect(sx - 18 * scale, headY + 6 * scale, 6 * scale, 3 * scale);
    ctx.fillRect(sx + 12 * scale, headY + 6 * scale, 6 * scale, 3 * scale);
  }
}

function drawApprovalMarker(a, sx, headY) {
  if (!approvalWaitingForAgent(a)) return;
  const blink = Math.floor(performance.now() / 320) % 2 === 0;
  const markerX = sx + 18 * scale;
  const markerY = headY - 25 * scale + (blink ? -2 * scale : 0);
  ctx.save();
  ctx.fillStyle = blink ? '#d2553a' : '#e0a93b';
  ctx.fillRect(markerX - 7 * scale, markerY - 9 * scale, 14 * scale, 16 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(markerX - 8 * scale, markerY - 10 * scale, 16 * scale, 1);
  ctx.fillRect(markerX - 8 * scale, markerY + 7 * scale, 16 * scale, 1);
  ctx.fillRect(markerX - 8 * scale, markerY - 10 * scale, 1, 18 * scale);
  ctx.fillRect(markerX + 7 * scale, markerY - 10 * scale, 1, 18 * scale);
  ctx.font = `${13 * scale}px 'DungGeunMo','Galmuri11','NeoDunggeunmo',monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillStyle = '#fbf3dd';
  ctx.fillText('!', markerX, markerY);
  ctx.restore();
}

function drawAgent(a) {
  const skin = characterSkinForAgent(a.name);
  const sx = a.x * scale, sy = a.y * scale;
  const bob = Math.sin(a.bobPhase) * (a.state === 'working' ? 1.5 : 2.5) * scale;
  const r = 12 * scale;
  const bodyY = sy + bob;
  const headY = bodyY - r;

  drawSkinBackLayer(skin, sx, bodyY, headY, r);

  // Shadow (soft ellipse)
  ctx.fillStyle = 'rgba(58, 42, 26, 0.35)';
  ctx.beginPath();
  ctx.ellipse(sx, sy + 10 * scale, r * 0.85, r * 0.25, 0, 0, Math.PI * 2);
  ctx.fill();

  // Body (chunky pixel blob)
  ctx.fillStyle = skin.outfit;
  // square-ish body for pixel vibe
  const bw = r * 1.9, bh = r * 1.9;
  ctx.fillRect(sx - bw/2, bodyY - bh/2, bw, bh);
  // Dark outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(sx - bw/2 - 1, bodyY - bh/2, bw + 2, 1);
  ctx.fillRect(sx - bw/2 - 1, bodyY + bh/2, bw + 2, 1);
  ctx.fillRect(sx - bw/2 - 1, bodyY - bh/2, 1, bh);
  ctx.fillRect(sx + bw/2, bodyY - bh/2, 1, bh);
  // Highlight
  ctx.fillStyle = 'rgba(255,255,255,0.35)';
  ctx.fillRect(sx - bw/2 + 2, bodyY - bh/2 + 2, bw - 4, 1);
  ctx.fillRect(sx - bw/2 + 2, bodyY - bh/2 + 2, 1, bh - 4);
  // Shadow side
  ctx.fillStyle = 'rgba(0,0,0,0.2)';
  ctx.fillRect(sx - bw/2 + 2, bodyY + bh/2 - 3, bw - 4, 1);
  ctx.fillStyle = skin.outfitShadow;
  ctx.fillRect(sx - 8 * scale, bodyY + 7 * scale, 16 * scale, 3 * scale);
  ctx.fillStyle = skin.accent;
  ctx.fillRect(sx - 3 * scale, bodyY - 8 * scale, 6 * scale, 3 * scale);

  // Eyes (pixel dots)
  const eyeOx = 4 * scale, eyeY = bodyY - 1 * scale;
  if (!a.isBlinking) {
    // white
    ctx.fillStyle = '#fbf3dd';
    ctx.fillRect(sx - eyeOx - 2 * scale, eyeY - 1 * scale, 3 * scale, 3 * scale);
    ctx.fillRect(sx + eyeOx - 1 * scale, eyeY - 1 * scale, 3 * scale, 3 * scale);
    // pupil
    const lookX = a.facingRight ? 0 : -1;
    ctx.fillStyle = skin.eye;
    ctx.fillRect(sx - eyeOx + lookX * scale, eyeY, 1 * scale, 2 * scale);
    ctx.fillRect(sx + eyeOx + lookX * scale, eyeY, 1 * scale, 2 * scale);
    if (skin.silhouette === 'blue_actor') {
      ctx.fillStyle = '#fbf3dd';
      ctx.fillRect(sx + eyeOx + lookX * scale, eyeY - 1 * scale, 1 * scale, 1 * scale);
    }
  } else {
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(sx - eyeOx - 2 * scale, eyeY + 1 * scale, 3 * scale, 1);
    ctx.fillRect(sx + eyeOx - 1 * scale, eyeY + 1 * scale, 3 * scale, 1);
  }

  // Mouth (state-dependent)
  if (a.state === 'working') {
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(sx - 2 * scale, bodyY + 4 * scale, 4 * scale, 1 * scale);
  } else if (a.state === 'broken' || a.state === 'dead') {
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(sx - 2 * scale, bodyY + 5 * scale, 1 * scale, 1);
    ctx.fillRect(sx - 1 * scale, bodyY + 4 * scale, 1 * scale, 1);
    ctx.fillRect(sx + 1 * scale, bodyY + 4 * scale, 1 * scale, 1);
    ctx.fillRect(sx + 2 * scale, bodyY + 5 * scale, 1 * scale, 1);
  } else {
    // smile
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(sx - 2 * scale, bodyY + 4 * scale, 1, 1);
    ctx.fillRect(sx - 1 * scale, bodyY + 5 * scale, 3 * scale, 1);
    ctx.fillRect(sx + 2 * scale, bodyY + 4 * scale, 1, 1);
  }

  drawSkinBangs(skin, sx, bodyY, headY);

  if (animationStateForAgent(a) === 'rest') {
    ctx.font = `${9 * scale}px 'DungGeunMo','Galmuri11','NeoDunggeunmo',monospace`;
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#5a3d28';
    ctx.fillText('Z', sx + 12 * scale, headY - 2 * scale);
    ctx.fillText('z', sx + 18 * scale, headY - 8 * scale);
  }

  drawSkinAccessory(skin, sx, bodyY, headY);

  // Name plate
  const nameY = headY - 10 * scale;
  ctx.font = `${10 * scale}px 'DungGeunMo','Galmuri11','NeoDunggeunmo',monospace`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'bottom';
  const nameW = ctx.measureText(a.name).width + 12 * scale;
  // plate
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(sx - nameW/2, nameY - 14 * scale, nameW, 14 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(sx - nameW/2 - 1, nameY - 15 * scale, nameW + 2, 1);
  ctx.fillRect(sx - nameW/2 - 1, nameY, nameW + 2, 1);
  ctx.fillRect(sx - nameW/2 - 1, nameY - 15 * scale, 1, 15 * scale);
  ctx.fillRect(sx + nameW/2, nameY - 15 * scale, 1, 15 * scale);
  ctx.fillStyle = '#3a2a1a';
  ctx.fillText(a.name, sx, nameY - 2 * scale);
  drawApprovalMarker(a, sx, headY);

  // State pill — pastel, pixel-bordered
  const stateText = animationStateForAgent(a).toUpperCase();
  ctx.font = `${9 * scale}px 'DungGeunMo','Galmuri11','NeoDunggeunmo',monospace`;
  const pw = ctx.measureText(stateText).width + 14 * scale;
  const ph = 16 * scale;
  const px = sx - pw/2, py = sy + 16 * scale;
  // background pastel
  ctx.fillStyle = a.color;
  ctx.fillRect(px, py, pw, ph);
  // dark outline
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(px - 1, py - 1, pw + 2, 1);
  ctx.fillRect(px - 1, py + ph, pw + 2, 1);
  ctx.fillRect(px - 1, py - 1, 1, ph + 2);
  ctx.fillRect(px + pw, py - 1, 1, ph + 2);
  // highlight
  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.fillRect(px, py, pw, 1);
  // shadow
  ctx.fillStyle = 'rgba(0,0,0,0.25)';
  ctx.fillRect(px, py + ph - 1, pw, 1);
  // text
  ctx.fillStyle = '#fbf3dd';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(stateText, sx, py + ph/2 + 1);

  // Token pulse from the live monitor stream.
  if (a.tokenPulse > 0) {
    const pulse = Math.min(1, a.tokenPulse);
    const ring = (22 + (1 - pulse) * 14) * scale;
    ctx.strokeStyle = `rgba(224, 169, 59, ${0.28 + pulse * 0.42})`;
    ctx.lineWidth = Math.max(1, 2 * scale);
    ctx.beginPath();
    ctx.arc(sx, bodyY, ring, 0, Math.PI * 2);
    ctx.stroke();
    const tokenText = formatCompactNumber(a.tokenTotal || 0);
    ctx.font = `${8 * scale}px 'DungGeunMo','Galmuri11','NeoDunggeunmo',monospace`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    ctx.fillStyle = `rgba(42, 24, 16, ${0.65 + pulse * 0.3})`;
    ctx.fillText(tokenText, sx, py + ph + 12 * scale);
  }

  // JRPG speech bubble (if timer > 0 & text present)
  if (a.bubble.text && a.bubble.timer > 0) {
    drawJRPGBubble(sx, headY - 22 * scale, a.bubble.text);
  }
}

function drawJRPGBubble(cx, cy, text) {
  ctx.save();
  ctx.font = `${10 * scale}px 'DungGeunMo','Galmuri11','NeoDunggeunmo',monospace`;
  const padX = 10 * scale, padY = 7 * scale;
  const textW = ctx.measureText(text).width;
  const boxW = textW + padX * 2;
  const boxH = 14 * scale + padY * 2;
  const bx = cx - boxW / 2;
  const by = cy - boxH;

  // Shadow
  ctx.fillStyle = 'rgba(58, 42, 26, 0.35)';
  ctx.fillRect(bx + 3, by + 3, boxW, boxH);

  // Box body (parchment cream)
  ctx.fillStyle = '#fbf3dd';
  ctx.fillRect(bx, by, boxW, boxH);

  // Chunky pixel border (4-layer)
  // Outer dark
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(bx - 2, by, boxW + 4, 2);
  ctx.fillRect(bx - 2, by + boxH - 2, boxW + 4, 2);
  ctx.fillRect(bx - 2, by, 2, boxH);
  ctx.fillRect(bx + boxW, by, 2, boxH);
  ctx.fillRect(bx, by - 2, boxW, 2);
  ctx.fillRect(bx, by + boxH, boxW, 2);
  // Inner bright bevel (top-left)
  ctx.fillStyle = '#fff8e0';
  ctx.fillRect(bx + 2, by + 2, boxW - 4, 1);
  ctx.fillRect(bx + 2, by + 2, 1, boxH - 4);
  // Inner dim bevel (bottom-right)
  ctx.fillStyle = '#d9b986';
  ctx.fillRect(bx + 2, by + boxH - 3, boxW - 4, 1);
  ctx.fillRect(bx + boxW - 3, by + 2, 1, boxH - 4);

  // Corner notches (JRPG-style)
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(bx - 2, by - 2, 1, 1);
  ctx.fillRect(bx + boxW + 1, by - 2, 1, 1);
  ctx.fillRect(bx - 2, by + boxH + 1, 1, 1);
  ctx.fillRect(bx + boxW + 1, by + boxH + 1, 1, 1);

  // Tail (pixel triangle pointing down)
  const tailX = cx;
  const tailY = by + boxH;
  ctx.fillStyle = '#fbf3dd';
  for (let i = 0; i < 4; i++) {
    ctx.fillRect(tailX - (4 - i) * scale, tailY + i * scale, (8 - i * 2) * scale, 1 * scale);
  }
  // Tail outline
  ctx.fillStyle = '#2a1810';
  for (let i = 0; i < 4; i++) {
    ctx.fillRect(tailX - (4 - i) * scale - 1, tailY + i * scale, 1, 1 * scale);
    ctx.fillRect(tailX + (4 - i) * scale, tailY + i * scale, 1, 1 * scale);
  }
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(tailX - 1 * scale, tailY + 4 * scale, 2 * scale, 1 * scale);

  // Text
  ctx.fillStyle = '#3a2a1a';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, cx, by + boxH / 2 + 1);

  // Blinking ▼ arrow (JRPG continue indicator)
  const arrowBlink = Math.floor(performance.now() / 400) % 2 === 0;
  if (arrowBlink) {
    ctx.fillStyle = '#d2553a';
    ctx.fillRect(bx + boxW - 10 * scale, by + boxH - 8 * scale, 5 * scale, 1 * scale);
    ctx.fillRect(bx + boxW - 9 * scale, by + boxH - 7 * scale, 3 * scale, 1 * scale);
    ctx.fillRect(bx + boxW - 8 * scale, by + boxH - 6 * scale, 1 * scale, 1 * scale);
  }

  ctx.restore();
}

/* ═══ Little pixel hearts drifting up from working agents ═══ */
const particles = [];
function spawnHeart(x, y) {
  particles.push({
    x, y, vy: -20 - Math.random() * 10,
    vx: (Math.random() - 0.5) * 6,
    life: 1.6, maxLife: 1.6,
    color: ['#d98ca0', '#e0a93b', '#a88cc5'][Math.floor(Math.random() * 3)],
    shape: Math.random() < 0.5 ? 'heart' : 'note',
  });
}
function spawnRedHeart(x, y) {
  particles.push({
    x, y,
    vy: -26 - Math.random() * 10,
    vx: (Math.random() - 0.5) * 10,
    life: 1.4, maxLife: 1.4,
    color: '#e83a4a',
    shape: 'heart',
  });
}
function updateParticles(dt) {
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.x += p.vx * dt; p.y += p.vy * dt;
    p.life -= dt;
    if (p.life <= 0) particles.splice(i, 1);
  }
}
function drawParticles() {
  for (const p of particles) {
    const alpha = p.life / p.maxLife;
    ctx.save();
    ctx.globalAlpha = alpha;
    const sx = p.x * scale, sy = p.y * scale;
    if (p.shape === 'heart') {
      // 4x3 pixel heart
      ctx.fillStyle = p.color;
      ctx.fillRect(sx - 2 * scale, sy - 1 * scale, 2 * scale, 1 * scale);
      ctx.fillRect(sx + 1 * scale, sy - 1 * scale, 2 * scale, 1 * scale);
      ctx.fillRect(sx - 2 * scale, sy, 5 * scale, 1 * scale);
      ctx.fillRect(sx - 1 * scale, sy + 1 * scale, 3 * scale, 1 * scale);
      ctx.fillRect(sx, sy + 2 * scale, 1 * scale, 1 * scale);
    } else {
      // music note
      ctx.fillStyle = p.color;
      ctx.fillRect(sx, sy - 4 * scale, 1 * scale, 5 * scale);
      ctx.fillRect(sx - 2 * scale, sy, 3 * scale, 2 * scale);
      ctx.fillRect(sx, sy - 5 * scale, 3 * scale, 1 * scale);
    }
    ctx.restore();
  }
}

/* ═══ Pneumatic tube / courier packets / owls ═══ */
const TUBE = {
  x: 988,
  yTop: 50,
  yBot: 500,
  radius: 14,
};

const packets = [];
const owls = [];
const communicationTransfers = [];

function queueScenePacket(fromZone, toZone, color = '#fbf3dd') {
  if (lowMotion) return;
  sendPacket(fromZone, toZone, color);
}

function queueSceneOwl(toZone, pickup = true) {
  if (lowMotion) return;
  sendOwl(toZone, pickup);
}

function communicationLabel(event) {
  return String(event?.message || event?.event_type || 'handoff').slice(0, 80);
}

function queueCommunicationTransfer(fromName, toName, label = 'handoff', color = '#6aa7c9') {
  const from = getAgent(fromName);
  const to = getAgent(toName);
  if (!from || !to) return;
  pushEvent('info', `${fromName} → ${toName}: ${label}`);
  if (lowMotion) return;
  communicationTransfers.push({
    fromName,
    toName,
    label,
    color,
    t: 0,
    duration: 4.0,
  });
  if (communicationTransfers.length > 24) communicationTransfers.shift();
}

function updateCommunicationTransfers(dt) {
  for (let i = communicationTransfers.length - 1; i >= 0; i--) {
    const transfer = communicationTransfers[i];
    transfer.t += dt;
    if (transfer.t >= transfer.duration) communicationTransfers.splice(i, 1);
  }
}

function drawCommunicationTransfers() {
  for (const transfer of communicationTransfers) {
    const from = getAgent(transfer.fromName);
    const to = getAgent(transfer.toName);
    if (!from || !to) continue;
    const minX = Math.min(from.x, to.x);
    const minY = Math.min(from.y, to.y) - 38;
    const maxX = Math.max(from.x, to.x);
    const maxY = Math.max(from.y, to.y);
    if (!isWorldRectVisible(minX, minY, maxX - minX, maxY - minY + 40, 60)) continue;
    const progress = Math.min(1, transfer.t / transfer.duration);
    const sx = from.x * scale;
    const sy = (from.y - 26) * scale;
    const ex = to.x * scale;
    const ey = (to.y - 26) * scale;
    const dotX = sx + (ex - sx) * progress;
    const dotY = sy + (ey - sy) * progress - Math.sin(progress * Math.PI) * 16 * scale;
    ctx.save();
    ctx.strokeStyle = transfer.color || '#6aa7c9';
    ctx.lineWidth = Math.max(1, 2 * scale);
    ctx.globalAlpha = 0.76;
    ctx.setLineDash([7 * scale, 6 * scale]);
    ctx.lineDashOffset = -transfer.t * 34 * scale;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(ex, ey);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
    ctx.fillStyle = '#fbf3dd';
    ctx.fillRect(dotX - 4 * scale, dotY - 4 * scale, 8 * scale, 8 * scale);
    ctx.fillStyle = transfer.color || '#6aa7c9';
    ctx.fillRect(dotX - 2 * scale, dotY - 2 * scale, 4 * scale, 4 * scale);
    ctx.restore();
  }
}

function drawPneumaticTube() {
  const time = performance.now() / 1000;
  const cx = TUBE.x * scale;
  const radius = TUBE.radius * scale;
  const yTop = TUBE.yTop * scale;
  const yBottom = TUBE.yBot * scale;

  [yTop, (yTop + yBottom) / 2, yBottom].forEach((bracketY) => {
    ctx.fillStyle = '#5a3d22';
    ctx.fillRect(cx - radius - 6 * scale, bracketY - 3 * scale, 2 * scale, 6 * scale);
    ctx.fillRect(cx + radius + 4 * scale, bracketY - 3 * scale, 2 * scale, 6 * scale);
    ctx.fillStyle = '#3a2a1a';
    ctx.fillRect(cx - radius - 6 * scale, bracketY - 4 * scale, radius * 2 + 12 * scale, 1);
    ctx.fillRect(cx - radius - 6 * scale, bracketY + 3 * scale, radius * 2 + 12 * scale, 1);
  });

  ctx.fillStyle = '#8a5f35';
  ctx.fillRect(cx - radius - 4 * scale, yTop - 10 * scale, radius * 2 + 8 * scale, 6 * scale);
  ctx.fillRect(cx - radius - 4 * scale, yBottom + 4 * scale, radius * 2 + 8 * scale, 6 * scale);
  ctx.fillStyle = '#3a2a1a';
  ctx.fillRect(cx - radius - 5 * scale, yTop - 11 * scale, radius * 2 + 10 * scale, 1);
  ctx.fillRect(cx - radius - 5 * scale, yTop - 4 * scale, radius * 2 + 10 * scale, 1);
  ctx.fillRect(cx - radius - 5 * scale, yBottom + 3 * scale, radius * 2 + 10 * scale, 1);
  ctx.fillRect(cx - radius - 5 * scale, yBottom + 10 * scale, radius * 2 + 10 * scale, 1);
  ctx.fillStyle = '#1a0f08';
  ctx.fillRect(cx - radius + 1, yTop - 10 * scale, radius * 2 - 2, 4 * scale);
  ctx.fillRect(cx - radius + 1, yBottom + 6 * scale, radius * 2 - 2, 4 * scale);

  ctx.fillStyle = 'rgba(180, 220, 235, 0.22)';
  ctx.fillRect(cx - radius, yTop, radius * 2, yBottom - yTop);
  ctx.fillStyle = 'rgba(255, 255, 255, 0.35)';
  ctx.fillRect(cx - radius + 2, yTop + 4, 1 * scale, yBottom - yTop - 8);
  ctx.fillStyle = 'rgba(255, 255, 255, 0.18)';
  ctx.fillRect(cx - radius + 4 * scale, yTop + 4, 1, yBottom - yTop - 8);
  ctx.fillStyle = 'rgba(40, 60, 80, 0.18)';
  ctx.fillRect(cx + radius - 3 * scale, yTop + 4, 1 * scale, yBottom - yTop - 8);

  const ringSpacing = 60 * scale;
  for (let ringY = yTop + ringSpacing; ringY < yBottom - 4; ringY += ringSpacing) {
    ctx.fillStyle = '#b08a5f';
    ctx.fillRect(cx - radius - 2 * scale, ringY, radius * 2 + 4 * scale, 4 * scale);
    ctx.fillStyle = '#e0c080';
    ctx.fillRect(cx - radius - 2 * scale, ringY, radius * 2 + 4 * scale, 1);
    ctx.fillStyle = '#5a3d22';
    ctx.fillRect(cx - radius - 2 * scale, ringY + 3 * scale, radius * 2 + 4 * scale, 1);
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(cx - radius - 3 * scale, ringY - 1, radius * 2 + 6 * scale, 1);
    ctx.fillRect(cx - radius - 3 * scale, ringY + 4 * scale, radius * 2 + 6 * scale, 1);
  }

  ctx.fillStyle = '#2a1810';
  ctx.fillRect(cx - radius - 1, yTop, 1, yBottom - yTop);
  ctx.fillRect(cx + radius, yTop, 1, yBottom - yTop);

  if (!lowMotion) {
    for (let i = 0; i < 5; i++) {
      const phase = (time * 0.3 + i * 0.19) % 1;
      const py = yTop + phase * (yBottom - yTop);
      const px = cx + Math.sin(time * 2 + i) * (radius - 4) * 0.3;
      ctx.fillStyle = `rgba(180, 220, 240, ${0.35 * (1 - Math.abs(phase - 0.5) * 1.4)})`;
      ctx.fillRect(px - 1, py, 2, 1);
    }
  }
}

function sendPacket(fromZone, toZone, color = '#fbf3dd') {
  const from = ZONE_MAP[fromZone];
  const to = ZONE_MAP[toZone];
  if (!from || !to) return;
  packets.push({
    phase: 'approach_up',
    t: 0,
    sx: from.x + from.w * 0.5,
    sy: from.y + from.h * 0.55,
    ex: TUBE.x,
    ey: TUBE.yTop - 4,
    ox: TUBE.x,
    oy: TUBE.yBot + 4,
    dx: to.x + to.w * 0.5,
    dy: to.y + to.h * 0.4,
    color,
    d1: 0.9,
    d2: 0.65,
    d3: 0.85,
  });
}

function updatePackets(dt) {
  for (let i = packets.length - 1; i >= 0; i--) {
    const packet = packets[i];
    packet.t += dt;
    if (packet.phase === 'approach_up' && packet.t >= packet.d1) {
      packet.phase = 'in_tube';
      packet.t = 0;
    } else if (packet.phase === 'in_tube' && packet.t >= packet.d2) {
      packet.phase = 'approach_out';
      packet.t = 0;
    } else if (packet.phase === 'approach_out' && packet.t >= packet.d3) {
      packets.splice(i, 1);
    }
  }
}

function drawPackets() {
  for (const packet of packets) {
    let x;
    let y;
    let tilt = 0;
    let squish = 1;
    if (packet.phase === 'approach_up') {
      const u = packet.t / packet.d1;
      const ease = 1 - (1 - u) * (1 - u);
      x = packet.sx + (packet.ex - packet.sx) * ease;
      y = packet.sy + (packet.ey - packet.sy) * ease - Math.sin(u * Math.PI) * 40;
      tilt = Math.sin(u * Math.PI * 2) * 0.35 + (packet.ex - packet.sx) * 0.003;
    } else if (packet.phase === 'in_tube') {
      const u = packet.t / packet.d2;
      const ease = u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
      x = packet.ex;
      y = packet.ey + (packet.oy - packet.ey) * ease;
      squish = 0.72;
    } else {
      const u = packet.t / packet.d3;
      const ease = 1 - (1 - u) * (1 - u);
      x = packet.ox + (packet.dx - packet.ox) * ease;
      y = packet.oy + (packet.dy - packet.oy) * ease - Math.sin(u * Math.PI) * 18;
      tilt = Math.sin(u * Math.PI * 1.5) * -0.3;
    }
    if (!isWorldRectVisible(x - 18, y - 18, 36, 36, 40)) continue;
    drawEnvelope(x * scale, y * scale, packet.color, tilt, squish, packet.phase === 'in_tube');
  }
}

function drawEnvelope(cx, cy, color, tilt, squish, inTube) {
  const width = 14 * scale;
  const height = 10 * scale * squish;
  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(tilt);
  if (inTube) {
    ctx.fillStyle = 'rgba(255, 240, 200, 0.25)';
    ctx.fillRect(-width / 2, -height / 2 - 14 * scale, width, 3 * scale);
    ctx.fillStyle = 'rgba(255, 240, 200, 0.45)';
    ctx.fillRect(-width / 2, -height / 2 - 8 * scale, width, 3 * scale);
  }
  ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
  ctx.fillRect(-width / 2 + 1, -height / 2 + 1, width, height);
  ctx.fillStyle = color;
  ctx.fillRect(-width / 2, -height / 2, width, height);
  ctx.fillStyle = '#e8d5a8';
  ctx.fillRect(-width / 2 + 1, -height / 2, width - 2, 1 * scale);
  ctx.fillRect(-width / 2 + 2, -height / 2 + 1, width - 4, 1 * scale);
  ctx.fillRect(-width / 2 + 3, -height / 2 + 2, width - 6, 1 * scale);
  ctx.fillRect(-width / 2 + 5, -height / 2 + 3, width - 10, 1 * scale);
  ctx.fillStyle = '#d2553a';
  ctx.fillRect(-1 * scale, 1 * scale, 3 * scale, 3 * scale);
  ctx.fillStyle = '#a8402a';
  ctx.fillRect(1 * scale, 3 * scale, 1 * scale, 1 * scale);
  ctx.fillStyle = '#2a1810';
  ctx.fillRect(-width / 2 - 1, -height / 2, 1, height);
  ctx.fillRect(width / 2, -height / 2, 1, height);
  ctx.fillRect(-width / 2, -height / 2 - 1, width, 1);
  ctx.fillRect(-width / 2, height / 2, width, 1);
  ctx.restore();
}

function sendOwl(toZone, pickup = true) {
  const zone = ZONE_MAP[toZone];
  if (!zone) return;
  const target = { x: zone.x + zone.w * 0.5, y: zone.y + zone.h * 0.4 };
  const fromRight = Math.random() < 0.5;
  owls.push({
    phase: 'fly_in',
    t: 0,
    x: fromRight ? VIRTUAL_W + 40 : -40,
    y: target.y - 60 - Math.random() * 20,
    dir: fromRight ? -1 : 1,
    target,
    hasLetter: pickup,
    exitX: fromRight ? -40 : VIRTUAL_W + 40,
    exitY: target.y - 80 - Math.random() * 30,
    d1: 1.9,
    d2: 0.9,
    d3: 1.6,
  });
}

function updateOwls(dt) {
  for (let i = owls.length - 1; i >= 0; i--) {
    const owl = owls[i];
    owl.t += dt;
    if (owl.phase === 'fly_in') {
      const u = Math.min(1, owl.t / owl.d1);
      const ease = 1 - (1 - u) * (1 - u);
      owl.x = (owl.phaseStartX ?? (owl.phaseStartX = owl.x)) + ((owl.target.x - 10 * owl.dir) - owl.phaseStartX) * ease;
      owl.y = (owl.phaseStartY ?? (owl.phaseStartY = owl.y)) + ((owl.target.y - 28) - owl.phaseStartY) * ease + Math.sin(u * Math.PI) * -8;
      if (u >= 1) {
        owl.phase = 'drop';
        owl.t = 0;
        delete owl.phaseStartX;
        delete owl.phaseStartY;
      }
    } else if (owl.phase === 'drop') {
      const u = Math.min(1, owl.t / owl.d2);
      owl.y = owl.target.y - 28 + Math.sin(u * Math.PI) * 6;
      if (u > 0.5 && owl.hasLetter) {
        owl.hasLetter = false;
        packets.push({
          phase: 'approach_out',
          t: 0,
          d3: 0.5,
          sx: owl.x,
          sy: owl.y + 4,
          ex: owl.x,
          ey: owl.y,
          ox: owl.x,
          oy: owl.y,
          dx: owl.target.x,
          dy: owl.target.y + 6,
          color: '#fbf3dd',
        });
      }
      if (u >= 1) {
        owl.phase = 'fly_out';
        owl.t = 0;
        owl.phaseStartX = owl.x;
        owl.phaseStartY = owl.y;
      }
    } else if (owl.phase === 'fly_out') {
      const u = Math.min(1, owl.t / owl.d3);
      const ease = u * u;
      owl.x = owl.phaseStartX + (owl.exitX - owl.phaseStartX) * ease;
      owl.y = owl.phaseStartY + (owl.exitY - owl.phaseStartY) * ease - Math.sin(u * Math.PI) * 10;
      if (u >= 1) owls.splice(i, 1);
    }
  }
}

function drawOwls() {
  const time = performance.now() / 1000;
  for (const owl of owls) {
    if (!isWorldRectVisible(owl.x - 36, owl.y - 48, 72, 80, 80)) continue;
    const cx = owl.x * scale;
    const cy = owl.y * scale;
    const wingUp = Math.sin(time * 14) * 0.5 + 0.5 > 0.5;
    const groundY = (owl.target.y + 10) * scale;
    ctx.save();
    ctx.fillStyle = 'rgba(0,0,0,0.18)';
    ctx.beginPath();
    ctx.ellipse(cx, groundY, 10 * scale, 3 * scale, 0, 0, Math.PI * 2);
    ctx.fill();

    const facing = owl.dir;
    ctx.fillStyle = '#8a5f35';
    ctx.fillRect(cx - 6 * scale, cy - 6 * scale, 12 * scale, 10 * scale);
    ctx.fillStyle = '#a67a4a';
    ctx.fillRect(cx - 5 * scale, cy - 7 * scale, 10 * scale, 3 * scale);
    ctx.fillStyle = '#8a5f35';
    ctx.fillRect(cx - 5 * scale, cy - 11 * scale, 10 * scale, 6 * scale);
    ctx.fillStyle = '#a67a4a';
    ctx.fillRect(cx - 4 * scale, cy - 12 * scale, 8 * scale, 2 * scale);
    ctx.fillStyle = '#5a3d22';
    ctx.fillRect(cx - 5 * scale, cy - 13 * scale, 2 * scale, 2 * scale);
    ctx.fillRect(cx + 3 * scale, cy - 13 * scale, 2 * scale, 2 * scale);
    ctx.fillStyle = '#e8d5a8';
    ctx.fillRect(cx - 4 * scale, cy - 10 * scale, 8 * scale, 4 * scale);
    ctx.fillStyle = '#f0d056';
    ctx.fillRect(cx - 4 * scale, cy - 10 * scale, 3 * scale, 3 * scale);
    ctx.fillRect(cx + 1 * scale, cy - 10 * scale, 3 * scale, 3 * scale);
    ctx.fillStyle = '#2a1810';
    ctx.fillRect(cx - 3 * scale + (facing > 0 ? 1 : 0), cy - 9 * scale, 1 * scale, 1 * scale);
    ctx.fillRect(cx + 2 * scale + (facing > 0 ? 1 : 0), cy - 9 * scale, 1 * scale, 1 * scale);
    ctx.fillStyle = '#e0a93b';
    ctx.fillRect(cx - 1 * scale, cy - 7 * scale, 2 * scale, 2 * scale);
    ctx.fillStyle = '#6a4525';
    ctx.fillRect(cx - 4 * scale, cy - 2 * scale, 1, 1);
    ctx.fillRect(cx - 1 * scale, cy - 2 * scale, 1, 1);
    ctx.fillRect(cx + 2 * scale, cy - 2 * scale, 1, 1);
    ctx.fillRect(cx - 3 * scale, cy, 1, 1);
    ctx.fillRect(cx, cy, 1, 1);
    ctx.fillRect(cx + 3 * scale, cy, 1, 1);
    ctx.fillStyle = '#5a3d22';
    if (wingUp) {
      ctx.fillRect(cx - 10 * scale, cy - 10 * scale, 4 * scale, 6 * scale);
      ctx.fillRect(cx + 6 * scale, cy - 10 * scale, 4 * scale, 6 * scale);
      ctx.fillStyle = '#8a5f35';
      ctx.fillRect(cx - 9 * scale, cy - 9 * scale, 2 * scale, 3 * scale);
      ctx.fillRect(cx + 7 * scale, cy - 9 * scale, 2 * scale, 3 * scale);
    } else {
      ctx.fillStyle = '#5a3d22';
      ctx.fillRect(cx - 12 * scale, cy - 4 * scale, 6 * scale, 4 * scale);
      ctx.fillRect(cx + 6 * scale, cy - 4 * scale, 6 * scale, 4 * scale);
      ctx.fillStyle = '#8a5f35';
      ctx.fillRect(cx - 11 * scale, cy - 3 * scale, 4 * scale, 2 * scale);
      ctx.fillRect(cx + 7 * scale, cy - 3 * scale, 4 * scale, 2 * scale);
    }
    ctx.fillStyle = '#e0a93b';
    ctx.fillRect(cx - 3 * scale, cy + 4 * scale, 1 * scale, 2 * scale);
    ctx.fillRect(cx + 2 * scale, cy + 4 * scale, 1 * scale, 2 * scale);
    if (owl.hasLetter) {
      ctx.fillStyle = '#fbf3dd';
      ctx.fillRect(cx - 2 * scale, cy - 4 * scale, 4 * scale, 3 * scale);
      ctx.fillStyle = '#2a1810';
      ctx.fillRect(cx - 2 * scale, cy - 5 * scale, 4 * scale, 1);
      ctx.fillRect(cx - 2 * scale, cy - 1 * scale, 4 * scale, 1);
      ctx.fillStyle = '#d2553a';
      ctx.fillRect(cx - 1 * scale, cy - 3 * scale, 1, 1);
    }
    ctx.restore();
  }
}

/* ═══ Main loop ═══ */
let last = performance.now();
let heartTimer = 0;
function loop(now) {
  const dt = Math.min((now - last) / 1000, 0.1);
  last = now;
  requestAnimationFrame(loop);

  // Update
  for (const a of agents) a.update(dt);
  cat.update(dt);
  updateParticles(dt);
  if (!lowMotion) {
    updatePackets(dt);
    updateOwls(dt);
    updateCommunicationTransfers(dt);
  }
  heartTimer -= dt;
  if (!lowMotion && heartTimer <= 0) {
    heartTimer = 1.5 + Math.random();
    const working = agents.filter(a => a.state === 'working');
    if (working.length) {
      const a = working[Math.floor(Math.random() * working.length)];
      spawnHeart(a.x, a.y - 18);
    }
  }

  // Render
  ctx.clearRect(0, 0, cw, ch);
  drawFloor();
  drawZones();
  drawTeamHulls();
  if (isWorldRectVisible(TUBE.x - TUBE.radius - 10, TUBE.yTop - 16, TUBE.radius * 2 + 20, TUBE.yBot - TUBE.yTop + 32, 80)) {
    drawPneumaticTube();
  }
  if (!lowMotion) drawCommunicationTransfers();

  // Sort agents by Y, cat mixed in for correct overlap
  const drawables = [
    ...agents
      .filter(a => isWorldRectVisible(a.x - 50, a.y - 70, 100, 120, 80))
      .map(a => ({kind:'agent', o:a, y:a.y})),
    ...(isWorldRectVisible(cat.x - 42, cat.y - 42, 84, 84, 80) ? [{kind:'cat', o:cat, y:cat.y}] : []),
  ];
  drawables.sort((a, b) => a.y - b.y);
  for (const d of drawables) d.kind === 'agent' ? drawAgent(d.o) : drawCat(d.o);
  if (!lowMotion) {
    drawPackets();
    drawOwls();
  }
  drawParticles();
}

resize();
requestAnimationFrame(loop);

/* ═══ Interactivity ═══ */
canvas.addEventListener('click', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / scale;
  const my = (e.clientY - rect.top) / scale;
  const catDx = mx - cat.x;
  const catDy = my - (cat.y - 6);
  if (catDx * catDx + catDy * catDy < 16 * 16) {
    cat.pet(mx);
    return;
  }
  for (const a of agents) {
    const dx = mx - a.x, dy = my - a.y;
    if (Math.sqrt(dx*dx + dy*dy) < 22) {
      openAgentInspector(a);
      return;
    }
  }
  for (const [key, zone] of Object.entries(ZONE_MAP)) {
    const renderedZone = zoneView(key) || zone;
    if (renderedZone.agent && mx >= renderedZone.x && mx <= renderedZone.x + renderedZone.w && my >= renderedZone.y && my <= renderedZone.y + renderedZone.h) {
      const agent = agents.find(a => a.name === renderedZone.agent);
      if (agent) openAgentInspector(agent);
      return;
    }
  }
});

const tooltip = document.getElementById('tooltip');
canvas.addEventListener('mousemove', (e) => {
  const rect = canvas.getBoundingClientRect();
  const mx = (e.clientX - rect.left) / scale;
  const my = (e.clientY - rect.top) / scale;
  let hit = null;
  for (const a of agents) {
    const dx = mx - a.x, dy = my - a.y;
    if (Math.sqrt(dx*dx + dy*dy) < 22) { hit = a; break; }
  }
  const catDx = mx - cat.x;
  const catDy = my - (cat.y - 6);
  const overCat = (catDx * catDx + catDy * catDy) < 16 * 16;
  canvas.style.cursor = (hit || overCat) ? 'pointer' : '';
  if (hit) {
    tooltip.style.display = 'block';
    tooltip.style.left = (e.clientX - rect.left + 16) + 'px';
    tooltip.style.top = (e.clientY - rect.top - 8) + 'px';
    tooltip.querySelector('.tt-name').textContent = `${hit.name} · ${(hit.role || 'unassigned').toUpperCase()}`;
    tooltip.querySelector('.tt-state').textContent = hit.state.toUpperCase();
    tooltip.querySelector('.tt-state').style.color = hit.color;
    tooltip.querySelector('.tt-note').textContent = hit.note || '';
  } else {
    tooltip.style.display = 'none';
  }
});
canvas.addEventListener('mouseleave', () => tooltip.style.display = 'none');

function esc(s) {
  return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function truncate(s, n) {
  const text = String(s || '');
  return text.length > n ? text.slice(0, n) + '…' : text;
}

function basename(path) {
  return String(path || '').split('/').filter(Boolean).pop() || '—';
}

function formatCompactNumber(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number)) return '0';
  const abs = Math.abs(number);
  if (abs >= 1000000) return `${(number / 1000000).toFixed(abs >= 10000000 ? 0 : 1)}m`;
  if (abs >= 1000) return `${(number / 1000).toFixed(abs >= 10000 ? 0 : 1)}k`;
  return String(Math.round(number));
}

function formatUsd(value) {
  const number = Number(value || 0);
  if (!Number.isFinite(number) || number <= 0) return '$0.00';
  if (number < 0.01) return `$${number.toFixed(4)}`;
  return `$${number.toFixed(2)}`;
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') return '—';
  const number = Number(value);
  if (!Number.isFinite(number)) return '—';
  return `${Math.round(number * 100)}%`;
}

function firstNonEmpty(...values) {
  for (const value of values) {
    const text = String(value || '').trim();
    if (text) return text;
  }
  return '';
}

function normalizeReasonToken(value) {
  return String(value || '').trim().toLowerCase().replace(/[\s-]+/g, '_');
}

function isAuthAttentionReason(reason) {
  const text = normalizeReasonToken(reason);
  return AUTH_ATTENTION_MARKERS.some((marker) => text.includes(marker.replace(/\s+/g, '_')));
}

function labelForAttentionReason(reason, missingReason) {
  if (missingReason) return '개입 필요 사유 누락';
  const normalized = normalizeReasonToken(reason);
  if (ATTENTION_REASON_LABELS[normalized]) return ATTENTION_REASON_LABELS[normalized];
  if (normalized.endsWith('_auth_login_required')) return ATTENTION_REASON_LABELS.auth_login_required;
  if (normalized.endsWith('_credential_required') || isAuthAttentionReason(normalized)) {
    return ATTENTION_REASON_LABELS.credential_required;
  }
  if (normalized.includes('approval')) return ATTENTION_REASON_LABELS.approval_required;
  if (normalized.includes('truth_sync')) return ATTENTION_REASON_LABELS.truth_sync_required;
  if (normalized.includes('publication') || normalized.includes('pr_')) return ATTENTION_REASON_LABELS.publication_boundary;
  return reason ? '운영자 개입 필요' : '개입 필요';
}

function attentionTone(reason, missingReason) {
  if (missingReason) return 'missing';
  if (isAuthAttentionReason(reason)) return 'auth';
  return 'operator';
}

function attentionControlLabel(control) {
  const file = basename(control.active_control_file || '');
  const seq = Number(control.active_control_seq);
  if (file === '—' && (!Number.isFinite(seq) || seq < 0)) return '—';
  return `${file}${Number.isFinite(seq) && seq >= 0 ? ` · #${seq}` : ''}`;
}

function attentionLaneName(data, reason) {
  const autonomy = data.autonomy || {};
  const direct = firstNonEmpty(
    autonomy.blocking_lane,
    autonomy.active_lane,
    autonomy.lane,
    data.blocking_lane,
    data.active_lane,
    (currentTurnState(data) || {}).active_lane,
  );
  if (AGENT_NAMES.includes(direct)) return direct;
  const active = activeWorkLaneName(data);
  if (AGENT_NAMES.includes(active)) return active;
  const reasonText = normalizeReasonToken(reason);
  const lanes = Array.isArray(data.lanes) ? data.lanes : [];
  const broken = lanes.find((lane) => {
    const state = String(lane.state || '').toLowerCase();
    const note = normalizeReasonToken(lane.note || lane.status_note || '');
    return (state === 'broken' || state === 'dead') && (!reasonText || note.includes(reasonText) || isAuthAttentionReason(note));
  });
  if (broken && AGENT_NAMES.includes(broken.name)) return broken.name;
  const noted = lanes.find((lane) => /approval|operator|auth|credential|login|oauth|승인|인증|로그인/i.test(String(lane.note || lane.status_note || '')));
  return noted && AGENT_NAMES.includes(noted.name) ? noted.name : '';
}

function attentionDecisionText(data, reason, missingReason, laneName) {
  const autonomy = data.autonomy || {};
  const explicit = firstNonEmpty(
    autonomy.decision_required,
    autonomy.safe_user_action,
    data.decision_required,
    data.safe_user_action,
  );
  if (explicit) return explicit;
  if (missingReason) {
    return '이 stop을 만든 경로에서 reason_code와 decision_required를 함께 기록하도록 보강해 주세요.';
  }
  if (isAuthAttentionReason(reason)) {
    return laneName
      ? `${laneName} lane을 열어 로그인 또는 인증 입력을 완료해 주세요.`
      : '해당 lane을 열어 로그인 또는 인증 입력을 완료해 주세요.';
  }
  if (normalizeReasonToken(reason).includes('approval')) {
    return '요청 내용을 확인한 뒤 승인 또는 거절을 명시해 주세요.';
  }
  return 'operator_request와 최근 lane 로그를 확인해 다음 행동을 결정해 주세요.';
}

function attentionEvidenceText(data, reason, missingReason, laneName) {
  const autonomy = data.autonomy || {};
  const lane = laneName ? (data.lanes || []).find((item) => item.name === laneName) : null;
  const explicit = firstNonEmpty(
    autonomy.evidence_summary,
    data.evidence_summary,
    data.automation_health_detail,
    lane && (lane.note || lane.status_note),
  );
  if (explicit) return explicit;
  if (missingReason) {
    return 'runtime status가 needs_operator를 노출했지만 reason metadata를 찾지 못했습니다.';
  }
  if (reason) return `runtime status reason_code=${reason}`;
  return 'runtime status에서 operator 대기 상태를 감지했습니다.';
}

function buildOperatorAttention(data = runtimeStateStore.data) {
  const payload = data || {};
  const presentation = getPresentation(payload);
  const control = payload.control || {};
  const autonomy = payload.autonomy || {};
  const controlNeedsOperator = presentation.controlStatus === 'needs_operator';
  const healthNeedsOperator = presentation.automationHealth === 'needs_operator';
  if (!controlNeedsOperator && !healthNeedsOperator) return { visible: false };
  const reason = firstNonEmpty(
    autonomy.reason_code,
    autonomy.block_reason,
    payload.automation_reason_code,
    autonomy.degraded_reason,
    presentation.degradedReason,
  );
  const missingReason = !reason;
  const laneName = attentionLaneName(payload, reason);
  const roleName = laneName ? roleForAgent(laneName, payload) : '';
  return {
    visible: true,
    tone: attentionTone(reason, missingReason),
    title: labelForAttentionReason(reason, missingReason),
    reason: reason || 'reason_code_missing',
    laneName,
    roleName,
    controlLabel: attentionControlLabel(control),
    policy: firstNonEmpty(autonomy.operator_policy, autonomy.classification_source),
    decision: attentionDecisionText(payload, reason, missingReason, laneName),
    evidence: attentionEvidenceText(payload, reason, missingReason, laneName),
    nextAction: firstNonEmpty(payload.automation_next_action, healthNeedsOperator ? 'operator_required' : ''),
    operatorEligible: autonomy.operator_eligible,
  };
}

function renderOperatorAttentionBoard() {
  const board = document.getElementById('operator-attention-board');
  if (!board) return;
  const attention = buildOperatorAttention();
  if (!attention.visible) {
    board.className = 'operator-attention-board hidden';
    board.removeAttribute('data-lane');
    board.innerHTML = '';
    return;
  }
  board.className = `operator-attention-board ${attention.tone || 'operator'}`;
  board.dataset.lane = attention.laneName || '';
  const target = attention.laneName
    ? `${attention.laneName}${attention.roleName ? ` / ${attention.roleName.toUpperCase()}` : ''}`
    : '—';
  const actionLabel = attention.laneName ? `${attention.laneName} Terminal` : 'Terminal';
  board.innerHTML = `
    <div class="operator-attention-header">
      <div class="operator-attention-kicker">개입 필요</div>
      <div class="operator-attention-title">${esc(attention.title)}</div>
      <div class="operator-attention-reason">${esc(attention.reason)}</div>
    </div>
    <div class="operator-attention-body">
      <div class="operator-attention-row"><span>대상</span><span>${esc(target)}</span></div>
      <div class="operator-attention-row"><span>조치</span><span>${esc(attention.decision)}</span></div>
      <div class="operator-attention-row"><span>Control</span><span>${esc(attention.controlLabel)}</span></div>
      ${attention.nextAction ? `<div class="operator-attention-row"><span>Next</span><span>${esc(attention.nextAction)}</span></div>` : ''}
      ${attention.policy ? `<div class="operator-attention-row"><span>Policy</span><span>${esc(attention.policy)}</span></div>` : ''}
      ${attention.operatorEligible !== undefined ? `<div class="operator-attention-row"><span>Eligible</span><span>${esc(String(attention.operatorEligible))}</span></div>` : ''}
      <div class="operator-attention-evidence">${esc(attention.evidence)}</div>
    </div>
    <div class="operator-attention-actions">
      <button class="operator-attention-action" id="operator-attention-open-log" ${attention.laneName ? '' : 'disabled'}>${esc(actionLabel)}</button>
      <button class="operator-attention-action secondary" id="operator-attention-refresh">Refresh</button>
    </div>
  `;
}

function tokenHudSnapshot() {
  const snapshot = runtimeStateStore.monitor.snapshot || {};
  return snapshot.hud && typeof snapshot.hud === 'object' ? snapshot.hud : null;
}

function tokenMetricForAgent(agentName, hud = tokenHudSnapshot()) {
  if (!hud || !Array.isArray(hud.agents)) return null;
  return hud.agents.find((item) => item && item.name === agentName) || null;
}

function renderAgentTokenMeta(agent) {
  const metric = tokenMetricForAgent(agent.name);
  if (!metric) return '';
  const tokens = formatCompactNumber(metric.total_tokens || 0);
  const cost = formatUsd(metric.total_cost_usd || 0);
  const cache = formatPercent(metric.cache_hit_rate);
  return `<div class="agent-token-meta"><span>${esc(tokens)} tok</span><span>${esc(cost)}</span><span>${esc(cache)} cache</span></div>`;
}

function renderTokenHud() {
  const hud = tokenHudSnapshot();
  if (!hud) {
    return `
      <div class="sidebar-section token-hud">
        <div class="sidebar-section-title">Token HUD</div>
        <div class="info-row"><span class="info-label">Stream</span><span class="info-value dim">connecting</span></div>
      </div>
    `;
  }
  const totals = hud.totals || {};
  const collector = hud.collector || {};
  const agentsForHud = Array.isArray(hud.agents) ? hud.agents : [];
  const collectorClass = collector.phase === 'idle' || collector.phase === 'scanning' ? 'ok'
    : collector.phase === 'stale' || collector.is_stale ? 'warn'
    : collector.phase === 'error' ? 'err' : 'dim';
  const streamClass = runtimeStateStore.monitor.connected ? 'ok' : 'warn';
  const agentRows = agentsForHud.length ? agentsForHud.map((agent) => {
    const state = String(agent.state || 'off').toUpperCase();
    const activeClass = agent.active ? 'ok' : 'dim';
    return `
      <div class="token-agent-row" data-agent="${esc(agent.name)}">
        <span class="token-agent-name">${esc(agent.name)}</span>
        <span class="token-agent-state ${activeClass}">${esc(state)}</span>
        <span class="token-agent-number">${esc(formatCompactNumber(agent.total_tokens || 0))}</span>
        <span class="token-agent-cost">${esc(formatUsd(agent.total_cost_usd || 0))}</span>
        <span class="token-agent-cache">${esc(formatPercent(agent.cache_hit_rate))}</span>
      </div>
    `;
  }).join('') : '<div class="token-agent-empty">usage stream 대기 중</div>';
  return `
    <div class="sidebar-section token-hud">
      <div class="sidebar-section-title">Token HUD</div>
      <div class="info-row"><span class="info-label">Stream</span><span class="info-value ${streamClass}">${runtimeStateStore.monitor.connected ? 'live' : 'fallback'}</span></div>
      <div class="info-row"><span class="info-label">Collector</span><span class="info-value ${collectorClass}">${esc(collector.phase || 'missing')}</span></div>
      <div class="token-total-strip">
        <span><b>${esc(formatCompactNumber(totals.total_tokens || 0))}</b><em>tokens</em></span>
        <span><b>${esc(formatUsd(totals.total_cost_usd || 0))}</b><em>cost</em></span>
        <span><b>${esc(formatPercent(totals.cache_hit_rate))}</b><em>cache</em></span>
      </div>
      <div class="token-agent-list">${agentRows}</div>
    </div>
  `;
}

function agentInspectorDetails() {
  return runtimeStateStore.inspector.details || null;
}

function renderAgentInspector() {
  const drawer = document.getElementById('agent-inspector');
  const title = document.getElementById('ai-title');
  const kicker = document.getElementById('ai-kicker');
  const body = document.getElementById('ai-body');
  const logButton = document.getElementById('ai-open-log');
  if (!drawer || !title || !kicker || !body || !logButton) return;
  const selectedName = runtimeStateStore.inspector.selectedAgent;
  drawer.classList.toggle('open', Boolean(selectedName));
  logButton.disabled = !selectedName;
  if (!selectedName) {
    title.textContent = '—';
    kicker.textContent = 'Agent Inspector';
    body.innerHTML = '<div class="ai-empty">에이전트를 선택하면 세부 상태가 표시됩니다.</div>';
    return;
  }
  const agent = getAgent(selectedName);
  const details = agentInspectorDetails();
  const metric = tokenMetricForAgent(selectedName) || (details && details.metrics) || {};
  title.textContent = selectedName;
  kicker.textContent = `${(agent?.role || details?.agent?.role || 'agent').toUpperCase()} · ${(agent?.state || details?.agent?.state || 'off').toUpperCase()}`;
  if (runtimeStateStore.inspector.loading && !details) {
    body.innerHTML = '<div class="ai-loading">$ inspector --loading</div>';
    return;
  }
  const currentPrompt = details?.current_prompt || agent?.note || metric.prompt || '—';
  const conversation = Array.isArray(details?.conversation) ? details.conversation : [];
  const agentDetail = details?.agent || {};
  body.innerHTML = `
    <div class="ai-section">
      <div class="ai-section-title">Assignment</div>
      <div class="ai-row"><span>Role</span><span>${esc(agent?.role || agentDetail.role || '—')}</span></div>
      <div class="ai-row"><span>State</span><span>${esc(agent?.state || agentDetail.state || '—')}</span></div>
      <div class="ai-row"><span>PID</span><span>${esc(agentDetail.pid || agent?.pid || '—')}</span></div>
      <div class="ai-row"><span>Last event</span><span>${esc(agentDetail.last_event_at || agent?.lastEventAt || '—')}</span></div>
    </div>
    <div class="ai-section">
      <div class="ai-section-title">Usage</div>
      <div class="ai-row"><span>Tokens</span><span>${esc(formatCompactNumber(metric.total_tokens || agent?.tokenTotal || 0))}</span></div>
      <div class="ai-row"><span>Cost</span><span>${esc(formatUsd(metric.total_cost_usd || agent?.tokenCost || 0))}</span></div>
      <div class="ai-row"><span>Cache hit</span><span>${esc(formatPercent(metric.cache_hit_rate))}</span></div>
    </div>
    <div class="ai-section">
      <div class="ai-section-title">Current Prompt</div>
      <div class="ai-text">${esc(currentPrompt)}</div>
    </div>
    <div class="ai-section">
      <div class="ai-section-title">Recent Conversation</div>
      <div class="ai-conversation">${
        conversation.length
          ? conversation.map((line) => `<div class="ai-conversation-line">${esc(truncate(line, 220))}</div>`).join('')
          : '<div class="ai-conversation-line">tail 대기 중</div>'
      }</div>
    </div>
  `;
}

async function fetchAgentInspector(agentName) {
  const requestSeq = ++runtimeStateStore.inspector.requestSeq;
  runtimeStateStore.inspector.loading = true;
  renderAgentInspector();
  try {
    const response = await fetch(`/api/runtime/agent-inspector?agent=${encodeURIComponent(agentName)}&lines=180`);
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    if (requestSeq !== runtimeStateStore.inspector.requestSeq) return;
    runtimeStateStore.inspector.details = data;
  } catch (error) {
    if (requestSeq === runtimeStateStore.inspector.requestSeq) {
      runtimeStateStore.inspector.details = {
        ok: false,
        agent: { id: agentName },
        current_prompt: `인스펙터 조회 실패: ${getErrorMessage(error)}`,
        conversation: [],
        metrics: tokenMetricForAgent(agentName) || {},
      };
    }
  } finally {
    if (requestSeq === runtimeStateStore.inspector.requestSeq) {
      runtimeStateStore.inspector.loading = false;
      renderAgentInspector();
    }
  }
}

function openAgentInspector(agent) {
  if (!agent) return;
  runtimeStateStore.inspector.selectedAgent = agent.name;
  runtimeStateStore.inspector.details = null;
  renderSidebar();
  renderAgentInspector();
  fetchAgentInspector(agent.name);
}

function closeAgentInspector() {
  runtimeStateStore.inspector.selectedAgent = '';
  runtimeStateStore.inspector.details = null;
  runtimeStateStore.inspector.loading = false;
  renderSidebar();
  renderAgentInspector();
}

function getAgent(name) {
  return agents.find((agent) => agent.name === name) || null;
}

function sampleIdleTarget(agentName) {
  const agent = getAgent(agentName);
  const zone = agent ? movementZoneForAgent(agent) : null;
  if (!zone) return { x: 500, y: 350 };
  return {
    x: zone.x + 30 + Math.random() * (zone.w - 60),
    y: zone.y + zone.h * 0.4 + Math.random() * (zone.h * 0.3),
  };
}

function restartMarqueeAnimation() {
  const marquee = document.getElementById('marquee-text');
  if (!marquee) return;
  marquee.style.animation = 'none';
  void marquee.offsetWidth;
  marquee.style.animation = 'marquee-scroll 22s linear infinite';
}

function setMarqueeText(text) {
  const marquee = document.getElementById('marquee-text');
  if (!marquee) return;
  if (lastMarqueeText === text) return;
  marquee.textContent = text;
  lastMarqueeText = text;
  restartMarqueeAnimation();
}

function updateMarqueeFromState(data) {
  const payload = data || runtimeStateStore.data || {};
  const presentation = getPresentation(payload);
  const artifacts = payload.artifacts || {};
  const latestWork = basename((artifacts.latest_work || {}).path);
  const latestVerify = basename((artifacts.latest_verify || {}).path);
  const projectRoot = payload.project_root || 'runtime loading';
  setMarqueeText(`Runtime ${presentation.runtimeState} · Control ${presentation.controlStatus} · Work ${latestWork} · Verify ${latestVerify} · ${projectRoot}`);
}

function pushEvent(type, msg) {
  const time = new Date().toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  runtimeStateStore.events.unshift({ type, msg, time });
  if (runtimeStateStore.events.length > EVENT_LIMIT) runtimeStateStore.events.length = EVENT_LIMIT;
  renderEvents();
}

function getErrorMessage(error, fallback = 'unknown') {
  if (error && typeof error.message === 'string' && error.message.trim()) return error.message.trim();
  const text = String(error || '').trim();
  return text || fallback;
}

function recordStatusFetchFailure(error) {
  const message = getErrorMessage(error);
  if (runtimeStateStore.statusFetchFailureActive && runtimeStateStore.statusFetchFailureMessage === message) return;
  runtimeStateStore.statusFetchFailureActive = true;
  runtimeStateStore.statusFetchFailureMessage = message;
  pushEvent('err', `상태 조회 실패: ${message}`);
}

function clearStatusFetchFailure() {
  if (!runtimeStateStore.statusFetchFailureActive) return;
  const message = runtimeStateStore.statusFetchFailureMessage || 'unknown';
  runtimeStateStore.statusFetchFailureActive = false;
  runtimeStateStore.statusFetchFailureMessage = '';
  pushEvent('ok', `상태 조회 복구: ${message}`);
}

function renderEvents() {
  const el = document.getElementById('event-list');
  if (!el) return;
  if (!runtimeStateStore.events.length) {
    el.innerHTML = '<div class="event-item"><span class="event-time">—</span><span class="event-msg">대기 중</span></div>';
    return;
  }
  el.innerHTML = runtimeStateStore.events.map((event) =>
    `<div class="event-item"><span class="event-time">${esc(event.time)}</span><span class="event-dot ${esc(event.type)}"></span><span class="event-msg">${esc(event.msg)}</span></div>`
  ).join('');
}

const PrefStore = (() => {
  let available = null;
  let warned = false;
  function probe() {
    if (available !== null) return available;
    try {
      const key = '__office_storage_probe__';
      localStorage.setItem(key, '1');
      localStorage.removeItem(key);
      available = true;
    } catch (error) {
      available = false;
      if (!warned) {
        warned = true;
        pushEvent('warn', '환경 설정 저장 불가 — 새로고침 시 toolbar 설정이 초기화됩니다');
      }
    }
    return available;
  }
  return {
    get(key) { return probe() ? localStorage.getItem(key) : null; },
    set(key, value) { if (probe()) localStorage.setItem(key, value); },
    get available() { return probe(); },
  };
})();

function updateMuteButton() {
  const button = document.getElementById('mute-btn');
  if (!button) return;
  button.textContent = muted ? '🔇' : '🔊';
  button.title = muted ? '사운드 켜기' : '음소거';
}

function setMuted(nextMuted, persist = true) {
  muted = Boolean(nextMuted);
  updateMuteButton();
  if (!muted) unlockAudio8();
  if (persist) PrefStore.set('office_muted', muted ? '1' : '0');
}

let _audio8Context = null;

function ensureAudio8Context() {
  if (_audio8Context) return _audio8Context;
  try {
    _audio8Context = new (window.AudioContext || window.webkitAudioContext)();
  } catch (_error) {
    _audio8Context = null;
  }
  return _audio8Context;
}

function unlockAudio8() {
  const context = ensureAudio8Context();
  if (context && context.state === 'suspended') context.resume();
}

function playAudio8Meow() {
  if (muted) return;
  const context = ensureAudio8Context();
  if (!context) return;
  if (context.state === 'suspended') context.resume();
  const now = context.currentTime;
  const master = context.createGain();
  master.gain.setValueAtTime(0.0001, now);
  master.connect(context.destination);

  const lowpass = context.createBiquadFilter();
  lowpass.type = 'lowpass';
  lowpass.frequency.value = 2800;
  lowpass.Q.value = 0.6;
  lowpass.connect(master);

  [
    { t: 0.00, dur: 0.11, f0: 620, f1: 880, gain: 0.22 },
    { t: 0.10, dur: 0.18, f0: 780, f1: 380, gain: 0.28 },
  ].forEach(({ t, dur, f0, f1, gain }) => {
    const osc = context.createOscillator();
    osc.type = 'square';
    osc.frequency.setValueAtTime(f0, now + t);
    osc.frequency.exponentialRampToValueAtTime(Math.max(40, f1), now + t + dur);

    const lfo = context.createOscillator();
    const lfoGain = context.createGain();
    lfo.frequency.value = 14;
    lfoGain.gain.value = 18;
    lfo.connect(lfoGain);
    lfoGain.connect(osc.frequency);

    const gainNode = context.createGain();
    gainNode.gain.setValueAtTime(0.0001, now + t);
    gainNode.gain.exponentialRampToValueAtTime(gain, now + t + 0.015);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, now + t + dur);

    osc.connect(gainNode);
    gainNode.connect(lowpass);
    osc.start(now + t);
    lfo.start(now + t);
    osc.stop(now + t + dur + 0.02);
    lfo.stop(now + t + dur + 0.02);
  });

  master.gain.setValueAtTime(0.0001, now);
  master.gain.exponentialRampToValueAtTime(1.0, now + 0.01);
  master.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);
}

window.Audio8 = {
  meow: playAudio8Meow,
  unlock: unlockAudio8,
  get muted() { return muted; },
  setMuted(value) { setMuted(value); },
  toggle() {
    const nextMuted = !muted;
    setMuted(nextMuted);
    return nextMuted;
  },
};

function updateMotionButton() {
  const button = document.getElementById('motion-btn');
  if (!button) return;
  button.textContent = lowMotion ? '🚫' : '✨';
  button.title = lowMotion ? '장식 효과 켜기' : '장식 효과 줄이기';
}

function setLowMotion(nextLowMotion, persist = true) {
  lowMotion = Boolean(nextLowMotion);
  updateMotionButton();
  if (lowMotion) {
    particles.length = 0;
    packets.length = 0;
    owls.length = 0;
    communicationTransfers.length = 0;
  }
  if (persist) PrefStore.set('office_low_motion', lowMotion ? '1' : '0');
}

function getPresentation(data) {
  const payload = data || runtimeStateStore.data || {};
  const runtimeState = String(payload.runtime_state || 'STOPPED').toUpperCase();
  const control = payload.control || {};
  const watcher = payload.watcher || {};
  const turn = currentTurnState(payload);
  const degradedReasons = (payload.degraded_reasons || []).filter(Boolean);
  const degradedReason = degradedReasons[0] || String(payload.degraded_reason || '').trim();
  const automationHealth = String(payload.automation_health || 'ok').trim();
  const automationReason = String(payload.automation_reason_code || '').trim();
  const automationFamily = String(payload.automation_incident_family || '').trim();
  const automationAction = String(payload.automation_next_action || 'continue').trim();
  const automationDetail = String(payload.automation_health_detail || '').trim();
  const controlAgeCycles = Number(payload.control_age_cycles || 0);
  const staleAdvisoryPending = Boolean(payload.stale_advisory_pending);
  const uncertain = runtimeState === 'DEGRADED' && degradedReasons.some((reason) => UNCERTAIN_RUNTIME_REASONS.has(reason));
  const inactive = INACTIVE_RUNTIME_STATES.has(runtimeState);
  const showLive = !inactive && !uncertain;
  const controlStatus = showLive ? (control.active_control_status || 'none') : (uncertain ? 'uncertain' : 'none');
  const roundState = showLive ? liveRoundState(payload) : (uncertain ? 'uncertain' : 'IDLE');
  let watcherStatus = 'Dead';
  let watcherClass = 'dim';
  if (uncertain) {
    watcherStatus = 'Unknown';
    watcherClass = 'warn';
  } else if (watcher.alive) {
    watcherStatus = 'Alive';
    watcherClass = 'ok';
  } else if (runtimeState === 'BROKEN') {
    watcherClass = 'err';
  } else if (runtimeState === 'STOPPING') {
    watcherClass = 'neutral';
  }
  const controlClass = controlStatus === 'implement' ? 'ok'
    : controlStatus === 'needs_operator' || controlStatus === 'uncertain' ? 'warn'
    : controlStatus === 'none' ? 'dim' : 'neutral';
  const roundClass = roundState === 'uncertain' ? 'warn' : roundState === 'IDLE' ? 'dim' : 'neutral';
  const runtimeClass = runtimeState === 'RUNNING' ? 'ok'
    : runtimeState === 'DEGRADED' ? 'warn'
    : runtimeState === 'STOPPING' ? 'neutral'
    : runtimeState === 'BROKEN' ? 'err' : 'dim';
  const badgeClass = runtimeState === 'RUNNING' ? 'running'
    : runtimeState === 'DEGRADED' ? 'degraded'
    : runtimeState === 'STOPPING' ? 'stopping'
    : runtimeState === 'BROKEN' ? 'broken' : 'stopped';
  return {
    runtimeState,
    runtimeClass,
    badgeClass,
    uncertain,
    inactive,
    controlStatus,
    controlClass,
    roundState,
    roundClass,
    watcherStatus,
    watcherClass,
    degradedReason,
    degradedReasons,
    automationHealth,
    automationReason,
    automationFamily,
    automationAction,
    automationDetail,
    controlAgeCycles,
    staleAdvisoryPending,
  };
}

function detectChanges(data) {
  const presentation = getPresentation(data);
  const previous = runtimeStateStore.previous;
  const runtimeState = presentation.runtimeState;
  const controlStatus = presentation.controlStatus;
  const watcherStatus = presentation.watcherStatus;
  const uncertaintyChanged = previous.uncertainRuntime !== null && previous.uncertainRuntime !== presentation.uncertain;

  if (previous.runtimeState !== null && previous.runtimeState !== runtimeState) {
    const tone = runtimeState === 'RUNNING' ? 'ok'
      : runtimeState === 'DEGRADED' ? 'warn'
      : runtimeState === 'BROKEN' ? 'err' : 'info';
    pushEvent(tone, `Runtime: ${previous.runtimeState} → ${runtimeState}`);
  }
  previous.runtimeState = runtimeState;

  if (uncertaintyChanged) {
    pushEvent(presentation.uncertain ? 'warn' : 'info',
      presentation.uncertain ? `Runtime truth uncertain: ${presentation.degradedReason}` : 'Runtime truth restored');
  }
  previous.uncertainRuntime = presentation.uncertain;

  if (!uncertaintyChanged && previous.controlStatus !== null && previous.controlStatus !== controlStatus) {
    const tone = controlStatus === 'implement' ? 'ok'
      : controlStatus === 'needs_operator' || controlStatus === 'uncertain' ? 'warn' : 'info';
    pushEvent(tone, `Control: ${previous.controlStatus} → ${controlStatus}`);
  }
  previous.controlStatus = controlStatus;
  const approvalWait = controlStatus === 'needs_operator';
  if (previous.approvalWait !== null && previous.approvalWait !== approvalWait && approvalWait) {
    pushEvent('warn', '승인 대기: operator control gate');
  }
  previous.approvalWait = approvalWait;

  if (!uncertaintyChanged && previous.watcherStatus !== null && previous.watcherStatus !== watcherStatus) {
    const tone = watcherStatus === 'Alive' ? 'ok' : watcherStatus === 'Unknown' ? 'warn' : 'err';
    pushEvent(tone, `Watcher: ${previous.watcherStatus} → ${watcherStatus}`);
  }
  previous.watcherStatus = watcherStatus;

  const roundState = String((data.active_round || {}).state || 'IDLE').toUpperCase();
  if (previous.roundState !== null && previous.roundState !== roundState && (roundState === 'CLOSED' || roundState === 'DONE')) {
    pushEvent('ok', 'Round closed 🎉');
  }
  previous.roundState = roundState;

  for (const lane of (data.lanes || [])) {
    const name = lane.name || '';
    const state = String(lane.state || 'off').toLowerCase();
    const previousState = previous.laneStates[name];
    if (previousState !== undefined && previousState !== state) {
      const tone = state === 'working' ? 'ok' : (state === 'broken' || state === 'dead') ? 'err' : 'info';
      pushEvent(tone, `${name}: ${previousState} → ${state}`);
    }
    previous.laneStates[name] = state;
  }
}

function checkDeliveryTriggers(data) {
  const delivery = runtimeStateStore.delivery;
  const implementDesk = zoneKeyForRole('implement');
  const verifyDesk = zoneKeyForRole('verify');
  const controlSeq = (data.control || {}).active_control_seq;
  const artifacts = data.artifacts || {};
  const latestWorkPath = String((artifacts.latest_work || {}).path || '').trim();
  const latestWorkMtime = String((artifacts.latest_work || {}).mtime || '').trim();
  const latestVerifyPath = String((artifacts.latest_verify || {}).path || '').trim();
  const latestVerifyMtime = String((artifacts.latest_verify || {}).mtime || '').trim();
  const lastReceiptId = String(data.last_receipt_id || ((data.last_receipt || {}).receipt_id) || '').trim();

  if (!delivery.initialized) {
    Object.assign(delivery, {
      initialized: true,
      controlSeq,
      latestWorkPath,
      latestWorkMtime,
      latestVerifyPath,
      latestVerifyMtime,
      lastReceiptId,
    });
    return;
  }

  if (controlSeq != null && controlSeq >= 0 && delivery.controlSeq !== null && controlSeq !== delivery.controlSeq) {
    pushEvent('info', `Control seq → #${controlSeq}`);
    queueScenePacket(implementDesk, verifyDesk, '#a8cce0');
  }
  if (latestWorkPath && delivery.latestWorkPath && (latestWorkPath !== delivery.latestWorkPath || (latestWorkMtime && latestWorkMtime !== delivery.latestWorkMtime))) {
    pushEvent('ok', `Latest work → ${basename(latestWorkPath)}`);
    queueScenePacket(implementDesk, 'archive_shelf', '#f4d49a');
  }
  if (latestVerifyPath && delivery.latestVerifyPath && (latestVerifyPath !== delivery.latestVerifyPath || (latestVerifyMtime && latestVerifyMtime !== delivery.latestVerifyMtime))) {
    pushEvent('info', `Latest verify → ${basename(latestVerifyPath)}`);
    queueScenePacket(verifyDesk, 'archive_shelf', '#a8cce0');
  }
  if (delivery.lastReceiptId && lastReceiptId && lastReceiptId !== delivery.lastReceiptId) {
    pushEvent('ok', `Receipt issued → ${lastReceiptId}`);
    queueScenePacket(verifyDesk, 'receipt_board', '#fbf3dd');
    queueSceneOwl('receipt_board');
  }

  Object.assign(delivery, {
    controlSeq,
    latestWorkPath,
    latestWorkMtime,
    latestVerifyPath,
    latestVerifyMtime,
    lastReceiptId,
  });
}

function syncAgentsFromRuntime(data) {
  const lanesByName = new Map((data.lanes || []).map((lane) => [lane.name, lane]));
  for (const agent of agents) {
    const lane = lanesByName.get(agent.name);
    const previousState = agent.state;
    const previousNote = agent.note;
    if (lane) {
      agent.state = effectiveLaneState(agent.name, lane, data);
      agent.note = lane.note || lane.status_note || '';
      agent.pid = lane.pid || null;
      agent.lastEventAt = lane.last_event_at || '';
      if (agent.state !== 'working' && agent.fatigueState !== 'coffee' && agent.fatigueState !== 'fatigued') {
        agent.fatigueState = '';
      }
    } else {
      agent.state = 'off';
      agent.note = '';
      agent.pid = null;
      agent.lastEventAt = '';
      if (agent.fatigueState !== 'coffee' && agent.fatigueState !== 'fatigued') {
        agent.fatigueState = '';
      }
    }
    applyAgentRoleBinding(agent, data, { snap: !agent.hasRuntimeSync });
    agent.hasRuntimeSync = true;
    if (agent.note && previousNote !== agent.note) agent.setBubble(agent.note);
    if (previousState !== agent.state && previousState !== 'off' && !agent.note) {
      agent.setBubble(`${agent.state.toUpperCase()} 상태`);
    }
  }
}

function roleOwnerRows(data = runtimeStateStore.data) {
  const owners = currentRoleOwners(data);
  return ROLE_NAMES.map((role) => {
    const title = ROLE_OWNER_LABELS[role] || `${role} owner`;
    const owner = owners[role] || 'Unassigned';
    return `<div class="info-row"><span class="info-label">${esc(title)}</span><span class="info-value neutral">${esc(owner)}</span></div>`;
  }).join('');
}

function renderSidebar() {
  const container = document.getElementById('tab-content');
  if (!container) return;
  const data = runtimeStateStore.data || {};
  const presentation = getPresentation(data);
  const control = data.control || {};
  const artifacts = data.artifacts || {};
  const lastReceipt = data.last_receipt || {};
  const autonomy = data.autonomy || {};
  const degradedReasons = (data.degraded_reasons || []).filter(Boolean);
  const laneCards = agents.map((agent) => {
    const skin = characterSkinForAgent(agent.name);
    const note = agent.note || '';
    const fatigue = agent.fatigueState || '';
    const fatigueLabel = fatigue === 'coffee' ? '☕ 커피 충전 중' : fatigue === 'fatigued' ? '💦 피로 누적' : '';
    const selectedClass = runtimeStateStore.inspector.selectedAgent === agent.name ? ' selected' : '';
    return `<div class="agent-card${selectedClass}" data-agent="${esc(agent.name)}" data-fatigue="${esc(fatigue)}">
      <div class="agent-avatar" style="background:${agent.color}">${esc(agent.name[0])}</div>
      <div class="agent-info">
        <div class="agent-name">${esc(agent.name)}</div>
        <div class="agent-role">${esc(agent.role)} · ${esc(skin.label)}</div>
        ${note ? `<div class="agent-detail">${esc(truncate(note, 46))}</div>` : ''}
        ${fatigueLabel ? `<div class="agent-fatigue" data-fatigue="${esc(fatigue)}">${fatigueLabel}</div>` : ''}
        ${renderAgentTokenMeta(agent)}
      </div>
      <div class="agent-state-dot" style="background:${agent.color}"></div>
    </div>`;
  }).join('');

  container.innerHTML = `
    <div class="sidebar-section">
      <div class="sidebar-section-title">Party Roster</div>
      ${laneCards}
    </div>
    ${renderTokenHud()}
    <div class="sidebar-section">
      <div class="sidebar-section-title">Role Binding</div>
      ${roleOwnerRows(data)}
    </div>
    <div class="sidebar-section">
      <div class="sidebar-section-title">Current Round</div>
      <div class="info-row"><span class="info-label">Runtime</span><span class="info-value ${presentation.runtimeClass}">${esc(presentation.runtimeState)}</span></div>
      <div class="info-row"><span class="info-label">Control</span><span class="info-value ${presentation.controlClass}">${esc(presentation.controlStatus)}</span></div>
      <div class="info-row"><span class="info-label">Seq</span><span class="info-value dim">${control.active_control_seq >= 0 ? `#${control.active_control_seq}` : '—'}</span></div>
      <div class="info-row"><span class="info-label">Round</span><span class="info-value ${presentation.roundClass}">${esc(presentation.roundState)}</span></div>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-section-title">Artifacts</div>
      <div class="info-row"><span class="info-label">Latest work</span><span class="info-value">${esc(truncate(basename((artifacts.latest_work || {}).path), 24))}</span></div>
      <div class="info-row"><span class="info-label">Latest verify</span><span class="info-value">${esc(truncate(basename((artifacts.latest_verify || {}).path), 24))}</span></div>
      <div class="info-row"><span class="info-label">Receipt ID</span><span class="info-value dim">${esc(lastReceipt.receipt_id || data.last_receipt_id || '—')}</span></div>
      <div class="info-row"><span class="info-label">Receipt result</span><span class="info-value ${(lastReceipt.verify_result || '') === 'passed' ? 'ok' : (lastReceipt.verify_result ? 'warn' : 'dim')}">${esc(lastReceipt.verify_result || '—')}</span></div>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-section-title">Incident Room</div>
      <div class="info-row"><span class="info-label">Watcher</span><span class="info-value ${presentation.watcherClass}">${esc(presentation.watcherStatus)}</span></div>
      <div class="info-row"><span class="info-label">Automation</span><span class="info-value ${presentation.automationHealth === 'ok' ? 'ok' : 'warn'}">${esc(presentation.automationHealth)}</span></div>
      ${presentation.automationReason ? `<div class="info-row"><span class="info-label">Reason</span><span class="info-value warn">${esc(presentation.automationReason)}</span></div>` : ''}
      ${presentation.automationFamily ? `<div class="info-row"><span class="info-label">Family</span><span class="info-value neutral">${esc(presentation.automationFamily)}</span></div>` : ''}
      ${presentation.automationAction ? `<div class="info-row"><span class="info-label">Next action</span><span class="info-value neutral">${esc(presentation.automationAction)}</span></div>` : ''}
      ${presentation.automationDetail ? `<div class="info-row"><span class="info-label">Detail</span><span class="info-value warn">${esc(presentation.automationDetail)}</span></div>` : ''}
      ${presentation.controlAgeCycles ? `<div class="info-row"><span class="info-label">Control age</span><span class="info-value dim">${esc(String(presentation.controlAgeCycles))}</span></div>` : ''}
      ${presentation.staleAdvisoryPending ? `<div class="info-row"><span class="info-label">Advisory</span><span class="info-value warn">stale_advisory_pending</span></div>` : ''}
      <div class="info-row"><span class="info-label">Operator eligible</span><span class="info-value dim">${esc(String(autonomy.operator_eligible ?? false))}</span></div>
      ${degradedReasons.map((reason) => `<div class="info-row"><span class="info-label">Degraded</span><span class="info-value warn">${esc(reason)}</span></div>`).join('')}
    </div>
  `;
}

function applyRuntimeStatusData(data) {
  clearStatusFetchFailure();
  runtimeStateStore.data = data;
  detectChanges(data);
  checkDeliveryTriggers(data);
  syncAgentsFromRuntime(data);
  renderSidebar();
  renderOperatorAttentionBoard();
  renderStatus(data);
  updateMarqueeFromState(data);
}

function communicationEventKey(event) {
  if (event.sequence != null) return `seq:${event.sequence}`;
  return `${event.from || ''}:${event.to || ''}:${event.event_type || ''}:${event.time_ms || ''}:${event.message || ''}`;
}

function consumeMonitorCommunications(snapshot) {
  const events = Array.isArray(snapshot.communications) ? snapshot.communications : [];
  const seen = runtimeStateStore.monitor.seenCommunications;
  for (const event of events) {
    if (!event || !event.from || !event.to) continue;
    const key = communicationEventKey(event);
    if (seen.has(key)) continue;
    seen.add(key);
    queueCommunicationTransfer(event.from, event.to, communicationLabel(event), event.color || '#6aa7c9');
  }
  if (seen.size > 240) {
    runtimeStateStore.monitor.seenCommunications = new Set(Array.from(seen).slice(-120));
  }
}

function consumeMonitorApprovalWait(snapshot) {
  const previous = runtimeStateStore.monitor.previousApprovalWait;
  const coordination = snapshot.coordination_state || snapshot.log_state || {};
  for (const agent of agents) {
    const value = coordination[agent.name] || {};
    const waiting = value.approval_wait === true || Boolean(value.approval_wait?.waiting || value.approval_wait?.required);
    if (waiting && previous[agent.name] !== true) {
      pushEvent('warn', `${agent.name}: 승인 대기`);
    }
    previous[agent.name] = waiting;
  }
}

function applyMonitorSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== 'object') return;
  runtimeStateStore.monitor.snapshot = snapshot;
  consumeMonitorCommunications(snapshot);
  consumeMonitorApprovalWait(snapshot);
  const hud = snapshot.hud || {};
  const previous = runtimeStateStore.monitor.previousAgentTokens;
  for (const metric of Array.isArray(hud.agents) ? hud.agents : []) {
    const agent = getAgent(metric.name);
    if (!agent) continue;
    const total = Number(metric.total_tokens || 0);
    const previousTotal = previous[agent.name];
    agent.tokenTotal = total;
    agent.tokenCost = Number(metric.total_cost_usd || 0);
    if (previousTotal !== undefined && total > previousTotal) {
      const delta = total - previousTotal;
      if (!lowMotion) agent.tokenPulse = 1.2;
      if (delta >= 100) agent.setBubble(`+${formatCompactNumber(delta)} tok`);
    }
    previous[agent.name] = total;
  }
  if (snapshot.runtime && typeof snapshot.runtime === 'object') {
    applyRuntimeStatusData(snapshot.runtime);
  } else {
    renderSidebar();
    renderOperatorAttentionBoard();
  }
  if (runtimeStateStore.inspector.selectedAgent) renderAgentInspector();
}

function monitorStreamUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws/runtime/monitor`;
}

function runtimeMonitorDisabled() {
  return Boolean(window.__officeRuntimeMonitorDisabled);
}

function monitorSocketDisabled() {
  return runtimeMonitorDisabled() || Boolean(window.__officeMonitorSocketDisabled);
}

function scheduleMonitorReconnect() {
  if (runtimeMonitorDisabled()) return;
  if (runtimeStateStore.monitor.reconnectTimer) return;
  runtimeStateStore.monitor.reconnectTimer = window.setTimeout(() => {
    runtimeStateStore.monitor.reconnectTimer = null;
    connectMonitorStream();
  }, 2500);
}

function connectMonitorStream() {
  if (monitorSocketDisabled()) return;
  if (!('WebSocket' in window) || monitorSocket) return;
  try {
    monitorSocket = new WebSocket(monitorStreamUrl());
  } catch (error) {
    pushEvent('warn', `실시간 모니터 연결 실패: ${getErrorMessage(error)}`);
    scheduleMonitorReconnect();
    return;
  }
  monitorSocket.addEventListener('open', () => {
    runtimeStateStore.monitor.connected = true;
    pushEvent('ok', '실시간 모니터 연결됨');
    renderSidebar();
  });
  monitorSocket.addEventListener('message', (event) => {
    try {
      applyMonitorSnapshot(JSON.parse(event.data));
    } catch (error) {
      pushEvent('warn', `실시간 모니터 payload 무시: ${getErrorMessage(error)}`);
    }
  });
  monitorSocket.addEventListener('close', () => {
    const wasConnected = runtimeStateStore.monitor.connected;
    runtimeStateStore.monitor.connected = false;
    monitorSocket = null;
    if (wasConnected) pushEvent('warn', '실시간 모니터 연결 끊김 — polling fallback');
    renderSidebar();
    scheduleMonitorReconnect();
  });
  monitorSocket.addEventListener('error', () => {
    if (monitorSocket) monitorSocket.close();
  });
}

async function pollMonitorSnapshot() {
  if (runtimeMonitorDisabled()) return;
  if (runtimeStateStore.monitor.connected || monitorFallbackInFlight) return;
  monitorFallbackInFlight = true;
  try {
    const response = await fetch('/api/runtime/monitor-snapshot');
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    applyMonitorSnapshot(data);
  } catch (error) {
    if (!runtimeStateStore.monitor.snapshot) {
      pushEvent('warn', `토큰 HUD 조회 실패: ${getErrorMessage(error)}`);
    }
  } finally {
    monitorFallbackInFlight = false;
  }
}

async function pollRuntime() {
  if (runtimeStateStore.monitor.connected) return;
  if (pollInFlight) return;
  pollInFlight = true;
  try {
    const response = await fetch('/api/runtime/status');
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || `HTTP ${response.status}`);
    applyRuntimeStatusData(data);
  } catch (error) {
    recordStatusFetchFailure(error);
  } finally {
    pollInFlight = false;
  }
}

function renderStatus(data) {
  const presentation = getPresentation(data);
  const badge = document.getElementById('status-badge');
  badge.textContent = presentation.runtimeState;
  badge.className = `badge ${presentation.badgeClass}`;
  document.getElementById('project-path').textContent = data.project_root || '—';
}

let logRefreshInterval = null;
let logRefreshInFlight = false;
let modalLaneName = '';
let modalSendInFlight = false;

function setLogSendStatus(message, tone = '') {
  const el = document.getElementById('lm-send-status');
  if (!el) return;
  el.textContent = message || '';
  el.classList.remove('ok', 'err');
  if (tone) el.classList.add(tone);
}

function syncModalInputState() {
  const input = document.getElementById('lm-input');
  const button = document.getElementById('lm-send');
  if (!input || !button) return;
  const hasLane = Boolean(modalLaneName);
  const hasText = Boolean(String(input.value || '').trim());
  input.disabled = !hasLane || modalSendInFlight;
  button.disabled = !hasLane || !hasText || modalSendInFlight;
}

async function fetchTail(laneName, bodyEl) {
  if (logRefreshInFlight) return;
  logRefreshInFlight = true;
  try {
    const res = await fetch(`/api/runtime/capture-tail?lane=${encodeURIComponent(laneName)}&lines=100`);
    const data = await res.json();
    if (data.ok && data.text) {
      const wasAtBottom = bodyEl.scrollHeight - bodyEl.scrollTop - bodyEl.clientHeight < 40;
      bodyEl.textContent = data.text;
      if (wasAtBottom) bodyEl.scrollTop = bodyEl.scrollHeight;
    } else {
      bodyEl.innerHTML = `<span class="log-loading">(${esc(laneName)} — 활성 로그 없음)</span>`;
    }
  } catch (error) {
    bodyEl.innerHTML = `<span class="log-loading">(로그 조회 실패: ${esc(error.message)})</span>`;
  } finally {
    logRefreshInFlight = false;
  }
}

async function openLogModal(agent) {
  modalLaneName = agent.name;
  const modal = document.getElementById('log-modal');
  document.getElementById('lm-dot').style.background = agent.color;
  document.getElementById('lm-name').textContent = agent.name;
  document.getElementById('lm-role').textContent = agent.role;
  const stateEl = document.getElementById('lm-state');
  stateEl.textContent = agent.state.toUpperCase();
  stateEl.style.background = agent.color;
  document.getElementById('lm-info').innerHTML = [
    agent.pid ? `PID ${esc(agent.pid)}` : null,
    agent.note ? `note: ${esc(truncate(agent.note, 60))}` : null,
    agent.lastEventAt ? `event: ${esc(agent.lastEventAt)}` : null,
  ].filter(Boolean).map((item) => `<span>${item}</span>`).join('');
  const body = document.getElementById('lm-body');
  const input = document.getElementById('lm-input');
  body.innerHTML = '<span class="log-loading">$ tail -f …</span>';
  if (input) input.value = '';
  setLogSendStatus('숫자 선택이나 짧은 응답이 필요한 prompt가 뜨면 여기서 바로 보내실 수 있습니다.');
  syncModalInputState();
  modal.classList.add('open');
  await fetchTail(agent.name, body);
  requestAnimationFrame(() => { if (input) input.focus(); });
  if (logRefreshInterval) clearInterval(logRefreshInterval);
  logRefreshInterval = setInterval(() => {
    if (!modal.classList.contains('open')) {
      clearInterval(logRefreshInterval);
      logRefreshInterval = null;
      return;
    }
    fetchTail(agent.name, body);
  }, LOG_REFRESH_MS);
}

function closeLogModal(event) {
  if (event && event.target !== document.getElementById('log-modal')) return;
  document.getElementById('log-modal').classList.remove('open');
  modalLaneName = '';
  modalSendInFlight = false;
  const input = document.getElementById('lm-input');
  if (input) {
    input.value = '';
    input.disabled = true;
  }
  setLogSendStatus('');
  syncModalInputState();
  logRefreshInFlight = false;
  if (logRefreshInterval) {
    clearInterval(logRefreshInterval);
    logRefreshInterval = null;
  }
}

async function sendModalInput() {
  const lane = String(modalLaneName || '').trim();
  const input = document.getElementById('lm-input');
  const body = document.getElementById('lm-body');
  const text = String(input?.value || '');
  if (!lane || !text.trim() || modalSendInFlight) return;
  modalSendInFlight = true;
  syncModalInputState();
  setLogSendStatus(`${lane}에 입력 전송 중…`);
  try {
    const response = await fetch('/api/runtime/send-input', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lane, text }),
    });
    const data = await response.json();
    if (!response.ok || data.ok === false) throw new Error(data.error || 'send failed');
    if (input) input.value = '';
    setLogSendStatus(`${lane}에 입력을 보냈습니다.`, 'ok');
    pushEvent('info', `${lane}에 입력 전송`);
    await fetchTail(lane, body);
    setTimeout(() => fetchTail(lane, body), 350);
  } catch (error) {
    setLogSendStatus(`입력 전송 실패: ${error.message}`, 'err');
    pushEvent('err', `입력 전송 실패: ${error.message}`);
  } finally {
    modalSendInFlight = false;
    syncModalInputState();
    if (input) input.focus();
  }
}

async function apiPost(path) {
  try {
    const response = await fetch(path, { method: 'POST' });
    const data = await response.json();
    if (!response.ok || data.ok === false) {
      pushEvent('err', `요청 실패: ${data.error || 'unknown'}`);
      return;
    }
    pushEvent('ok', `${path.split('/').pop()} 완료`);
    setTimeout(pollRuntime, ACTION_REPOLL_MS);
  } catch (error) {
    pushEvent('err', `요청 실패: ${error.message}`);
  }
}

document.getElementById('btn-start').onclick = () => apiPost('/api/runtime/start');
document.getElementById('btn-stop').onclick = () => apiPost('/api/runtime/stop');
document.getElementById('btn-restart').onclick = () => apiPost('/api/runtime/restart');
document.getElementById('mute-btn').onclick = () => setMuted(!muted);
document.getElementById('motion-btn').onclick = () => setLowMotion(!lowMotion);

document.getElementById('log-modal').addEventListener('click', (event) => closeLogModal(event));
document.getElementById('lm-close').addEventListener('click', () => closeLogModal());
document.addEventListener('keydown', (event) => {
  if (event.key !== 'Escape') return;
  closeLogModal();
  closeAgentInspector();
});
document.getElementById('lm-input').addEventListener('input', syncModalInputState);
document.getElementById('lm-input').addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    sendModalInput();
  }
});
document.getElementById('lm-send').addEventListener('click', sendModalInput);
document.getElementById('ai-close').addEventListener('click', closeAgentInspector);
document.getElementById('ai-open-log').addEventListener('click', () => {
  const agent = getAgent(runtimeStateStore.inspector.selectedAgent);
  if (agent) openLogModal(agent);
});
document.getElementById('operator-attention-board').addEventListener('click', (event) => {
  const openLog = event.target.closest('#operator-attention-open-log');
  const refresh = event.target.closest('#operator-attention-refresh');
  if (openLog) {
    const agent = getAgent(event.currentTarget.dataset.lane || '');
    if (agent) openLogModal(agent);
    return;
  }
  if (refresh) {
    pollRuntime();
    pollMonitorSnapshot();
  }
});

document.getElementById('tab-content').addEventListener('click', (event) => {
  const card = event.target.closest('.agent-card');
  if (!card) return;
  const agent = getAgent(card.getAttribute('data-agent'));
  if (agent) openAgentInspector(agent);
});

window.setAgentFatigue = function(name, value) {
  const agent = getAgent(name);
  if (!agent) return;
  if (value === 'coffee') agent.fatigueState = 'coffee';
  else if (value === 'fatigued') agent.fatigueState = 'fatigued';
  else agent.fatigueState = '';
  renderSidebar();
};

window.getRoamBounds = function() {
  return {
    zones: ZONE_MAP,
    restZones: Object.fromEntries(AGENT_NAMES.map((name) => [name, loungeSeatZone(name)])),
    pathObstacles: PATH_OBSTACLES,
  };
};

window.testPickIdleTargets = function(name, count) {
  const points = [];
  for (let i = 0; i < count; i++) points.push(sampleIdleTarget(name));
  return points;
};

window.testAntiStacking = function(name, _x, _y, count) {
  return window.testPickIdleTargets(name, count);
};

window.testHistoryPenalty = function() {
  return [];
};

window.getSceneDebug = function() {
  return {
    hasWindowRenderer: typeof drawWindow === 'function',
    hasPneumaticTube: typeof drawPneumaticTube === 'function',
    hasPacketCourier: typeof sendPacket === 'function',
    hasOwlCourier: typeof sendOwl === 'function',
    hasTeamHullRenderer: typeof drawTeamHulls === 'function',
    hasCommunicationTransfer: typeof queueCommunicationTransfer === 'function',
    hasApprovalMarker: typeof drawApprovalMarker === 'function',
    hasViewCulling: typeof isWorldRectVisible === 'function',
    hasAudio8: typeof window.Audio8?.meow === 'function',
    catState: cat.state,
    roleOwners: currentRoleOwners(),
    characterSkins: Object.fromEntries(AGENT_NAMES.map((name) => [name, characterSkinForAgent(name).label])),
    teamCount: monitorTeams().length,
    communicationTransferCount: communicationTransfers.length,
    approvalWaitingAgents: agents.filter((agent) => approvalWaitingForAgent(agent)).map((agent) => agent.name),
    camera: cameraView(),
    tube: { ...TUBE },
  };
};

window.getOperatorAttentionDebug = function() {
  return buildOperatorAttention();
};

window.getAgentPositions = function() {
  return Object.fromEntries(
    agents.map((agent) => [
      agent.name,
      {
        x: agent.x,
        y: agent.y,
        tx: agent.tx,
        ty: agent.ty,
        state: agent.state,
        atLounge: !!agent.atLounge,
        pathLength: agent.path.length,
        animationState: animationStateForAgent(agent),
        teamId: teamForAgent(agent.name)?.id || '',
        approvalWaiting: approvalWaitingForAgent(agent),
      },
    ]),
  );
};

window.getTeamDebug = function() {
  return {
    teams: monitorTeams(),
    communicationTransferCount: communicationTransfers.length,
    approvalWaitingAgents: agents.filter((agent) => approvalWaitingForAgent(agent)).map((agent) => agent.name),
    camera: cameraView(),
  };
};

window.testPetCat = function() {
  cat.pet(cat.x + 10);
  return {
    catState: cat.state,
    particleCount: particles.length,
    hasAudio8: typeof window.Audio8?.meow === 'function',
  };
};

const TWEAKS = /*EDITMODE-BEGIN*/{
  timeOfDay: 'auto',
  showWindow: true,
}/*EDITMODE-END*/;

function applyTweaks() {
  const timeOfDay = TWEAKS.timeOfDay;
  if (timeOfDay === 'auto') window.__timeOverride = null;
  else if (timeOfDay === 'dawn') window.__timeOverride = 6.5;
  else if (timeOfDay === 'day') window.__timeOverride = 13;
  else if (timeOfDay === 'sunset') window.__timeOverride = 18.5;
  else if (timeOfDay === 'night') window.__timeOverride = 22;
  window.__hideWindow = !TWEAKS.showWindow;
}

function buildTweaksPanel() {
  if (document.getElementById('tweaks-panel')) return;
  const panel = document.createElement('div');
  panel.id = 'tweaks-panel';
  panel.style.cssText = `
    position: fixed; right: 18px; bottom: 18px; z-index: 90;
    background: var(--parchment-bright, #fbf3dd);
    color: var(--ink, #2a1810);
    font-family: 'Galmuri11', 'DungGeunMo', monospace;
    padding: 14px; min-width: 220px;
    box-shadow: 0 -3px 0 0 #2a1810, 0 3px 0 0 #2a1810, -3px 0 0 0 #2a1810, 3px 0 0 0 #2a1810, 6px 6px 0 0 rgba(0,0,0,0.25);
    display: none;
  `;
  panel.innerHTML = `
    <div style="font-size:13px; letter-spacing:0.08em; color:#5c3b22; border-bottom:2px dashed #c9a875; padding-bottom:6px; margin-bottom:10px; text-transform:uppercase;">
      ✦ Tweaks
    </div>
    <div style="font-size:11px; color:#5a3d28; margin-bottom:6px;">Time of day</div>
    <div id="tweak-tod" style="display:grid; grid-template-columns: 1fr 1fr 1fr; gap:4px; margin-bottom:12px;">
      ${['auto', 'dawn', 'day', 'sunset', 'night'].map((value) => `
        <button data-tod="${value}" style="
          font-family: inherit; font-size: 11px;
          padding: 6px 4px; cursor: pointer;
          background: ${TWEAKS.timeOfDay === value ? '#e0a93b' : '#fbf3dd'};
          color: #2a1810; border: none;
          box-shadow: 0 -2px 0 0 #2a1810, 0 2px 0 0 #2a1810, -2px 0 0 0 #2a1810, 2px 0 0 0 #2a1810, inset 2px 2px 0 0 rgba(255,255,255,0.3), inset -2px -2px 0 0 rgba(0,0,0,0.15);
        ">${value}</button>
      `).join('')}
    </div>
    <label style="display:flex; align-items:center; gap:6px; font-size:11px; color:#5a3d28; cursor:pointer;">
      <input type="checkbox" id="tweak-win" ${TWEAKS.showWindow ? 'checked' : ''} style="width:14px; height:14px;">
      Show windows
    </label>
  `;
  document.body.appendChild(panel);

  panel.querySelectorAll('[data-tod]').forEach((button) => {
    button.addEventListener('click', () => {
      TWEAKS.timeOfDay = button.dataset.tod;
      applyTweaks();
      panel.querySelectorAll('[data-tod]').forEach((other) => {
        other.style.background = TWEAKS.timeOfDay === other.dataset.tod ? '#e0a93b' : '#fbf3dd';
      });
      window.parent.postMessage({ type: '__edit_mode_set_keys', edits: { timeOfDay: TWEAKS.timeOfDay } }, '*');
    });
  });

  panel.querySelector('#tweak-win').addEventListener('change', (event) => {
    TWEAKS.showWindow = event.target.checked;
    applyTweaks();
    window.parent.postMessage({ type: '__edit_mode_set_keys', edits: { showWindow: TWEAKS.showWindow } }, '*');
  });
}

renderSidebar();
renderAgentInspector();
renderEvents();
applyTweaks();
buildTweaksPanel();
setMuted(PrefStore.get('office_muted') === '1', false);
setLowMotion(PrefStore.get('office_low_motion') === '1', false);
if (!PrefStore.available) {
  const chip = document.getElementById('storage-warn');
  if (chip) chip.style.display = 'inline-block';
}
window.addEventListener('pointerdown', unlockAudio8, { once: true });
window.addEventListener('message', (event) => {
  if (!event.data || !event.data.type) return;
  const panel = document.getElementById('tweaks-panel');
  if (!panel) return;
  if (event.data.type === '__activate_edit_mode') {
    panel.style.display = 'block';
  } else if (event.data.type === '__deactivate_edit_mode') {
    panel.style.display = 'none';
  }
});
window.parent.postMessage({ type: '__edit_mode_available' }, '*');
resize();
requestAnimationFrame(loop);
connectMonitorStream();
pollMonitorSnapshot();
pollRuntime();
setInterval(() => pollRuntime(), POLL_MS);
setInterval(() => pollMonitorSnapshot(), POLL_MS);
