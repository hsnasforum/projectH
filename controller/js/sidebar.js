// controller/js/sidebar.js — Stacked sidebar panels: agents + round + artifacts + incidents + events
import { STATE_COLORS, LANE_ROLES } from './config.js';
import { PipelineState } from './state.js';
import { agents } from './agents.js';

function esc(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function basename(p) { return String(p || '').split('/').filter(Boolean).pop() || '\u2014'; }
function truncate(s, n) { return s.length > n ? s.slice(0, n) + '\u2026' : s; }

export function switchTab(tabName) {
  // Legacy: scroll to section instead of switching tabs
  const el = document.getElementById(`sidebar-${tabName}`);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

export function initSidebar() {
  renderSidebar();
  renderEvents();
  PipelineState.onChange((type, detail) => {
    if (type === 'poll') renderSidebar();
    if (type === 'event') renderEvents();
    if (type === 'fatigueChange') renderSidebar();
    if (type === 'controlChange' && detail.to === 'needs_operator') {
      const el = document.getElementById('sidebar-incidents');
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
}

function renderSidebar() {
  const data = PipelineState.data || {};
  const container = document.getElementById('tab-content');
  if (!container) return;

  container.innerHTML =
    renderAgentsSection(data) +
    renderRoundSection(data) +
    renderArtifactsSection(data) +
    renderIncidentsSection(data);
}

// ── Agents ──
function renderAgentsSection(data) {
  const lanes = data.lanes || [];
  if (!lanes.length) return '<div id="sidebar-agents" class="sidebar-section"><div class="sidebar-section-title">파티 명부</div><div style="font-size:11px;color:#3d5070">에이전트 없음</div></div>';
  const cards = lanes.map(lane => {
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
  return `<div id="sidebar-agents" class="sidebar-section">${cards}</div>`;
}

// ── Current Round ──
function renderRoundSection(data) {
  const pres = PipelineState.getPresentation(data);
  const control = data.control || {};
  const autonomy = data.autonomy || {};
  return `<div id="sidebar-round" class="sidebar-section">
    <div class="sidebar-section-title">진행 라운드</div>
    <div class="info-row"><span class="info-label">런타임</span><span class="info-value ${pres.runtimeClass}">${esc(pres.runtimeState)}</span></div>
    <div class="info-row"><span class="info-label">큐</span><span class="info-value ${pres.pipelineQueueClass}">${esc(pres.pipelineQueueStatus)}</span></div>
    <div class="info-row"><span class="info-label">제어 상태</span><span class="info-value ${pres.controlClass}">${esc(pres.controlStatus)}</span></div>
    <div class="info-row"><span class="info-label">시퀀스</span><span class="info-value dim">${control.active_control_seq >= 0 ? control.active_control_seq : '\u2014'}</span></div>
    <div class="info-row"><span class="info-label">라운드</span><span class="info-value ${pres.roundClass}">${esc(pres.roundState)}</span></div>
    ${autonomy.mode && autonomy.mode !== 'normal' ? `<div class="info-row"><span class="info-label">모드</span><span class="info-value warn">${esc(autonomy.mode)}</span></div>` : ''}
  </div>`;
}

// ── Artifacts ──
function renderArtifactsSection(data) {
  const lr = data.last_receipt || {};
  const lw = (data.artifacts || {}).latest_work || {};
  const lv = (data.artifacts || {}).latest_verify || {};
  return `<div id="sidebar-artifacts" class="sidebar-section">
    <div class="sidebar-section-title">산출물</div>
    <div class="info-row"><span class="info-label">최신 작업 (Work)</span><span class="info-value">${esc(truncate(basename(lw.path), 24))}</span></div>
    <div class="info-row"><span class="info-label">최신 검증 (Verify)</span><span class="info-value">${esc(truncate(basename(lv.path), 24))}</span></div>
    ${lr.receipt_id ? `<div class="info-row"><span class="info-label">영수증 ID</span><span class="info-value dim">${esc(lr.receipt_id)}</span></div>` : ''}
    ${lr.verify_result ? `<div class="info-row"><span class="info-label">영수증 결과</span><span class="info-value ${lr.verify_result === 'passed' ? 'ok' : 'warn'}">${esc(lr.verify_result)}</span></div>` : ''}
    ${lr.close_status ? `<div class="info-row"><span class="info-label">영수증 종결</span><span class="info-value">${esc(lr.close_status)}</span></div>` : ''}
  </div>`;
}

// ── Incident Room ──
function renderIncidentsSection(data) {
  const dr = (data.degraded_reasons || []).filter(Boolean);
  const pres = PipelineState.getPresentation(data);
  const autonomy = data.autonomy || {};
  return `<div id="sidebar-incidents" class="sidebar-section">
    <div class="sidebar-section-title">인시던트 룸</div>
    <div class="info-row"><span class="info-label">와처</span><span class="info-value ${pres.watcherClass}">${esc(pres.watcherStatus)}</span></div>
    ${dr.length ? dr.map(r => `<div class="info-row"><span class="info-label">성능 저하</span><span class="info-value ${pres.uncertain ? 'warn' : 'err'}">${esc(r)}</span></div>`).join('') : ''}
    ${autonomy.operator_eligible !== undefined ? `<div class="info-row"><span class="info-label">운영자 개입 가능</span><span class="info-value dim">${autonomy.operator_eligible}</span></div>` : ''}
    ${autonomy.block_reason ? `<div class="info-row"><span class="info-label">차단 사유</span><span class="info-value warn">${esc(autonomy.block_reason)}</span></div>` : ''}
  </div>`;
}

function renderEvents() {
  const el = document.getElementById('event-list');
  if (!el) return;
  const log = PipelineState.eventLog;
  if (!log.length) { el.innerHTML = '<div class="event-item"><span class="event-time">\u2014</span><span class="event-msg">\uB300\uAE30 \uC911</span></div>'; return; }
  el.innerHTML = log.map(e => `<div class="event-item"><span class="event-time">${esc(e.time)}</span><span class="event-dot ${e.type}"></span><span class="event-msg">${esc(e.msg)}</span></div>`).join('');
}

// Global hook for legacy tab switching (zones.js calls switchTab)
window.__switchTab = switchTab;
