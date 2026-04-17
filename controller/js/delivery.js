// controller/js/delivery.js — Agent walk delivery + packet animation + drone
import { agents, spawnParticle, Particle, particles } from './agents.js';
import { SoundFX } from './audio.js';
import { ZONE_MAP, VIRTUAL_W } from './config.js';
import { PipelineState } from './state.js';

export const deliveryPackets = [];
export const drones = [];

function basename(p) { return String(p || '').split('/').filter(Boolean).pop() || '\u2014'; }

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
            deliveryPackets.push(new DeliveryPacket('codex_desk', 'claude_desk', '\u{1F4CB}'));
            speakAgent('Claude', '\uBC1B\uC558\uC2B5\uB2C8\uB2E4', 2.5);
            PipelineState.pushEvent('info', `Implement handoff \u2192 Claude (seq ${trigger.seq})`);
          } else if (status === 'needs_operator') {
            const owner = agents.get('Claude');
            if (owner) { owner.walkToZone('incident_zone', '\u26A0\uFE0F'); }
            PipelineState.pushEvent('warn', `Operator review requested (seq ${trigger.seq})`);
            SoundFX.warn();
          } else if (status === 'advice_ready') {
            const gemini = agents.get('Gemini');
            if (gemini) { gemini.walkToZone('codex_desk', '\u{1F4DD}'); }
            PipelineState.pushEvent('info', `Advice ready \u2192 Codex`);
          } else {
            deliveryPackets.push(new DeliveryPacket('claude_desk', 'codex_desk', '\u{1F4E6}'));
            PipelineState.pushEvent('info', `Control changed \u2192 ${status || 'none'} (seq ${trigger.seq})`);
          }
          break;
        }
        case 'work': {
          const claude = agents.get('Claude');
          if (claude) { claude.walkToZone('archive_shelf', '\u{1F4C1}'); }
          PipelineState.pushEvent('ok', `Work delivered \u2192 ${basename(trigger.path)}`);
          SoundFX.success();
          break;
        }
        case 'verify': {
          const codex = agents.get('Codex');
          if (codex) { codex.walkToZone('archive_shelf', '\u2705'); }
          PipelineState.pushEvent('info', `Verify updated \u2192 ${basename(trigger.path)}`);
          break;
        }
        case 'receipt': {
          const codex2 = agents.get('Codex');
          if (codex2) { codex2.walkToZone('receipt_board', '\u{1F9FE}'); }
          PipelineState.pushEvent('ok', `Receipt issued \u2192 ${trigger.id}`);
          SoundFX.success();
          break;
        }
      }
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
