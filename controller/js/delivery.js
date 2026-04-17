// controller/js/delivery.js — Agent walk delivery + packet animation + drone
import { agents, spawnParticle, Particle, particles } from './agents.js';
import { SoundFX } from './audio.js';
import { ZONE_MAP, VIRTUAL_W } from './config.js';
import { PipelineState } from './state.js';

export const deliveryPackets = [];
export const drones = [];
export const archiveCubeFlights = [];
export const circuitPulses = [];
export const receiptPaperQueue = [];

const archiveCubeLandings = [];
const archiveFlightTokens = new Map();

export const CIRCUIT_ROUTE_IDS = {
  implementVerify: 'implement_verify',
  verifyAdvisory: 'verify_advisory',
  implementReceipt: 'implement_receipt',
  verifyArchive: 'verify_archive',
  advisoryIncident: 'advisory_incident',
  receiptArchive: 'receipt_archive',
  archiveIncident: 'archive_incident',
};

function basename(p) { return String(p || '').split('/').filter(Boolean).pop() || '\u2014'; }

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

function formatReceiptTime(raw) {
  const value = raw ? new Date(raw) : new Date();
  const ts = Number.isNaN(value.getTime()) ? new Date() : value;
  return ts.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function hexToRgb(hex, fallback = [129, 140, 248]) {
  const raw = String(hex || '').trim().replace('#', '');
  if (raw.length !== 6) return fallback;
  const value = Number.parseInt(raw, 16);
  if (!Number.isFinite(value)) return fallback;
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function rgba(rgb, alpha) {
  return `rgba(${rgb[0]},${rgb[1]},${rgb[2]},${clamp(alpha, 0, 1)})`;
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - clamp(t, 0, 1), 3);
}

function queueCircuitPulse(routeId, options = {}) {
  circuitPulses.push({
    routeId,
    reverse: Boolean(options.reverse),
    color: options.color || '#60a5fa',
    progress: 0,
    speed: options.speed || 1.9,
    trail: options.trail || 0.24,
    alive: true,
  });
}

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

export function drawDataCube(ctx, scale, x, y, options = {}) {
  const alpha = clamp(options.alpha ?? 1, 0, 1);
  if (alpha <= 0) return;
  const size = (options.size ?? 12) * scale;
  const rgb = hexToRgb(options.tint || '#7dd3fc');
  const top = { x: x * scale, y: y * scale - size * 0.7 };
  const right = { x: top.x + size, y: top.y + size * 0.45 };
  const bottom = { x: top.x, y: top.y + size * 0.9 };
  const left = { x: top.x - size, y: top.y + size * 0.45 };
  const drop = size * 0.95;
  const bottomDrop = { x: bottom.x, y: bottom.y + drop };
  const leftDrop = { x: left.x, y: left.y + drop };
  const rightDrop = { x: right.x, y: right.y + drop };

  ctx.save();
  if ((options.glow ?? 0) > 0) {
    ctx.shadowBlur = size * (1.1 + options.glow * 2.2);
    ctx.shadowColor = rgba(rgb, 0.45 * alpha);
  }

  ctx.fillStyle = rgba(rgb, 0.92 * alpha);
  ctx.beginPath();
  ctx.moveTo(top.x, top.y);
  ctx.lineTo(right.x, right.y);
  ctx.lineTo(bottom.x, bottom.y);
  ctx.lineTo(left.x, left.y);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = rgba(rgb.map(v => Math.round(v * 0.7)), 0.92 * alpha);
  ctx.beginPath();
  ctx.moveTo(left.x, left.y);
  ctx.lineTo(bottom.x, bottom.y);
  ctx.lineTo(bottomDrop.x, bottomDrop.y);
  ctx.lineTo(leftDrop.x, leftDrop.y);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = rgba(rgb.map(v => Math.round(Math.min(255, v * 0.88 + 10))), 0.92 * alpha);
  ctx.beginPath();
  ctx.moveTo(right.x, right.y);
  ctx.lineTo(bottom.x, bottom.y);
  ctx.lineTo(bottomDrop.x, bottomDrop.y);
  ctx.lineTo(rightDrop.x, rightDrop.y);
  ctx.closePath();
  ctx.fill();

  ctx.strokeStyle = rgba([255, 255, 255], 0.45 * alpha);
  ctx.lineWidth = Math.max(1, scale * 0.8);
  ctx.beginPath();
  ctx.moveTo(top.x, top.y);
  ctx.lineTo(right.x, right.y);
  ctx.lineTo(bottom.x, bottom.y);
  ctx.lineTo(left.x, left.y);
  ctx.closePath();
  ctx.stroke();

  ctx.strokeStyle = rgba(rgb.map(v => Math.round(v * 0.55)), 0.5 * alpha);
  ctx.beginPath();
  ctx.moveTo(left.x, left.y);
  ctx.lineTo(leftDrop.x, leftDrop.y);
  ctx.moveTo(bottom.x, bottom.y);
  ctx.lineTo(bottomDrop.x, bottomDrop.y);
  ctx.moveTo(right.x, right.y);
  ctx.lineTo(rightDrop.x, rightDrop.y);
  ctx.stroke();

  ctx.fillStyle = rgba([255, 255, 255], 0.28 * alpha);
  ctx.beginPath();
  ctx.moveTo(top.x, top.y + size * 0.12);
  ctx.lineTo(top.x + size * 0.32, top.y + size * 0.28);
  ctx.lineTo(top.x, top.y + size * 0.45);
  ctx.lineTo(top.x - size * 0.32, top.y + size * 0.28);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

class ArchiveCubeFlight {
  constructor({ token, reason, fromZone = 'codex_desk', toZone = 'archive_shelf', tint = '#7dd3fc' }) {
    const src = zoneCenter(fromZone);
    const dst = archiveLandingPoint(toZone);
    this.token = token;
    this.reason = reason;
    this.tint = tint;
    this.sx = src.x;
    this.sy = src.y - 18;
    this.tx = dst.x;
    this.ty = dst.y;
    this.x = this.sx;
    this.y = this.sy;
    this.duration = 1.35 + Math.random() * 0.2;
    this.elapsed = 0;
    this.arcHeight = 78 + Math.random() * 18;
    this.wobble = (Math.random() - 0.5) * 18;
    this.size = 11 + Math.random() * 2;
    this.alive = true;
    this._landed = false;
  }

  update(dt) {
    if (!this.alive) return;
    this.elapsed += dt;
    const raw = clamp(this.elapsed / this.duration, 0, 1);
    const t = easeOutCubic(raw);
    this.x = this.sx + (this.tx - this.sx) * t;
    this.y = this.sy + (this.ty - this.sy) * t - Math.sin(raw * Math.PI) * this.arcHeight + Math.sin(raw * Math.PI * 2) * this.wobble * 0.15;
    if (raw >= 1) {
      this.alive = false;
      if (!this._landed) {
        this._landed = true;
        archiveCubeLandings.push({ token: this.token, reason: this.reason, tint: this.tint });
        SoundFX.blip();
      }
    }
  }

  draw(ctx, scale) {
    const raw = clamp(this.elapsed / this.duration, 0, 1);
    const glow = 0.75 - raw * 0.25;
    const alpha = 0.95 - raw * 0.1;
    const shadowScale = 0.55 + raw * 0.2;
    ctx.save();
    ctx.fillStyle = 'rgba(125,211,252,0.16)';
    ctx.beginPath();
    ctx.ellipse(this.x * scale, (this.ty + 12) * scale, this.size * scale * shadowScale, this.size * scale * 0.32, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
    drawDataCube(ctx, scale, this.x, this.y, { size: this.size, tint: this.tint, alpha, glow });
  }
}

// ── Drone ──
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

function archiveLandingPoint(zoneKey) {
  const z = ZONE_MAP[zoneKey];
  return z ? { x: z.x + z.w * 0.5, y: z.y + z.h * 0.8 } : zoneCenter(zoneKey);
}

function agentZoneKey(name) { return `${name.toLowerCase()}_desk`; }

function pruneArchiveTokens(now) {
  for (const [token, seenAt] of archiveFlightTokens.entries()) {
    if (now - seenAt > 6000) archiveFlightTokens.delete(token);
  }
}

function buildArchiveToken() {
  const data = PipelineState.data || {};
  const controlSeq = (data.control || {}).active_control_seq ?? -1;
  const verifyPath = basename(((data.artifacts || {}).latest_verify || {}).path || '');
  return `${controlSeq}:${verifyPath || 'archive'}`;
}

function buildReceiptPaper(receiptId) {
  const data = PipelineState.data || {};
  const receipt = data.last_receipt || {};
  const result = String(receipt.verify_result || receipt.result || receipt.status || 'pending').trim() || 'pending';
  const receiptTime = formatReceiptTime(
    receipt.closed_at || receipt.created_at || receipt.updated_at || receipt.receipt_written_at || Date.now()
  );
  const verifyBase = basename(((data.artifacts || {}).latest_verify || {}).path || '');
  const normalizedId = String(receiptId || receipt.receipt_id || '\u2014').trim() || '\u2014';
  return {
    id: normalizedId,
    result,
    timeLabel: receiptTime,
    source: verifyBase,
    issuedAt: performance.now(),
    lines: [
      `ID     ${normalizedId}`,
      `RESULT ${result.toUpperCase()}`,
      `TIME   ${receiptTime}`,
      `SRC    ${verifyBase}`,
    ],
  };
}

function queueArchiveCube(reason) {
  const token = buildArchiveToken();
  if (!token || token.endsWith(':')) return;
  const now = performance.now();
  pruneArchiveTokens(now);
  if (archiveFlightTokens.has(token)) return;
  archiveFlightTokens.set(token, now);
  archiveCubeFlights.push(new ArchiveCubeFlight({
    token,
    reason,
    fromZone: 'codex_desk',
    toZone: 'archive_shelf',
    tint: reason === 'receipt' ? '#a78bfa' : '#7dd3fc',
  }));
}

function queueReceiptPaper(receiptId) {
  receiptPaperQueue.push(buildReceiptPaper(receiptId));
}

export function drainArchiveCubeLandings() {
  return archiveCubeLandings.splice(0);
}

export function drainReceiptPaperQueue() {
  return receiptPaperQueue.splice(0);
}

export function completeArchiveFlightsImmediately() {
  const landed = [];
  while (archiveCubeFlights.length) {
    const flight = archiveCubeFlights.shift();
    if (!flight) continue;
    landed.push({ token: flight.token, reason: flight.reason, tint: flight.tint });
  }
  return landed;
}

// ── Delivery dispatcher ──
export function initDeliverySystem() {
  PipelineState.onChange((type, detail) => {
    if (type !== 'delivery') return;
    for (const trigger of detail) {
      switch (trigger.type) {
        case 'control': {
          const status = trigger.status;
          if (status === 'implement') {
            deliveryPackets.push(new DeliveryPacket('codex_desk', 'claude_desk', '\u{1F4CB}'));
            queueCircuitPulse(CIRCUIT_ROUTE_IDS.implementVerify, { reverse: true, color: '#60a5fa' });
            speakAgent('Claude', '\uBC1B\uC558\uC2B5\uB2C8\uB2E4', 2.5);
            PipelineState.pushEvent('info', `Implement handoff \u2192 Claude (seq ${trigger.seq})`);
          } else if (status === 'needs_operator') {
            const owner = agents.get('Claude');
            if (owner) { owner.walkToZone('incident_zone', '\u26A0\uFE0F'); }
            queueCircuitPulse(CIRCUIT_ROUTE_IDS.advisoryIncident, { color: '#ef4444' });
            PipelineState.pushEvent('warn', `Operator review requested (seq ${trigger.seq})`);
            SoundFX.warn();
          } else if (status === 'advice_ready') {
            const gemini = agents.get('Gemini');
            if (gemini) { gemini.walkToZone('codex_desk', '\u{1F4DD}'); }
            queueCircuitPulse(CIRCUIT_ROUTE_IDS.verifyAdvisory, { reverse: true, color: '#fbbf24' });
            PipelineState.pushEvent('info', `Advice ready \u2192 Codex`);
          } else {
            deliveryPackets.push(new DeliveryPacket('claude_desk', 'codex_desk', '\u{1F4E6}'));
            queueCircuitPulse(CIRCUIT_ROUTE_IDS.implementVerify, { color: '#34d399' });
            PipelineState.pushEvent('info', `Control changed \u2192 ${status || 'none'} (seq ${trigger.seq})`);
          }
          break;
        }
        case 'work': {
          const claude = agents.get('Claude');
          if (claude) { claude.walkToZone('archive_shelf', '\u{1F4C1}'); }
          queueCircuitPulse(CIRCUIT_ROUTE_IDS.implementVerify, { color: '#34d399' });
          PipelineState.pushEvent('ok', `Work delivered \u2192 ${basename(trigger.path)}`);
          SoundFX.success();
          break;
        }
        case 'verify': {
          const codex = agents.get('Codex');
          if (codex) { codex.walkToZone('archive_shelf', '\u2705'); }
          queueCircuitPulse(CIRCUIT_ROUTE_IDS.verifyArchive, { color: '#7dd3fc' });
          PipelineState.pushEvent('info', `Verify updated \u2192 ${basename(trigger.path)}`);
          break;
        }
        case 'receipt': {
          const codex2 = agents.get('Codex');
          if (codex2) { codex2.walkToZone('receipt_board', '\u{1F9FE}'); }
          PipelineState.pushEvent('ok', `Receipt issued \u2192 ${trigger.id}`);
          queueCircuitPulse(CIRCUIT_ROUTE_IDS.implementReceipt, { color: '#a78bfa' });
          queueCircuitPulse(CIRCUIT_ROUTE_IDS.receiptArchive, { color: '#a78bfa', reverse: false });
          queueReceiptPaper(trigger.id);
          queueArchiveCube('receipt');
          SoundFX.success();
          break;
        }
      }
    }
  });

  PipelineState.onChange((type, detail) => {
    if (type !== 'roundComplete') return;
    const nextState = String(detail?.to || '').toUpperCase();
    if (nextState === 'DONE' || nextState === 'CLOSED') {
      queueCircuitPulse(CIRCUIT_ROUTE_IDS.verifyArchive, { color: '#7dd3fc' });
      queueArchiveCube('round_complete');
    }
  });

  // Drone on lane state -> working
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
