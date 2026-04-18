// controller/js/canvas.js — Canvas render loop, isometric background, zone boundaries
import { ZONE_MAP, CORRIDOR_Y, VIRTUAL_W, VIRTUAL_H, SEVERITY_MAP, INACTIVE_RUNTIME_STATES } from './config.js';
import { PipelineState } from './state.js';
import { agents, particles, setAgentLowMotion } from './agents.js';
import {
  CIRCUIT_ROUTE_IDS,
  archiveCubeFlights,
  circuitPulses,
  completeArchiveFlightsImmediately,
  deliveryPackets,
  drainArchiveCubeLandings,
  drainReceiptPaperQueue,
  drawDataCube,
  drones,
} from './delivery.js';
import { AmbientAudio, SoundFX } from './audio.js';

let _lowMotion = false;
export function isLowMotion() { return _lowMotion; }
export function setLowMotion(v) {
  _lowMotion = v;
  setAgentLowMotion(v);
  if (v) {
    particles.length = 0;
    deliveryPackets.length = 0;
    drones.length = 0;
    circuitPulses.length = 0;
  }
}

const archiveShelfCubes = [];
const ARCHIVE_VISIBLE_LIMIT = 10;
const ARCHIVE_FADE_MS = 1400;
const receiptPrinterPapers = [];
const RECEIPT_VISIBLE_LIMIT = 5;
const RECEIPT_FADE_MS = 1600;
const RECEIPT_PRINT_MS = 820;
const RECEIPT_TYPE_MS = 950;

const glitchCanvas = document.createElement('canvas');
const glitchCtx = glitchCanvas.getContext('2d', { willReadFrequently: true });
const redTintCanvas = document.createElement('canvas');
const redTintCtx = redTintCanvas.getContext('2d');
const blueTintCanvas = document.createElement('canvas');
const blueTintCtx = blueTintCanvas.getContext('2d');

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

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function easeOutCubic(t) {
  const value = clamp(t, 0, 1);
  return 1 - Math.pow(1 - value, 3);
}

function heartbeatPulse(ms, speed = 1) {
  const t = ((ms / 1000) * speed) % 1;
  const beatA = Math.exp(-Math.pow((t - 0.14) / 0.05, 2));
  const beatB = 0.65 * Math.exp(-Math.pow((t - 0.32) / 0.04, 2));
  return clamp(beatA + beatB, 0, 1);
}

function zoneAnchor(zoneKey, side, ratio = 0.5) {
  const zone = ZONE_MAP[zoneKey];
  if (!zone) return { x: 0, y: 0 };
  if (side === 'left') return { x: zone.x + 10, y: zone.y + zone.h * ratio };
  if (side === 'right') return { x: zone.x + zone.w - 10, y: zone.y + zone.h * ratio };
  if (side === 'top') return { x: zone.x + zone.w * ratio, y: zone.y + 10 };
  return { x: zone.x + zone.w * ratio, y: zone.y + zone.h - 10 };
}

function buildCircuitRoutes() {
  const claudeRight = zoneAnchor('claude_desk', 'right', 0.46);
  const codexLeft = zoneAnchor('codex_desk', 'left', 0.46);
  const codexRight = zoneAnchor('codex_desk', 'right', 0.46);
  const geminiLeft = zoneAnchor('gemini_desk', 'left', 0.46);
  const claudeBottom = zoneAnchor('claude_desk', 'bottom', 0.56);
  const codexBottom = zoneAnchor('codex_desk', 'bottom', 0.55);
  const geminiBottom = zoneAnchor('gemini_desk', 'bottom', 0.55);
  const receiptTop = zoneAnchor('receipt_board', 'top', 0.48);
  const archiveTop = zoneAnchor('archive_shelf', 'top', 0.48);
  const receiptRight = zoneAnchor('receipt_board', 'right', 0.58);
  const archiveLeft = zoneAnchor('archive_shelf', 'left', 0.58);
  const archiveRight = zoneAnchor('archive_shelf', 'right', 0.58);
  const incidentTop = zoneAnchor('incident_zone', 'top', 0.5);
  const incidentLeft = zoneAnchor('incident_zone', 'left', 0.58);

  return {
    [CIRCUIT_ROUTE_IDS.implementVerify]: [
      claudeRight,
      { x: claudeRight.x + 18, y: claudeRight.y },
      { x: claudeRight.x + 18, y: 124 },
      { x: codexLeft.x - 18, y: 124 },
      { x: codexLeft.x - 18, y: codexLeft.y },
      codexLeft,
    ],
    [CIRCUIT_ROUTE_IDS.verifyAdvisory]: [
      codexRight,
      { x: codexRight.x + 16, y: codexRight.y },
      { x: codexRight.x + 16, y: 124 },
      { x: geminiLeft.x - 16, y: 124 },
      { x: geminiLeft.x - 16, y: geminiLeft.y },
      geminiLeft,
    ],
    [CIRCUIT_ROUTE_IDS.implementReceipt]: [
      codexBottom,
      { x: codexBottom.x, y: 320 },
      { x: receiptTop.x, y: 320 },
      receiptTop,
    ],
    [CIRCUIT_ROUTE_IDS.verifyArchive]: [
      codexBottom,
      { x: codexBottom.x, y: 320 },
      { x: archiveTop.x, y: 320 },
      archiveTop,
    ],
    [CIRCUIT_ROUTE_IDS.advisoryIncident]: [
      geminiBottom,
      { x: geminiBottom.x, y: 320 },
      { x: incidentTop.x, y: 320 },
      incidentTop,
    ],
    [CIRCUIT_ROUTE_IDS.receiptArchive]: [
      receiptRight,
      { x: receiptRight.x + 18, y: receiptRight.y },
      { x: receiptRight.x + 18, y: archiveLeft.y },
      { x: archiveLeft.x - 18, y: archiveLeft.y },
      archiveLeft,
    ],
    [CIRCUIT_ROUTE_IDS.archiveIncident]: [
      archiveRight,
      { x: archiveRight.x + 18, y: archiveRight.y },
      { x: archiveRight.x + 18, y: incidentLeft.y },
      incidentLeft,
    ],
  };
}

function routeMetrics(points) {
  const segments = [];
  let total = 0;
  for (let i = 0; i < points.length - 1; i++) {
    const a = points[i];
    const b = points[i + 1];
    const length = Math.hypot(b.x - a.x, b.y - a.y);
    if (length <= 0) continue;
    segments.push({ a, b, length, start: total, end: total + length });
    total += length;
  }
  return { points, segments, total };
}

function sampleRoutePoint(route, t) {
  const safeT = clamp(t, 0, 1);
  const distance = route.total * safeT;
  for (const seg of route.segments) {
    if (distance <= seg.end) {
      const local = clamp((distance - seg.start) / seg.length, 0, 1);
      return {
        x: seg.a.x + (seg.b.x - seg.a.x) * local,
        y: seg.a.y + (seg.b.y - seg.a.y) * local,
      };
    }
  }
  const last = route.points[route.points.length - 1];
  return { x: last.x, y: last.y };
}

function ensureFxBuffers() {
  if (glitchCanvas.width === canvas.width && glitchCanvas.height === canvas.height) return;
  for (const target of [glitchCanvas, redTintCanvas, blueTintCanvas]) {
    target.width = canvas.width;
    target.height = canvas.height;
  }
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

function drawCircuitLines(ctx, scale) {
  const routes = Object.values(buildCircuitRoutes());
  ctx.save();
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.shadowBlur = 8 * scale;
  ctx.shadowColor = 'rgba(96,165,250,0.08)';
  for (const points of routes) {
    ctx.beginPath();
    ctx.moveTo(points[0].x * scale, points[0].y * scale);
    for (let i = 1; i < points.length; i++) ctx.lineTo(points[i].x * scale, points[i].y * scale);
    ctx.strokeStyle = 'rgba(96,165,250,0.08)';
    ctx.lineWidth = 1.5 * scale;
    ctx.stroke();

    for (const point of points) {
      ctx.fillStyle = 'rgba(125,211,252,0.14)';
      ctx.beginPath();
      ctx.arc(point.x * scale, point.y * scale, 1.6 * scale, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  ctx.restore();
}

function drawCircuitPulses(ctx, scale) {
  const routeMap = Object.fromEntries(Object.entries(buildCircuitRoutes()).map(([id, points]) => [id, routeMetrics(points)]));
  for (const pulse of circuitPulses) {
    const route = routeMap[pulse.routeId];
    if (!route) continue;
    const head = pulse.progress;
    const tail = pulse.progress - pulse.trail;
    const start = clamp(tail, 0, 1);
    const end = clamp(head, 0, 1);
    if (end <= 0 || end <= start) continue;

    ctx.save();
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.shadowBlur = 14 * scale;
    ctx.shadowColor = pulse.color;
    const steps = 10;
    for (let i = 0; i < steps; i++) {
      const u1 = start + ((end - start) * i) / steps;
      const u2 = start + ((end - start) * (i + 1)) / steps;
      const t1 = pulse.reverse ? 1 - u1 : u1;
      const t2 = pulse.reverse ? 1 - u2 : u2;
      const p1 = sampleRoutePoint(route, t1);
      const p2 = sampleRoutePoint(route, t2);
      const alpha = 0.08 + ((i + 1) / steps) * 0.55;
      ctx.strokeStyle = pulse.color;
      ctx.globalAlpha = alpha;
      ctx.lineWidth = (1.4 + ((i + 1) / steps) * 2.1) * scale;
      ctx.beginPath();
      ctx.moveTo(p1.x * scale, p1.y * scale);
      ctx.lineTo(p2.x * scale, p2.y * scale);
      ctx.stroke();
    }
    const headPoint = sampleRoutePoint(route, pulse.reverse ? 1 - end : end);
    ctx.globalAlpha = 0.95;
    ctx.fillStyle = pulse.color;
    ctx.beginPath();
    ctx.arc(headPoint.x * scale, headPoint.y * scale, 2.6 * scale, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

function drawZones(ctx, scale) {
  const rd = PipelineState.data || {};
  const severity = getSeverity(rd);

  for (const [key, zone] of Object.entries(ZONE_MAP)) {
    const sx = zone.x * scale, sy = zone.y * scale;
    const sw = zone.w * scale, sh = zone.h * scale;
    const agent = zone.agent ? agents.get(zone.agent) : null;
    const isBottleneck = Boolean(agent && typeof agent.isBottleneck === 'function' && agent.isBottleneck());

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
      if (isBottleneck) {
        const beat = heartbeatPulse(performance.now(), 1.9);
        ctx.strokeStyle = 'rgba(249, 115, 22, 1)';
        ctx.globalAlpha = 0.45 + beat * 0.5;
        ctx.shadowBlur = 18 * scale;
        ctx.shadowColor = `rgba(249,115,22,${0.22 + beat * 0.28})`;
      } else {
        ctx.strokeStyle = zone.color;
        ctx.globalAlpha = 0.25;
        ctx.shadowBlur = 0;
      }
    }
    ctx.lineWidth = (isBottleneck ? 2.6 : 1.5) * scale;
    ctx.beginPath(); ctx.roundRect(sx, sy, sw, sh, 6 * scale); ctx.stroke();
    ctx.globalAlpha = 1; ctx.setLineDash([]);
    ctx.shadowBlur = 0;

    // Zone label
    ctx.font = `bold ${8 * scale}px 'Noto Sans KR', sans-serif`;
    ctx.fillStyle = isBottleneck ? 'rgba(249,115,22,1)' : zone.color;
    ctx.globalAlpha = 0.6;
    ctx.textAlign = 'left'; ctx.textBaseline = 'top';
    const icon = key.includes('desk') ? '\u{1F5A5}' : key === 'receipt_board' ? '\u{1F4CB}' : key === 'archive_shelf' ? '\u{1F4DA}' : '\u{1F6A8}';
    ctx.fillText(`${icon} ${zone.role.toUpperCase()}`, sx + 8 * scale, sy + 6 * scale);
    ctx.globalAlpha = 1;

    if (key === 'archive_shelf') drawArchiveShelf(ctx, scale, zone);
    if (key === 'receipt_board') drawReceiptPrinter(ctx, scale, zone);

    // Active zone data-flow effect (working agent)
    if (agent && agent.state === 'working') {
      drawZoneDataFlow(ctx, scale, sx, sy, sw, sh, isBottleneck ? '#f97316' : zone.color);
      if (isBottleneck) {
        ctx.save();
        ctx.strokeStyle = 'rgba(249,115,22,0.32)';
        ctx.lineWidth = 1.2 * scale;
        ctx.setLineDash([8 * scale, 5 * scale]);
        ctx.beginPath();
        ctx.roundRect(sx + 8 * scale, sy + 8 * scale, sw - 16 * scale, sh - 16 * scale, 8 * scale);
        ctx.stroke();
        ctx.restore();
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

function syncReceiptPrinterState() {
  const now = performance.now();
  const issued = drainReceiptPaperQueue();
  for (const paper of issued) {
    receiptPrinterPapers.unshift({
      ...paper,
      bornAt: now,
      fadeStartAt: null,
    });
  }
  const visible = receiptPrinterPapers.filter(item => item.fadeStartAt == null);
  while (visible.length > RECEIPT_VISIBLE_LIMIT) {
    const oldest = [...receiptPrinterPapers].reverse().find(item => item.fadeStartAt == null && item !== receiptPrinterPapers[0]);
    if (!oldest) break;
    oldest.fadeStartAt = now;
    visible.shift();
  }
  for (let i = receiptPrinterPapers.length - 1; i >= 0; i--) {
    const paper = receiptPrinterPapers[i];
    if (paper.fadeStartAt == null) continue;
    if (now - paper.fadeStartAt >= RECEIPT_FADE_MS) receiptPrinterPapers.splice(i, 1);
  }
}

function drawReceiptLines(ctx, scale, lines, visibleChars, x, y, lineGap, maxWidth) {
  let remaining = visibleChars;
  let row = 0;
  ctx.save();
  ctx.font = `${7.2 * scale}px monospace`;
  ctx.textAlign = 'left';
  ctx.textBaseline = 'top';
  ctx.fillStyle = 'rgba(17,24,39,0.92)';
  for (const line of lines) {
    if (remaining <= 0) break;
    const text = line.slice(0, remaining);
    ctx.fillText(text, x, y + row * lineGap, maxWidth);
    remaining -= line.length;
    row += 1;
  }
  ctx.restore();
}

function drawReceiptPrinter(ctx, scale, zone) {
  const now = performance.now();
  const slitX = zone.x + zone.w * 0.5;
  const slitY = zone.y + 30;
  const paperW = 92;
  const paperH = 78;
  const lineGap = 11 * scale;

  ctx.save();
  ctx.fillStyle = 'rgba(12,18,32,0.85)';
  ctx.beginPath();
  ctx.roundRect(zone.x * scale + 18 * scale, zone.y * scale + 12 * scale, zone.w * scale - 36 * scale, 24 * scale, 8 * scale);
  ctx.fill();
  ctx.fillStyle = 'rgba(88,28,135,0.95)';
  ctx.beginPath();
  ctx.roundRect((slitX - 52) * scale, (slitY - 4) * scale, 104 * scale, 8 * scale, 4 * scale);
  ctx.fill();
  ctx.fillStyle = 'rgba(226,232,240,0.16)';
  ctx.fillRect((slitX - 40) * scale, (slitY - 1) * scale, 80 * scale, 2 * scale);
  ctx.restore();

  const sorted = [...receiptPrinterPapers].sort((a, b) => a.bornAt - b.bornAt);
  sorted.forEach((paper, index) => {
    const age = now - paper.bornAt;
    const newest = paper === receiptPrinterPapers[0];
    const isPrinting = newest && paper.fadeStartAt == null;
    const printProgress = _lowMotion ? 1 : easeOutCubic(age / RECEIPT_PRINT_MS);
    const typedProgress = _lowMotion ? 1 : clamp((age - RECEIPT_PRINT_MS * 0.55) / RECEIPT_TYPE_MS, 0, 1);
    const visibleChars = Math.floor((paper.lines.join('').length + paper.lines.length) * typedProgress);
    const fadeAlpha = paper.fadeStartAt == null ? 1 : Math.max(0, 1 - (now - paper.fadeStartAt) / RECEIPT_FADE_MS);

    let drawX = slitX - paperW / 2;
    let drawY = slitY + 3;
    let drawH = 18 + (paperH - 18) * printProgress;
    let angle = 0;

    if (!isPrinting) {
      const stackIndex = Math.max(0, receiptPrinterPapers.indexOf(paper) - 1);
      drawX = zone.x + 74 + stackIndex * 8;
      drawY = zone.y + zone.h * 0.6 + stackIndex * 5;
      drawH = paperH;
      angle = (-0.06 + stackIndex * 0.025);
    }

    ctx.save();
    ctx.translate((drawX + paperW / 2) * scale, (drawY + drawH / 2) * scale);
    ctx.rotate(angle);
    ctx.globalAlpha = 0.96 * fadeAlpha;
    ctx.fillStyle = 'rgba(0,0,0,0.2)';
    ctx.fillRect(-paperW * scale / 2 + 2, -drawH * scale / 2 + 2, paperW * scale, drawH * scale);
    ctx.fillStyle = 'rgba(255,255,255,0.97)';
    ctx.fillRect(-paperW * scale / 2, -drawH * scale / 2, paperW * scale, drawH * scale);
    ctx.strokeStyle = 'rgba(148,163,184,0.28)';
    ctx.lineWidth = 1;
    ctx.strokeRect(-paperW * scale / 2, -drawH * scale / 2, paperW * scale, drawH * scale);
    ctx.restore();

    const clippedHeight = drawH * scale - 12 * scale;
    ctx.save();
    ctx.beginPath();
    ctx.rect(drawX * scale, drawY * scale, paperW * scale, drawH * scale);
    ctx.clip();
    drawReceiptLines(
      ctx,
      scale,
      paper.lines,
      isPrinting ? visibleChars : paper.lines.join('').length + paper.lines.length,
      drawX * scale + 9 * scale,
      drawY * scale + 10 * scale,
      lineGap,
      paperW * scale - 18 * scale
    );
    if (isPrinting && printProgress < 1) {
      ctx.fillStyle = 'rgba(167,139,250,0.22)';
      ctx.fillRect(drawX * scale, (drawY + drawH - 6) * scale, paperW * scale, 6 * scale);
    }
    ctx.restore();
  });
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

function applyBrokenGlitch() {
  try {
    ensureFxBuffers();
    glitchCtx.clearRect(0, 0, glitchCanvas.width, glitchCanvas.height);
    glitchCtx.drawImage(canvas, 0, 0);

    const bandCount = 2 + Math.floor(Math.random() * 4);
    for (let i = 0; i < bandCount; i++) {
      const rowH = Math.max(1, Math.floor((3 + Math.random() * 7) * (window.devicePixelRatio || 1)));
      const rowY = Math.floor(Math.random() * Math.max(1, glitchCanvas.height - rowH));
      const image = glitchCtx.getImageData(0, rowY, glitchCanvas.width, rowH);
      const offset = (Math.random() < 0.5 ? -1 : 1) * Math.floor((5 + Math.random() * 5) * (window.devicePixelRatio || 1));
      glitchCtx.putImageData(image, offset, rowY);
    }

    for (const [targetCtx, tint] of [
      [redTintCtx, 'rgba(255,64,64,0.22)'],
      [blueTintCtx, 'rgba(96,165,250,0.22)'],
    ]) {
      targetCtx.clearRect(0, 0, glitchCanvas.width, glitchCanvas.height);
      targetCtx.drawImage(glitchCanvas, 0, 0);
      targetCtx.globalCompositeOperation = 'source-atop';
      targetCtx.fillStyle = tint;
      targetCtx.fillRect(0, 0, glitchCanvas.width, glitchCanvas.height);
      targetCtx.globalCompositeOperation = 'source-over';
    }

    ctx.clearRect(0, 0, cw, ch);
    ctx.save();
    ctx.globalAlpha = 0.94;
    ctx.drawImage(glitchCanvas, 0, 0, cw, ch);
    ctx.globalCompositeOperation = 'screen';
    ctx.globalAlpha = 0.36;
    ctx.drawImage(redTintCanvas, -2, 0, cw, ch);
    ctx.drawImage(blueTintCanvas, 2, 0, cw, ch);
    ctx.restore();
  } catch (_) {
    // Canvas taint or readback failure should not stop the render loop.
  }
}

function drawScanlines(ctx, cw, ch, broken = false) {
  const step = 4;
  ctx.save();
  for (let y = 0; y < ch; y += step) {
    ctx.fillStyle = `rgba(226,232,240,${broken ? 0.03 : 0.018})`;
    ctx.fillRect(0, y, cw, 1);
    ctx.fillStyle = `rgba(2,6,23,${broken ? 0.04 : 0.025})`;
    ctx.fillRect(0, y + 1, cw, 1);
  }
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
    for (let i = circuitPulses.length - 1; i >= 0; i--) {
      const pulse = circuitPulses[i];
      pulse.progress += dt * pulse.speed;
      if (pulse.progress > 1 + pulse.trail) circuitPulses.splice(i, 1);
    }
  }
  syncArchiveShelfState();
  syncReceiptPrinterState();
  AmbientAudio.update(workingCount);

  // Render
  ctx.clearRect(0, 0, cw, ch);
  drawIsometricGrid(ctx, scale);
  drawCircuitLines(ctx, scale);
  drawZones(ctx, scale);

  // Radar (under agents, over zones)
  if (!_lowMotion) drawRadar(ctx, scale, dt);

  // Agents sorted by Y
  const sorted = [...agents.values()].sort((a, b) => a.y - b.y);
  for (const a of sorted) a.draw(ctx, scale);

  // Radar glow on agents (over agent sprites)
  if (!_lowMotion) drawRadarGlow(ctx, scale);

  if (!_lowMotion) {
    drawCircuitPulses(ctx, scale);
    for (const d of deliveryPackets) d.draw(ctx, scale);
    for (const cube of archiveCubeFlights) cube.draw(ctx, scale);
    for (const dr of drones) dr.draw(ctx, scale);
    for (const p of particles) p.draw(ctx, scale);
  }

  // Party overlay (topmost visual, under broken glow)
  if (!_lowMotion) drawPartyOverlay(ctx, cw, ch, scale, dt);

  const isBrokenRuntime = String(rd.runtime_state || '').toUpperCase() === 'BROKEN';
  if (!_lowMotion && isBrokenRuntime) applyBrokenGlitch();
  drawScanlines(ctx, cw, ch, isBrokenRuntime);
  drawBrokenGlow(ctx, cw, ch, severity);
}

export function startRenderLoop() {
  window.addEventListener('resize', resize);
  resize();
  requestAnimationFrame(loop);
}
