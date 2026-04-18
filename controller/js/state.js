// controller/js/state.js — Runtime state polling and change detection
import { POLL_MS, INACTIVE_RUNTIME_STATES, UNCERTAIN_RUNTIME_REASONS } from './config.js';

const MAX_EVENTS = 40;

class _PipelineState {
  constructor() {
    this.data = null;
    this.eventLog = [];
    this._listeners = [];
    this._prev = { runtimeState: null, controlStatus: null, watcherStatus: null, uncertainRuntime: null, laneStates: {}, roundState: null };
    this._pollInFlight = false;
    this._deliveryState = {
      initialized: false, controlSeq: null,
      latestWorkPath: '', latestWorkMtime: '',
      latestVerifyPath: '', latestVerifyMtime: '',
      lastReceiptId: '',
    };
  }

  onChange(fn) { this._listeners.push(fn); }
  _notify(changeType, detail) { for (const fn of this._listeners) fn(changeType, detail); }

  pushEvent(type, msg) {
    const t = new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    this.eventLog.unshift({ type, msg, time: t });
    if (this.eventLog.length > MAX_EVENTS) this.eventLog.length = MAX_EVENTS;
    this._notify('event', { type, msg, time: t });
  }

  getPresentation(data) {
    const d = data || this.data || {};
    const runtimeState = String(d.runtime_state || 'STOPPED').toUpperCase();
    const control = d.control || {};
    const watcher = d.watcher || {};
    const round = d.active_round || {};
    const degradedReasons = (d.degraded_reasons || []).filter(Boolean);
    const degradedReason = degradedReasons[0] || String(d.degraded_reason || '').trim();
    const uncertain = runtimeState === 'DEGRADED' && degradedReasons.some(r => UNCERTAIN_RUNTIME_REASONS.has(r));
    const inactive = INACTIVE_RUNTIME_STATES.has(runtimeState);
    const showLive = !inactive && !uncertain;
    const controlStatus = showLive ? (control.active_control_status || 'none') : (uncertain ? 'uncertain' : 'none');
    const roundState = showLive ? (round.state || 'IDLE') : (uncertain ? 'uncertain' : 'IDLE');
    let watcherStatus = 'Dead', watcherClass = 'dim';
    if (uncertain) { watcherStatus = 'Unknown'; watcherClass = 'warn'; }
    else if (watcher.alive) { watcherStatus = 'Alive'; watcherClass = 'ok'; }
    else if (runtimeState === 'BROKEN') { watcherClass = 'err'; }
    else if (runtimeState === 'STOPPING') { watcherClass = 'neutral'; }
    const controlClass = controlStatus === 'implement' ? 'ok'
      : controlStatus === 'needs_operator' || controlStatus === 'uncertain' ? 'warn'
      : controlStatus === 'none' ? 'dim' : 'neutral';
    const roundClass = roundState === 'uncertain' ? 'warn' : roundState === 'IDLE' ? 'dim' : 'neutral';
    const runtimeClass = runtimeState === 'RUNNING' ? 'ok' : runtimeState === 'DEGRADED' ? 'warn'
      : runtimeState === 'STOPPING' ? 'neutral' : runtimeState === 'BROKEN' ? 'err' : 'dim';
    const badgeClass = runtimeState === 'RUNNING' ? 'running' : runtimeState === 'DEGRADED' ? 'degraded'
      : runtimeState === 'STOPPING' ? 'stopping' : runtimeState === 'BROKEN' ? 'broken' : 'stopped';
    return { runtimeState, runtimeClass, badgeClass, uncertain, inactive, controlStatus, controlClass,
      roundState, roundClass, watcherStatus, watcherClass, degradedReason, degradedReasons };
  }

  detectChanges(data) {
    const p = this.getPresentation(data);
    const rs = p.runtimeState, cs = p.controlStatus, ws = p.watcherStatus;
    const uncertaintyChanged = this._prev.uncertainRuntime !== null && this._prev.uncertainRuntime !== p.uncertain;

    if (this._prev.runtimeState !== null && this._prev.runtimeState !== rs) {
      const t = rs === 'RUNNING' ? 'ok' : rs === 'DEGRADED' ? 'warn' : rs === 'BROKEN' ? 'err' : 'info';
      this.pushEvent(t, `Runtime: ${this._prev.runtimeState} \u2192 ${rs}`);
    }
    this._prev.runtimeState = rs;
    if (uncertaintyChanged) {
      this.pushEvent(p.uncertain ? 'warn' : 'info',
        p.uncertain ? `Runtime truth uncertain: ${p.degradedReason}` : 'Runtime truth restored');
    }
    this._prev.uncertainRuntime = p.uncertain;
    if (!uncertaintyChanged && this._prev.controlStatus !== null && this._prev.controlStatus !== cs) {
      const t = cs === 'implement' ? 'ok' : cs === 'needs_operator' || cs === 'uncertain' ? 'warn' : 'info';
      this.pushEvent(t, `Control: ${this._prev.controlStatus} \u2192 ${cs}`);
      this._notify('controlChange', { from: this._prev.controlStatus, to: cs });
    }
    this._prev.controlStatus = cs;
    if (!uncertaintyChanged && this._prev.watcherStatus !== null && this._prev.watcherStatus !== ws) {
      const t = ws === 'Alive' ? 'ok' : ws === 'Unknown' ? 'warn' : 'err';
      this.pushEvent(t, `Watcher: ${this._prev.watcherStatus} \u2192 ${ws}`);
    }
    this._prev.watcherStatus = ws;
    // Round state change detection
    const roundState = ((data.active_round || {}).state || 'IDLE').toUpperCase();
    if (this._prev.roundState !== null && this._prev.roundState !== roundState) {
      if (roundState === 'CLOSED' || roundState === 'DONE') {
        this.pushEvent('ok', `Round closed \u{1F389}`);
        this._notify('roundComplete', { from: this._prev.roundState, to: roundState });
      }
    }
    this._prev.roundState = roundState;

    for (const lane of (data.lanes || [])) {
      const n = lane.name || '', s = (lane.state || 'off').toLowerCase(), prev = this._prev.laneStates[n];
      if (prev !== undefined && prev !== s) {
        const t = s === 'working' ? 'ok' : (s === 'broken' || s === 'dead') ? 'err' : 'info';
        this.pushEvent(t, `${n}: ${prev} \u2192 ${s}`);
        this._notify('laneChange', { name: n, from: prev, to: s });
      }
      this._prev.laneStates[n] = s;
    }
  }

  checkDeliveryTriggers(data) {
    const ds = this._deliveryState;
    const seq = (data.control || {}).active_control_seq;
    const artifacts = data.artifacts || {};
    const wP = String((artifacts.latest_work || {}).path || '').trim();
    const wM = String((artifacts.latest_work || {}).mtime || '').trim();
    const vP = String((artifacts.latest_verify || {}).path || '').trim();
    const vM = String((artifacts.latest_verify || {}).mtime || '').trim();
    const rId = String(data.last_receipt_id || ((data.last_receipt || {}).receipt_id) || '').trim();

    if (!ds.initialized) {
      Object.assign(ds, { initialized: true, controlSeq: seq, latestWorkPath: wP, latestWorkMtime: wM, latestVerifyPath: vP, latestVerifyMtime: vM, lastReceiptId: rId });
      return;
    }
    const triggers = [];
    if (seq != null && seq >= 0 && ds.controlSeq !== null && seq !== ds.controlSeq) {
      triggers.push({ type: 'control', status: (data.control || {}).active_control_status || '', seq });
    }
    if (wP && wP !== '\u2014' && ds.latestWorkPath && (wP !== ds.latestWorkPath || (wM && wM !== ds.latestWorkMtime))) {
      triggers.push({ type: 'work', path: wP });
    }
    if (vP && vP !== '\u2014' && ds.latestVerifyPath && (vP !== ds.latestVerifyPath || (vM && vM !== ds.latestVerifyMtime))) {
      triggers.push({ type: 'verify', path: vP });
    }
    if (ds.lastReceiptId && rId && rId !== ds.lastReceiptId) {
      triggers.push({ type: 'receipt', id: rId });
    }
    Object.assign(ds, { controlSeq: seq, latestWorkPath: wP, latestWorkMtime: wM, latestVerifyPath: vP, latestVerifyMtime: vM, lastReceiptId: rId });
    if (triggers.length) this._notify('delivery', triggers);
  }

  async poll() {
    if (this._pollInFlight) return;
    this._pollInFlight = true;
    try {
      const res = await fetch('/api/runtime/status');
      const data = await res.json();
      this.data = data;
      this.detectChanges(data);
      this.checkDeliveryTriggers(data);
      this._notify('poll', data);
    } catch (e) {
      this._notify('pollError', e);
    } finally { this._pollInFlight = false; }
  }

  startPolling() {
    this.poll();
    setInterval(() => this.poll(), POLL_MS);
  }
}

export const PipelineState = new _PipelineState();
