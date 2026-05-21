// Shared runtime Queue presentation reducer. It is intentionally a classic
// script as well as module-safe so both cozy.js and state.js use one contract.
(function attachQueuePresentation(root) {
  const DEFAULT_INACTIVE_RUNTIME_STATES = new Set(['STOPPED', 'STOPPING', 'BROKEN']);
  const DEFAULT_UNCERTAIN_RUNTIME_REASONS = new Set([
    'supervisor_missing_recent_ambiguous',
    'supervisor_missing_snapshot_undated',
  ]);

  function stringValue(value) {
    return String(value || '').trim();
  }

  function numberValue(value, fallback = -1) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  }

  function currentTurnState(data) {
    if (data && data.turn_state && typeof data.turn_state === 'object') return data.turn_state;
    if (data && data.compat && data.compat.turn_state && typeof data.compat.turn_state === 'object') return data.compat.turn_state;
    return {};
  }

  function liveRoundState(data, turn = currentTurnState(data)) {
    const snapshot = (data && data.runtime_snapshot) || {};
    const snapshotRoundState = stringValue(snapshot.round_state);
    if (snapshotRoundState) return snapshotRoundState;
    const round = (data && data.active_round) || {};
    const roundState = stringValue(round.state).toUpperCase();
    const turnState = stringValue((turn || {}).state).toUpperCase();
    if (roundState && roundState !== 'IDLE') return roundState;
    return turnState || roundState || 'IDLE';
  }

  function isSuppressedOperatorCandidate(data, automationHealth, controlStatus) {
    const snapshot = (data && data.runtime_snapshot) || {};
    if (typeof snapshot.suppressed_operator_candidate === 'boolean') {
      return snapshot.suppressed_operator_candidate;
    }
    const autonomy = (data || {}).autonomy || {};
    const autonomyMode = stringValue(autonomy.mode);
    return controlStatus === 'none'
      && automationHealth === 'ok'
      && autonomy.operator_eligible === false
      && autonomyMode === 'hibernate';
  }

  function compatActiveControl(data) {
    return (((data || {}).compat || {}).control_slots || {}).active || {};
  }

  function hasCompatActiveControl(data) {
    const active = compatActiveControl(data);
    const seq = numberValue(active.control_seq);
    return Boolean(stringValue(active.file) || stringValue(active.status) || seq >= 0);
  }

  function isNoQueuedPipelineTask(data, showLive, controlStatus, automationHealth) {
    const snapshotQueue = (((data || {}).runtime_snapshot || {}).queue) || {};
    if (typeof snapshotQueue.no_queued_pipeline_task === 'boolean') {
      return snapshotQueue.no_queued_pipeline_task;
    }
    const payload = data || {};
    const control = payload.control || {};
    const activeRound = payload.active_round;
    const controlFile = stringValue(control.active_control_file);
    const controlSeq = numberValue(control.active_control_seq);
    return Boolean(showLive)
      && controlStatus === 'none'
      && automationHealth === 'ok'
      && !stringValue(payload.automation_reason_code)
      && !payload.stale_advisory_pending
      && !controlFile
      && controlSeq < 0
      && !activeRound
      && !hasCompatActiveControl(payload);
  }

  function pipelineQueuePresentation(data, showLive, controlStatus, roundState, automationHealth, noQueuedPipelineTask) {
    const snapshotQueue = (((data || {}).runtime_snapshot || {}).queue) || {};
    if (stringValue(snapshotQueue.status)) {
      return {
        status: stringValue(snapshotQueue.status),
        className: stringValue(snapshotQueue.class_name) || 'neutral',
      };
    }
    const payload = data || {};
    const control = payload.control || {};
    const controlSeq = numberValue(control.active_control_seq);
    if (noQueuedPipelineTask) return { status: '대기 중인 작업 없음', className: 'ok' };
    if (!showLive) return { status: '런타임 비활성화됨', className: 'dim' };
    if (automationHealth && automationHealth !== 'ok') return { status: automationHealth, className: 'warn' };
    if (controlStatus && controlStatus !== 'none') {
      const suffix = controlSeq >= 0 ? ` #${controlSeq}` : '';
      return { status: `${controlStatus}${suffix}`, className: controlStatus === 'needs_operator' ? 'warn' : 'neutral' };
    }
    if (hasCompatActiveControl(payload)) {
      const active = compatActiveControl(payload);
      const suffix = numberValue(active.control_seq) >= 0 ? ` #${numberValue(active.control_seq)}` : '';
      return { status: `${stringValue(active.status) || 'control_pending'}${suffix}`, className: 'neutral' };
    }
    if (roundState && !['IDLE', 'uncertain'].includes(roundState)) return { status: roundState, className: 'neutral' };
    return { status: '활성화된 제어 없음', className: 'dim' };
  }

  function buildPresentation(data, options = {}) {
    const payload = data || {};
    const runtimeState = stringValue(payload.runtime_state || 'STOPPED').toUpperCase();
    const control = payload.control || {};
    const watcher = payload.watcher || {};
    const turn = currentTurnState(payload);
    const degradedReasons = (payload.degraded_reasons || []).filter(Boolean);
    const degradedReason = degradedReasons[0] || stringValue(payload.degraded_reason);
    const automationHealth = stringValue(payload.automation_health || 'ok');
    const automationReason = stringValue(payload.automation_reason_code);
    const automationFamily = stringValue(payload.automation_incident_family);
    const automationAction = stringValue(payload.automation_next_action || 'continue');
    const automationDetail = stringValue(payload.automation_health_detail);
    const controlAgeCycles = Number(payload.control_age_cycles || 0);
    const staleAdvisoryPending = Boolean(payload.stale_advisory_pending);
    const inactiveStates = options.inactiveRuntimeStates || DEFAULT_INACTIVE_RUNTIME_STATES;
    const uncertainReasons = options.uncertainRuntimeReasons || DEFAULT_UNCERTAIN_RUNTIME_REASONS;
    const uncertain = runtimeState === 'DEGRADED' && degradedReasons.some((reason) => uncertainReasons.has(reason));
    const inactive = inactiveStates.has(runtimeState);
    const showLive = !inactive && !uncertain;
    const rawControlStatus = showLive ? (control.active_control_status || 'none') : (uncertain ? 'uncertain' : 'none');
    const controlStatus = rawControlStatus;
    const suppressedOperatorCandidate = showLive
      ? isSuppressedOperatorCandidate(payload, automationHealth, rawControlStatus)
      : false;
    const roundState = showLive ? liveRoundState(payload, turn) : (uncertain ? 'uncertain' : 'IDLE');
    const noQueuedPipelineTask = isNoQueuedPipelineTask(payload, showLive, controlStatus, automationHealth);
    const queue = pipelineQueuePresentation(payload, showLive, controlStatus, roundState, automationHealth, noQueuedPipelineTask);
    let watcherStatus = 'Dead';
    let watcherClass = 'dim';
    if (uncertain) {
      watcherStatus = 'Unknown';
      watcherClass = 'warn';
    } else if (watcher.alive) {
      watcherStatus = 'Alive';
      watcherClass = 'ok';
    } else if (runtimeState === 'BROKEN') {
      watcherClass = 'err';
    } else if (runtimeState === 'STOPPING') {
      watcherClass = 'neutral';
    }
    const controlClass = controlStatus === 'implement' ? 'ok'
      : controlStatus === 'needs_operator' || controlStatus === 'uncertain' ? 'warn'
      : controlStatus === 'none' ? 'dim' : 'neutral';
    const roundClass = roundState === 'uncertain' ? 'warn' : roundState === 'IDLE' ? 'dim' : 'neutral';
    const runtimeClass = runtimeState === 'RUNNING' ? 'ok'
      : runtimeState === 'DEGRADED' ? 'warn'
      : runtimeState === 'STOPPING' ? 'neutral'
      : runtimeState === 'BROKEN' ? 'err' : 'dim';
    const badgeClass = runtimeState === 'RUNNING' ? 'running'
      : runtimeState === 'DEGRADED' ? 'degraded'
      : runtimeState === 'STOPPING' ? 'stopping'
      : runtimeState === 'BROKEN' ? 'broken' : 'stopped';
    return {
      runtimeState,
      runtimeClass,
      badgeClass,
      uncertain,
      inactive,
      controlStatus,
      controlClass,
      roundState,
      roundClass,
      watcherStatus,
      watcherClass,
      degradedReason,
      degradedReasons,
      automationHealth,
      automationReason,
      automationFamily,
      automationAction,
      automationDetail,
      controlAgeCycles,
      staleAdvisoryPending,
      suppressedOperatorCandidate,
      noQueuedPipelineTask,
      pipelineQueueStatus: queue.status,
      pipelineQueueClass: queue.className,
    };
  }

  root.PipelineQueuePresentation = Object.freeze({
    currentTurnState,
    liveRoundState,
    isSuppressedOperatorCandidate,
    isNoQueuedPipelineTask,
    pipelineQueuePresentation,
    buildPresentation,
  });
})(globalThis);
