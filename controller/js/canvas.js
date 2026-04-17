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
