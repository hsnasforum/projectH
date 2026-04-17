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

    // 1. Agent click -> slide-in panel (priority)
    for (const a of agents.values()) {
      if (a.hitTest(mx, my)) { openPanel(a.name); return; }
    }

    // 2. Desk zone click -> slide-in panel
    for (const [key, zone] of Object.entries(ZONE_MAP)) {
      if (zone.agent && mx >= zone.x && mx <= zone.x + zone.w && my >= zone.y && my <= zone.y + zone.h) {
        openPanel(zone.agent); SoundFX.blip(); return;
      }
    }

    // 3. Object zone click -> sidebar tab switch
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
