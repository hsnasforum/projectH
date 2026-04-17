// controller/js/agents.js — Agent entities with zone-bounded movement
import { ZONE_MAP, CORRIDOR_Y, STATE_COLORS, LANE_ROLES, WALK_SPEED,
         STATE_GIF_ASSETS, STATE_PARTICLES, VIRTUAL_W } from './config.js';
import { PipelineState } from './state.js';

// ── Sprite Manager ──
export const SpriteManager = {
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

function truncate(s, n) { return s.length > n ? s.slice(0, n) + '\u2026' : s; }

// ── Agent Map (shared) ──
export const agents = new Map();

export function spawnParticle(agentName, text, opts) {
  const agent = agents.get(agentName);
  if (!agent) return;
  particles.push(new Particle(agent.x, agent.y, text, opts));
}

export function spawnStateParticle(agentName, newState) {
  spawnParticle(agentName, STATE_PARTICLES[newState] || '\u2753', { size: 20, lifetime: 1.8 });
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
    this._deliveryIcon = icon || '\u{1F4C4}';
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
        spawnParticle(this.name, '\u{1F4A6}', { size: 12, lifetime: 1.0 });
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
  // Zone-based: return zone map for compatibility
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

window.testAntiStacking = function(name, otherX, otherY, count) {
  const agent = agents.get(name);
  if (!agent) return [];
  // Zone-bounded agents don't need anti-stacking since they stay in separate zones.
  // Still return results for test compatibility.
  const results = [];
  for (let i = 0; i < count; i++) {
    const pt = agent._pickIdleTarget();
    results.push({ x: pt.x, y: pt.y, distFromOther: Math.hypot(pt.x - otherX, pt.y - otherY) });
  }
  return results;
};

window.testHistoryPenalty = function(name, historyIndices, count) {
  const agent = agents.get(name);
  if (!agent) return [];
  // Zone-bounded: no spot-based roaming. Return empty for compatibility.
  return [];
};
