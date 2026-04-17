// controller/js/sidebar.js — Tab-based sidebar with event log
import { STATE_COLORS, LANE_ROLES } from './config.js';
import { PipelineState } from './state.js';
import { agents } from './agents.js';

let _activeTab = 'agents';
const TABS = ['agents', 'round', 'artifacts', 'incidents'];
const TAB_ICONS = { agents: '\u{1F465}', round: '\u{1F4CB}', artifacts: '\u{1F4E6}', incidents: '\u{1F6A8}' };
let _incidentBadge = 0;

function esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function basename(p) { return String(p || '').split('/').filter(Boolean).pop() || '\u2014'; }
function truncate(s, n) { return s.length > n ? s.slice(0, n) + '\u2026' : s; }

export function switchTab(tabName) {
  if (!TABS.includes(tabName)) return;
  _activeTab = tabName;
  if (tabName === 'incidents') _incidentBadge = 0;
  renderSidebar();
}

export function initSidebar() {
  renderSidebar();
  PipelineState.onChange((type, detail) => {
    if (type === 'poll') renderSidebar();
    if (type === 'event') renderEvents();
    if (type === 'fatigueChange') renderSidebar(); // Re-render on test hook fatigue changes
    // Auto-switch to incidents on severity events
    if (type === 'controlChange' && detail.to === 'needs_operator') { _incidentBadge++; switchTab('incidents'); }
  });
}

function renderSidebar() {
  const data = PipelineState.data || {};
  const tabBar = document.getElementById('tab-bar');
  const tabContent = document.getElementById('tab-content');
  if (!tabBar || !tabContent) return;

  // Tab bar
  tabBar.innerHTML = TABS.map(t => {
    const active = t === _activeTab ? ' active' : '';
    const badge = t === 'incidents' && _incidentBadge > 0 ? `<span class="tab-badge">${_incidentBadge}</span>` : '';
    return `<button class="tab-btn${active}" data-tab="${t}" onclick="window.__switchTab('${t}')">${TAB_ICONS[t]}${badge}</button>`;
  }).join('');

  // Tab content
  switch (_activeTab) {
    case 'agents': tabContent.innerHTML = renderAgentsTab(data); break;
    case 'round': tabContent.innerHTML = renderRoundTab(data); break;
    case 'artifacts': tabContent.innerHTML = renderArtifactsTab(data); break;
    case 'incidents': tabContent.innerHTML = renderIncidentsTab(data); break;
  }
}

function renderAgentsTab(data) {
  const lanes = data.lanes || [];
  if (!lanes.length) return '<div style="font-size:11px;color:#3d5070">\uC5D0\uC774\uC804\uD2B8 \uC5C6\uC74C</div>';
  return lanes.map(lane => {
    const s = (lane.state || 'off').toLowerCase(), color = STATE_COLORS[s] || STATE_COLORS.off;
    const role = LANE_ROLES[(lane.name || '').toLowerCase()] || '', note = lane.note || lane.status_note || '';
    const initial = (lane.name || '?')[0].toUpperCase();
    const agent = agents.get(lane.name || '');
    const fatigue = agent ? agent.fatigueState : '';
    const fatigueLabel = fatigue === 'coffee' ? '\u2615 \uCEE4\uD53C \uCDA9\uC804 \uC911' : fatigue === 'fatigued' ? '\u{1F4A6} \uD53C\uB85C \uB204\uC801' : '';
    return `<div class="agent-card" data-agent="${esc(lane.name || '')}" data-fatigue="${fatigue}"><div class="agent-avatar" style="background:${color}">${esc(initial)}</div>
      <div class="agent-info"><div class="agent-name">${esc(lane.name || '?')}</div><div class="agent-role">${esc(role)}</div>
      ${note ? `<div class="agent-detail">${esc(truncate(note, 50))}</div>` : ''}
      ${fatigueLabel ? `<div class="agent-fatigue" data-fatigue="${fatigue}">${fatigueLabel}</div>` : ''}</div>
      <div class="agent-state-dot" style="background:${color}" title="${esc(s)}"></div></div>`;
  }).join('');
}

function renderRoundTab(data) {
  const pres = PipelineState.getPresentation(data);
  const control = data.control || {};
  return `
    <div class="info-row"><span class="info-label">\uC0C1\uD0DC</span><span class="info-value ${pres.runtimeClass}">${esc(pres.runtimeState)}</span></div>
    <div class="info-row"><span class="info-label">Control</span><span class="info-value ${pres.controlClass}">${esc(pres.controlStatus)}</span></div>
    <div class="info-row"><span class="info-label">Control File</span><span class="info-value dim">${esc(control.active_control_file || '\u2014')}</span></div>
    <div class="info-row"><span class="info-label">Control Seq</span><span class="info-value dim">${control.active_control_seq >= 0 ? control.active_control_seq : '\u2014'}</span></div>
    <div class="info-row"><span class="info-label">Round</span><span class="info-value ${pres.roundClass}">${esc(pres.roundState)}</span></div>
    <div class="info-row"><span class="info-label">Watcher</span><span class="info-value ${pres.watcherClass}">${esc(pres.watcherStatus)}</span></div>
  `;
}

function renderArtifactsTab(data) {
  const lr = data.last_receipt || {};
  const lw = (data.artifacts || {}).latest_work || {};
  const lv = (data.artifacts || {}).latest_verify || {};
  return `
    <div class="section-title">Receipt</div>
    ${lr.verify_result ? `<div class="info-row"><span class="info-label">\uACB0\uACFC</span><span class="info-value ${lr.verify_result === 'passed' ? 'ok' : 'err'}">${esc(lr.verify_result)}</span></div>
    <div class="info-row"><span class="info-label">ID</span><span class="info-value dim">${esc(lr.receipt_id || '\u2014')}</span></div>` : '<div class="info-row"><span class="info-value dim">receipt \uC5C6\uC74C</span></div>'}
    <div class="section-title" style="margin-top:12px">Artifacts</div>
    <div class="info-row"><span class="info-label">Work</span><span class="info-value">${esc(basename(lw.path))}</span></div>
    <div class="info-row"><span class="info-label">Verify</span><span class="info-value">${esc(basename(lv.path))}</span></div>
  `;
}

function renderIncidentsTab(data) {
  const dr = (data.degraded_reasons || []).filter(Boolean);
  const pres = PipelineState.getPresentation(data);
  const watcher = data.watcher || {};
  const autonomy = data.autonomy || {};
  return `
    <div class="info-row"><span class="info-label">\uC2EC\uAC01\uB3C4</span><span class="info-value ${pres.runtimeClass}">${esc(pres.runtimeState)}</span></div>
    <div class="info-row"><span class="info-label">Watcher</span><span class="info-value ${pres.watcherClass}">${esc(pres.watcherStatus)}</span></div>
    ${dr.length ? dr.map(r => `<div class="info-row"><span class="info-label">Degraded</span><span class="info-value ${pres.uncertain ? 'warn' : 'err'}">${esc(r)}</span></div>`).join('') : '<div class="info-row"><span class="info-value dim">\uC774\uC0C1 \uC5C6\uC74C</span></div>'}
    ${autonomy.block_reason ? `<div class="info-row"><span class="info-label">Block</span><span class="info-value warn">${esc(autonomy.block_reason)}</span></div>` : ''}
    ${autonomy.decision_required ? `<div class="info-row"><span class="info-label">Decision</span><span class="info-value warn">${esc(autonomy.decision_required)}</span></div>` : ''}
  `;
}

function renderEvents() {
  const el = document.getElementById('event-list');
  if (!el) return;
  const log = PipelineState.eventLog;
  if (!log.length) { el.innerHTML = '<div class="event-item"><span class="event-time">\u2014</span><span class="event-msg">\uB300\uAE30 \uC911</span></div>'; return; }
  el.innerHTML = log.map(e => `<div class="event-item"><span class="event-time">${esc(e.time)}</span><span class="event-dot ${e.type}"></span><span class="event-msg">${esc(e.msg)}</span></div>`).join('');
}

// Global hook for tab buttons
window.__switchTab = switchTab;
