// controller/js/audio.js — Sound effects and ambient audio

export const PrefStore = (() => {
  let _available = null;
  let _eventCallback = null;
  function _probe() {
    if (_available !== null) return _available;
    try {
      const k = '__office_storage_probe__';
      localStorage.setItem(k, '1');
      localStorage.removeItem(k);
      _available = true;
    } catch (e) {
      _available = false;
      if (_eventCallback) _eventCallback('warn', '\uD658\uACBD \uC124\uC815 \uC800\uC7A5 \uBD88\uAC00 \u2014 \uC0C8\uB85C\uACE0\uCE68 \uC2DC toolbar \uC124\uC815\uC774 \uCD08\uAE30\uD654\uB429\uB2C8\uB2E4');
    }
    return _available;
  }
  return {
    get(key) { return _probe() ? localStorage.getItem(key) : null; },
    set(key, val) { if (_probe()) localStorage.setItem(key, val); },
    get available() { return _probe(); },
    setEventCallback(fn) { _eventCallback = fn; },
  };
})();

export const SoundFX = {
  _ctx: null, _enabled: true,
  _ensure() {
    if (!this._ctx) { try { this._ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { this._enabled = false; } }
    if (this._ctx && this._ctx.state === 'suspended') this._ctx.resume();
    return this._ctx;
  },
  _play(notes, { gain = 0.12, type = 'square' } = {}) {
    if (!this._enabled) return; const ctx = this._ensure(); if (!ctx) return;
    const now = ctx.currentTime, osc = ctx.createOscillator(), vol = ctx.createGain();
    osc.type = type; osc.connect(vol); vol.connect(ctx.destination);
    let t = now;
    for (const [freq, dur] of notes) {
      osc.frequency.setValueAtTime(freq, t); vol.gain.setValueAtTime(gain, t);
      vol.gain.setValueAtTime(gain, t + dur * 0.7); vol.gain.linearRampToValueAtTime(0, t + dur); t += dur;
    }
    osc.start(now); osc.stop(t);
  },
  click()   { this._play([[880, 0.06]], { gain: 0.08 }); },
  success() { this._play([[523, 0.08], [659, 0.08], [784, 0.12]], { gain: 0.10 }); },
  error()   { this._play([[220, 0.12], [165, 0.18]], { gain: 0.13, type: 'sawtooth' }); },
  warn()    { this._play([[440, 0.08], [0, 0.06], [440, 0.08]], { gain: 0.09 }); },
  blip()    { this._play([[660, 0.05]], { gain: 0.06 }); },
};

export const AmbientAudio = {
  _typingOsc: null, _typingGain: null, _toneOsc: null, _toneGain: null,
  _running: false, muted: false, _targetTypingVol: 0,

  toggle() {
    this.muted = !this.muted;
    const btn = document.getElementById('mute-btn');
    if (btn) { btn.textContent = this.muted ? '\u{1F507}' : '\u{1F50A}'; btn.title = this.muted ? '\uC0AC\uC6B4\uB4DC \uCF1C\uAE30' : '\uC74C\uC18C\uAC70'; }
    PrefStore.set('office_muted', this.muted ? '1' : '0');
    if (this.muted) this._stop(); else this._start();
  },

  _start() {
    if (this._running || this.muted) return;
    const ac = SoundFX._ensure(); if (!ac) return;
    this._running = true;
    this._toneOsc = ac.createOscillator(); this._toneGain = ac.createGain();
    this._toneOsc.type = 'sine'; this._toneOsc.frequency.value = 85; this._toneGain.gain.value = 0.008;
    this._toneOsc.connect(this._toneGain); this._toneGain.connect(ac.destination); this._toneOsc.start();
    this._typingOsc = ac.createOscillator(); this._typingGain = ac.createGain();
    this._typingOsc.type = 'square'; this._typingOsc.frequency.value = 200; this._typingGain.gain.value = 0;
    this._typingOsc.connect(this._typingGain); this._typingGain.connect(ac.destination); this._typingOsc.start();
  },

  _stop() {
    try { this._toneOsc?.stop(); } catch(e) {}
    try { this._typingOsc?.stop(); } catch(e) {}
    this._running = false;
    this._toneOsc = null; this._typingOsc = null; this._toneGain = null; this._typingGain = null;
  },

  update(workingCount) {
    if (!this._running || this.muted) return;
    this._targetTypingVol = Math.min(0.015, workingCount * 0.005);
    if (this._typingGain) {
      const cur = this._typingGain.gain.value;
      this._typingGain.gain.value = cur + (this._targetTypingVol - cur) * 0.05;
    }
    if (this._typingOsc && Math.random() < 0.1) {
      this._typingOsc.frequency.value = 150 + Math.random() * 300;
    }
  },

  restore() {
    if (PrefStore.get('office_muted') === '1') {
      this.muted = true;
      const mb = document.getElementById('mute-btn');
      if (mb) { mb.textContent = '\u{1F507}'; mb.title = '\uC0AC\uC6B4\uB4DC \uCF1C\uAE30'; }
    }
  },
};
