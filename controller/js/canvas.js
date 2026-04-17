// controller/js/canvas.js — Canvas render loop, isometric background, zone boundaries
import { ZONE_MAP, CORRIDOR_Y, VIRTUAL_W, VIRTUAL_H, SEVERITY_MAP, INACTIVE_RUNTIME_STATES } from './config.js';
import { PipelineState } from './state.js';
import { agents, particles } from './agents.js';
import {
  archiveCubeFlights,
  completeArchiveFlightsImmediately,
  deliveryPackets,
  drainArchiveCubeLandings,
  drawDataCube,
  drones,
} from './delivery.js';
import { AmbientAudio, SoundFX } from './audio.js';

let _lowMotion = false;
export function isLowMotion() { return _lowMotion; }
export function setLowMotion(v) { _lowMotion = v; if (v) { particles.length = 0; deliveryPackets.length = 0; drones.length = 0; } }

const archiveShelfCubes = [];
const ARCHIVE_VISIBLE_LIMIT = 10;
const ARCHIVE_FADE_MS = 1400;

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

// ── Isometric background ──
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
    const icon = key.includes('desk') ? '\u{1F5A5}' : key === 'receipt_board' ? '\u{1F4CB}' : key === 'archive_shelf' ? '\u{1F4DA}' : '\u{1F6A8}';
    ctx.fillText(`${icon} ${zone.role.toUpperCase()}`, sx + 8 * scale, sy + 6 * scale);
    ctx.globalAlpha = 1;

    if (key === 'archive_shelf') drawArchiveShelf(ctx, scale, zone);

    // Active zone data-flow effect (working agent)
    if (zone.agent) {
      const a = agents.get(zone.agent);
      if (a && a.state === 'working') {
        drawZoneDataFlow(ctx, scale, sx, sy, sw, sh, zone.color);
      }
    }

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

function pushArchiveShelfCube(cube) {
  archiveShelfCubes.push({
    id: `${cube.token}:${performance.now()}:${Math.random().toString(36).slice(2, 7)}`,
    tint: cube.tint || '#7dd3fc',
    bornAt: performance.now(),
    fadeStartAt: null,
  });
  const visible = archiveShelfCubes.filter(item => item.fadeStartAt == null);
  while (visible.length > ARCHIVE_VISIBLE_LIMIT) {
    const oldest = archiveShelfCubes.find(item => item.fadeStartAt == null);
    if (!oldest) break;
    oldest.fadeStartAt = performance.now();
    visible.shift();
  }
}

function syncArchiveShelfState() {
  const landed = _lowMotion ? completeArchiveFlightsImmediately() : drainArchiveCubeLandings();
  for (const cube of landed) pushArchiveShelfCube(cube);
  const now = performance.now();
  for (let i = archiveShelfCubes.length - 1; i >= 0; i--) {
    const cube = archiveShelfCubes[i];
    if (cube.fadeStartAt == null) continue;
    if (now - cube.fadeStartAt >= ARCHIVE_FADE_MS) archiveShelfCubes.splice(i, 1);
  }
}

function archiveShelfLayout(index) {
  const rows = [4, 3, 2, 1];
  let cursor = 0;
  for (let level = 0; level < rows.length; level++) {
    const count = rows[level];
    if (index < cursor + count) {
      return { level, slot: index - cursor, count };
    }
    cursor += count;
  }
  return { level: rows.length - 1, slot: 0, count: 1 };
}

function drawArchiveShelf(ctx, scale, zone) {
  const now = performance.now();
  const baseX = zone.x + zone.w * 0.5;
  const baseY = zone.y + zone.h * 0.84;

  ctx.save();
  ctx.fillStyle = 'rgba(129,140,248,0.08)';
  ctx.beginPath();
  ctx.ellipse(baseX * scale, baseY * scale, 88 * scale, 26 * scale, 0, 0, Math.PI * 2);
  ctx.fill();

  const positioned = archiveShelfCubes.map((cube, index) => ({ cube, layout: archiveShelfLayout(index) }));
  positioned.sort((a, b) => {
    if (a.layout.level !== b.layout.level) return b.layout.level - a.layout.level;
    return a.layout.slot - b.layout.slot;
  });

  for (const { cube, layout } of positioned) {
    const fadeAlpha = cube.fadeStartAt == null ? 1 : Math.max(0, 1 - (now - cube.fadeStartAt) / ARCHIVE_FADE_MS);
    const dx = (layout.slot - (layout.count - 1) / 2) * 22;
    const dy = layout.level * 19 + Math.abs(layout.slot - (layout.count - 1) / 2) * 3;
    drawDataCube(ctx, scale, baseX + dx, baseY - dy, {
      size: 9.5,
      tint: cube.tint,
      alpha: 0.92 * fadeAlpha,
      glow: cube.fadeStartAt == null ? 0.15 : 0.05,
    });
  }
  ctx.restore();
}

function drawZoneDataFlow(ctx, scale, sx, sy, sw, sh, color) {
  const t = performance.now() / 1000;
  ctx.save();
  // Clip to zone rounded rect
  ctx.beginPath(); ctx.roundRect(sx, sy, sw, sh, 6 * scale); ctx.clip();

  // Matrix rain columns
  const colW = 12 * scale;
  const cols = Math.ceil(sw / colW);
  const chars = 'アイウエオカキクケコ01<>/{}[];=+-*';
  const fontSize = 5 * scale;
  ctx.font = `${fontSize}px monospace`;
  ctx.textAlign = 'center';
  for (let c = 0; c < cols; c++) {
    // Each column has its own speed/phase seeded by column index
    const seed = c * 7.3 + 0.5;
    const speed = 1.8 + (seed % 3);
    const cx = sx + c * colW + colW / 2;
    const offset = (t * speed * 20 * scale + seed * 40) % (sh + 60 * scale);
    const headY = sy + offset;
    const tailLen = 6;
    for (let i = 0; i < tailLen; i++) {
      const cy = headY - i * fontSize * 1.3;
      if (cy < sy - fontSize || cy > sy + sh + fontSize) continue;
      const brightness = i === 0 ? 1.0 : 0.2 + (1 - i / tailLen) * 0.4;
      const alpha = brightness * 0.18;
      if (i === 0) {
        ctx.fillStyle = `rgba(255,255,255,${alpha + 0.06})`;
      } else {
        // Parse zone color hex to approximate rgb for tinting
        ctx.fillStyle = color.startsWith('#34d') ? `rgba(52,211,153,${alpha})`
          : color.startsWith('#60a') ? `rgba(96,165,250,${alpha})`
          : color.startsWith('#fbb') ? `rgba(251,191,36,${alpha})`
          : `rgba(52,211,153,${alpha})`;
      }
      const charIdx = Math.floor((seed * 13 + i * 7 + t * 3) % chars.length);
      ctx.fillText(chars[charIdx], cx, cy);
    }
  }

  // Iso grid glow (scrolling bright diamonds on floor)
  const gridStep = 28 * scale;
  const scrollY = (t * 18 * scale) % gridStep;
  ctx.strokeStyle = color.startsWith('#34d') ? 'rgba(52,211,153,0.06)'
    : color.startsWith('#60a') ? 'rgba(96,165,250,0.06)'
    : color.startsWith('#fbb') ? 'rgba(251,191,36,0.06)'
    : 'rgba(52,211,153,0.06)';
  ctx.lineWidth = 0.5;
  for (let gx = sx - gridStep; gx < sx + sw + gridStep; gx += gridStep) {
    for (let gy = sy - gridStep + scrollY; gy < sy + sh + gridStep; gy += gridStep) {
      ctx.beginPath();
      ctx.moveTo(gx, gy + gridStep / 2);
      ctx.lineTo(gx + gridStep / 2, gy);
      ctx.lineTo(gx + gridStep, gy + gridStep / 2);
      ctx.lineTo(gx + gridStep / 2, gy + gridStep);
      ctx.closePath();
      ctx.stroke();
    }
  }

  ctx.restore();
}

function drawDeskFurniture(ctx, scale, zone) {
  const cx = (zone.x + zone.w / 2) * scale;
  const cy = (zone.y + zone.h * 0.65) * scale;
  const dw = 40 * scale, dh = 25 * scale;
  const a = agents.get(zone.agent);
  const isWorking = a && a.state === 'working';
  const pulse = isWorking ? 0.12 + Math.sin(performance.now() / 400) * 0.06 : 0;

  // Top face
  ctx.beginPath();
  ctx.moveTo(cx, cy - dh / 2); ctx.lineTo(cx + dw / 2, cy - dh / 4);
  ctx.lineTo(cx, cy); ctx.lineTo(cx - dw / 2, cy - dh / 4); ctx.closePath();
  if (isWorking) { ctx.fillStyle = zone.color; ctx.globalAlpha = pulse + 0.04; ctx.fill(); }
  ctx.strokeStyle = zone.color; ctx.lineWidth = 1 * scale;
  ctx.globalAlpha = isWorking ? 0.5 : 0.3; ctx.stroke();

  // Left side
  ctx.beginPath();
  ctx.moveTo(cx - dw / 2, cy - dh / 4); ctx.lineTo(cx - dw / 2, cy + dh / 4);
  ctx.lineTo(cx, cy + dh / 2); ctx.lineTo(cx, cy); ctx.closePath();
  if (isWorking) { ctx.fillStyle = zone.color; ctx.globalAlpha = pulse * 0.7; ctx.fill(); }
  ctx.globalAlpha = isWorking ? 0.5 : 0.3; ctx.stroke();

  // Right side
  ctx.beginPath();
  ctx.moveTo(cx + dw / 2, cy - dh / 4); ctx.lineTo(cx + dw / 2, cy + dh / 4);
  ctx.lineTo(cx, cy + dh / 2); ctx.lineTo(cx, cy); ctx.closePath();
  if (isWorking) { ctx.fillStyle = zone.color; ctx.globalAlpha = pulse * 0.5; ctx.fill(); }
  ctx.globalAlpha = isWorking ? 0.5 : 0.3; ctx.stroke();

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

// ── Watcher Radar ──
let _radarAngle = 0;
const _radarGlow = new Map();       // agentName → { timer, color }
let _radarBrokenCooldown = 0;       // prevent SoundFX spam

function drawRadar(ctx, scale, dt) {
  const iz = ZONE_MAP.incident_zone;
  if (!iz) return;
  const cx = (iz.x + iz.w / 2) * scale;
  const cy = (iz.y + iz.h / 2) * scale;
  const radius = 180 * scale;

  _radarAngle += dt * 1.2;  // ~1.2 rad/s → full rotation ~5.2s
  if (_radarBrokenCooldown > 0) _radarBrokenCooldown -= dt;

  // Sweep detection: check each agent
  for (const a of agents.values()) {
    const ax = a.x * scale, ay = a.y * scale;
    const dx = ax - cx, dy = ay - cy;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > radius) continue;

    const agentAngle = Math.atan2(dy, dx);
    // Normalize both angles to [0, 2π]
    const normRadar = ((_radarAngle % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
    const normAgent = ((agentAngle % (Math.PI * 2)) + Math.PI * 2) % (Math.PI * 2);
    const diff = Math.abs(normRadar - normAgent);
    const angleDist = Math.min(diff, Math.PI * 2 - diff);

    // Sweep width ~0.15 rad
    if (angleDist < 0.15) {
      if (a.state === 'working') {
        _radarGlow.set(a.name, { timer: 0.5, color: 'rgba(255,255,255,0.6)' });
      } else if (a.state === 'broken') {
        _radarGlow.set(a.name, { timer: 0.5, color: 'rgba(239,68,68,0.8)' });
        if (_radarBrokenCooldown <= 0) {
          SoundFX.warn();
          _radarBrokenCooldown = 5; // max once per 5s per full sweep
        }
      }
    }
  }

  // Decay glow timers
  for (const [name, g] of _radarGlow) {
    g.timer -= dt;
    if (g.timer <= 0) _radarGlow.delete(name);
  }

  ctx.save();

  // Radar circle outline
  ctx.strokeStyle = 'rgba(52,211,153,0.08)';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.stroke();

  // Crosshair
  ctx.strokeStyle = 'rgba(52,211,153,0.06)';
  ctx.beginPath(); ctx.moveTo(cx - radius, cy); ctx.lineTo(cx + radius, cy); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx, cy - radius); ctx.lineTo(cx, cy + radius); ctx.stroke();

  // Sweeping arc (gradient wedge)
  const sweepSpan = 0.5; // radians
  const grad = ctx.createConicGradient(_radarAngle - sweepSpan, cx, cy);
  grad.addColorStop(0, 'rgba(52,211,153,0)');
  grad.addColorStop(sweepSpan / (Math.PI * 2), 'rgba(52,211,153,0.18)');
  grad.addColorStop((sweepSpan + 0.01) / (Math.PI * 2), 'rgba(52,211,153,0)');
  grad.addColorStop(1, 'rgba(52,211,153,0)');
  ctx.fillStyle = grad;
  ctx.beginPath(); ctx.arc(cx, cy, radius, 0, Math.PI * 2); ctx.fill();

  // Sweep line
  const lx = cx + Math.cos(_radarAngle) * radius;
  const ly = cy + Math.sin(_radarAngle) * radius;
  ctx.strokeStyle = 'rgba(52,211,153,0.35)';
  ctx.lineWidth = 1.5;
  ctx.beginPath(); ctx.moveTo(cx, cy); ctx.lineTo(lx, ly); ctx.stroke();

  // Center dot
  ctx.fillStyle = 'rgba(52,211,153,0.5)';
  ctx.beginPath(); ctx.arc(cx, cy, 3 * scale, 0, Math.PI * 2); ctx.fill();

  ctx.restore();
}

function drawRadarGlow(ctx, scale) {
  for (const [name, g] of _radarGlow) {
    const a = agents.get(name);
    if (!a) continue;
    const sx = a.x * scale, sy = a.y * scale;
    const alpha = Math.min(1, g.timer / 0.3);
    ctx.save();
    ctx.shadowColor = g.color;
    ctx.shadowBlur = 16 * scale;
    ctx.strokeStyle = g.color.replace(/[\d.]+\)$/, `${alpha})`);
    ctx.lineWidth = 2 * scale;
    ctx.beginPath(); ctx.arc(sx, sy, 18 * scale, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();
  }
}

// ── Office Party ──
let _partyTimer = 0;
let _partyPhase = 0;
const PARTY_DURATION = 5;
const MIRROR_BALL_COLORS = [
  'rgba(239,68,68,',   // red
  'rgba(96,165,250,',  // blue
  'rgba(52,211,153,',  // green
  'rgba(251,191,36,',  // amber
  'rgba(167,139,250,', // purple
  'rgba(236,72,153,',  // pink
];

function startParty() {
  _partyTimer = PARTY_DURATION;
  _partyPhase = 0;
  SoundFX.fanfare();
  for (const a of agents.values()) a.startParty(PARTY_DURATION);
}

function drawPartyOverlay(ctx, cw, ch, scale, dt) {
  if (_partyTimer <= 0) return;
  _partyTimer -= dt;
  _partyPhase += dt * 2.5;

  // Dim lights
  const dimAlpha = Math.min(0.35, (_partyTimer < 1 ? _partyTimer * 0.35 : 0.35));
  ctx.fillStyle = `rgba(0,0,0,${dimAlpha})`;
  ctx.fillRect(0, 0, cw, ch);

  // Mirror ball position: top center
  const ballX = (VIRTUAL_W / 2) * scale;
  const ballY = 30 * scale;
  const ballR = 12 * scale;

  // Mirror ball body
  ctx.save();
  ctx.fillStyle = 'rgba(200,210,230,0.7)';
  ctx.beginPath(); ctx.arc(ballX, ballY, ballR, 0, Math.PI * 2); ctx.fill();
  // Sparkle facets
  for (let i = 0; i < 8; i++) {
    const fa = (i / 8) * Math.PI * 2 + _partyPhase * 0.5;
    const fx = ballX + Math.cos(fa) * ballR * 0.65;
    const fy = ballY + Math.sin(fa) * ballR * 0.65;
    ctx.fillStyle = 'rgba(255,255,255,0.8)';
    ctx.beginPath(); ctx.arc(fx, fy, 1.5 * scale, 0, Math.PI * 2); ctx.fill();
  }
  // String
  ctx.strokeStyle = 'rgba(150,160,180,0.4)';
  ctx.lineWidth = 1;
  ctx.beginPath(); ctx.moveTo(ballX, 0); ctx.lineTo(ballX, ballY - ballR); ctx.stroke();
  ctx.restore();

  // Rotating color beams from mirror ball
  const beamCount = 6;
  for (let i = 0; i < beamCount; i++) {
    const angle = _partyPhase + (i / beamCount) * Math.PI * 2;
    const beamLen = 400 * scale;
    const endX = ballX + Math.cos(angle) * beamLen;
    const endY = ballY + Math.sin(angle) * beamLen;
    const colorBase = MIRROR_BALL_COLORS[i % MIRROR_BALL_COLORS.length];
    const fadeAlpha = _partyTimer < 1 ? _partyTimer * 0.12 : 0.12;

    // Beam triangle (narrow cone)
    ctx.save();
    ctx.beginPath();
    const spread = 0.08;
    ctx.moveTo(ballX, ballY);
    ctx.lineTo(ballX + Math.cos(angle - spread) * beamLen, ballY + Math.sin(angle - spread) * beamLen);
    ctx.lineTo(ballX + Math.cos(angle + spread) * beamLen, ballY + Math.sin(angle + spread) * beamLen);
    ctx.closePath();
    const grad = ctx.createRadialGradient(ballX, ballY, 0, ballX, ballY, beamLen);
    grad.addColorStop(0, colorBase + (fadeAlpha + 0.05) + ')');
    grad.addColorStop(0.6, colorBase + fadeAlpha + ')');
    grad.addColorStop(1, colorBase + '0)');
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.restore();

    // Floor spot (circle where beam hits)
    if (endY > 0 && endY < ch && endX > 0 && endX < cw) {
      ctx.save();
      ctx.fillStyle = colorBase + (fadeAlpha * 0.8) + ')';
      ctx.beginPath(); ctx.ellipse(endX, endY, 20 * scale, 8 * scale, 0, 0, Math.PI * 2); ctx.fill();
      ctx.restore();
    }
  }
}

// Wire roundComplete event
PipelineState.onChange((type) => {
  if (type === 'roundComplete' && !_lowMotion) startParty();
});

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
    for (let i = archiveCubeFlights.length - 1; i >= 0; i--) { archiveCubeFlights[i].update(dt); if (!archiveCubeFlights[i].alive) archiveCubeFlights.splice(i, 1); }
    for (let i = drones.length - 1; i >= 0; i--) { drones[i].update(dt); if (!drones[i].alive) drones.splice(i, 1); }
  }
  syncArchiveShelfState();
  AmbientAudio.update(workingCount);

  // Render
  ctx.clearRect(0, 0, cw, ch);
  drawIsometricGrid(ctx, scale);
  drawZones(ctx, scale);

  // Radar (under agents, over zones)
  if (!_lowMotion) drawRadar(ctx, scale, dt);

  // Agents sorted by Y
  const sorted = [...agents.values()].sort((a, b) => a.y - b.y);
  for (const a of sorted) a.draw(ctx, scale);

  // Radar glow on agents (over agent sprites)
  if (!_lowMotion) drawRadarGlow(ctx, scale);

  if (!_lowMotion) {
    for (const d of deliveryPackets) d.draw(ctx, scale);
    for (const cube of archiveCubeFlights) cube.draw(ctx, scale);
    for (const dr of drones) dr.draw(ctx, scale);
    for (const p of particles) p.draw(ctx, scale);
  }

  // Party overlay (topmost visual, under broken glow)
  if (!_lowMotion) drawPartyOverlay(ctx, cw, ch, scale, dt);

  drawBrokenGlow(ctx, cw, ch, severity);
}

export function startRenderLoop() {
  window.addEventListener('resize', resize);
  resize();
  requestAnimationFrame(loop);
}
