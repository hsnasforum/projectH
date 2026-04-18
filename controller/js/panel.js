// controller/js/panel.js — Slide-in desk dashboard panel
import { PipelineState } from './state.js';
import { agents } from './agents.js';
import { SoundFX } from './audio.js';
import { STATE_COLORS, LOG_REFRESH_MS } from './config.js';

let _panelOpen = false;
let _panelLane = '';
let _tailInterval = null;
let _tailInFlight = false;
let _sendInFlight = false;

function esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }

export function openPanel(agentName) {
  _panelLane = agentName;
  _panelOpen = true;
  const panel = document.getElementById('desk-panel');
  if (!panel) return;
  panel.classList.add('open');
  renderPanel();
  fetchTail();
  if (_tailInterval) clearInterval(_tailInterval);
  _tailInterval = setInterval(fetchTail, 1000); // 1s refresh
  SoundFX.blip();
}

export function closePanel() {
  _panelOpen = false; _panelLane = '';
  const panel = document.getElementById('desk-panel');
  if (panel) panel.classList.remove('open');
  if (_tailInterval) { clearInterval(_tailInterval); _tailInterval = null; }
}

export function initPanel() {
  // Real-time update on poll
  PipelineState.onChange((type) => {
    if (type === 'poll' && _panelOpen) renderPanel();
  });

  // Close on Escape
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && _panelOpen) closePanel(); });

  // Input handlers
  const input = document.getElementById('panel-input');
  const sendBtn = document.getElementById('panel-send');
  if (input) {
    input.addEventListener('input', syncInputState);
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) { e.preventDefault(); sendInput(); }
    });
  }
  if (sendBtn) sendBtn.addEventListener('click', sendInput);
}

function renderPanel() {
  if (!_panelOpen || !_panelLane) return;
  const agent = agents.get(_panelLane);
  const data = PipelineState.data || {};
  const lane = (data.lanes || []).find(l => l.name === _panelLane) || {};
  const control = data.control || {};
  const color = agent ? agent.color : STATE_COLORS.off;

  document.getElementById('panel-title').textContent = `${_panelLane} Desk`;
  document.getElementById('panel-title').style.borderLeftColor = color;
  document.getElementById('panel-state').textContent = (lane.state || 'OFF').toUpperCase();
  document.getElementById('panel-state').style.color = color;
  document.getElementById('panel-pid').textContent = lane.pid || '\u2014';
  document.getElementById('panel-fatigue').textContent = agent ? `${Math.round(agent.fatigue)}s` : '\u2014';
  document.getElementById('panel-last-event').textContent = lane.last_event_at || '\u2014';
  document.getElementById('panel-control-file').textContent = control.active_control_file || '\u2014';
  document.getElementById('panel-control-seq').textContent = control.active_control_seq >= 0 ? `#${control.active_control_seq}` : '\u2014';
  document.getElementById('panel-control-status').textContent = control.active_control_status || 'none';
}

async function fetchTail() {
  if (_tailInFlight || !_panelLane) return;
  _tailInFlight = true;
  const body = document.getElementById('panel-tail');
  try {
    const res = await fetch(`/api/runtime/capture-tail?lane=${encodeURIComponent(_panelLane)}&lines=15`);
    const data = await res.json();
    if (data.ok && data.text) { body.textContent = data.text; }
    else { body.textContent = `(${_panelLane} \u2014 \uD65C\uC131 \uB85C\uADF8 \uC5C6\uC74C)`; }
  } catch (e) { body.textContent = `(\uB85C\uADF8 \uC870\uD68C \uC2E4\uD328: ${e.message})`; }
  finally { _tailInFlight = false; }
}

function syncInputState() {
  const input = document.getElementById('panel-input');
  const btn = document.getElementById('panel-send');
  if (!input || !btn) return;
  btn.disabled = !_panelLane || !input.value.trim() || _sendInFlight;
  input.disabled = !_panelLane || _sendInFlight;
}

async function sendInput() {
  const input = document.getElementById('panel-input');
  const text = String(input?.value || '').trim();
  if (!_panelLane || !text || _sendInFlight) return;
  _sendInFlight = true; syncInputState();
  try {
    const res = await fetch('/api/runtime/send-input', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lane: _panelLane, text }),
    });
    const data = await res.json();
    if (!res.ok || data.ok === false) throw new Error(data.error || 'send failed');
    input.value = ''; SoundFX.blip();
    await fetchTail();
  } catch (e) { SoundFX.error(); }
  finally { _sendInFlight = false; syncInputState(); if (input) input.focus(); }
}

// Global hooks
window.__closePanel = closePanel;
