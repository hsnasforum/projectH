/* ═══════════════════════════════════════════════════════════════════
   audio.js — tiny 8-bit SFX bank (WebAudio, no assets)
   Exposes window.Audio8 with { meow, muted, setMuted, toggle }.
   Wires up #mute-btn automatically if present.
   ═══════════════════════════════════════════════════════════════════ */
(function () {
  let ctx = null;
  let muted = false;

  // Lazy AudioContext — must be created AFTER a user gesture on most browsers
  function ac() {
    if (ctx) return ctx;
    try {
      ctx = new (window.AudioContext || window.webkitAudioContext)();
    } catch (e) { ctx = null; }
    return ctx;
  }

  // Resume a suspended context (triggered by first user click)
  function unlock() {
    const c = ac();
    if (c && c.state === 'suspended') c.resume();
  }

  /* ── 8-bit "meow / squeak" ──
     Two short chirps with a pitch slide, square-wave timbre, quick
     amp envelope. Sounds like a Game Boy cat. */
  function meow() {
    if (muted) return;
    const c = ac();
    if (!c) return;
    if (c.state === 'suspended') c.resume();
    const now = c.currentTime;

    // Master gain (so both chirps share one envelope tail)
    const master = c.createGain();
    master.gain.setValueAtTime(0.0001, now);
    master.connect(c.destination);

    // Gentle lowpass so it reads as "cute" not "harsh"
    const lp = c.createBiquadFilter();
    lp.type = 'lowpass';
    lp.frequency.value = 2800;
    lp.Q.value = 0.6;
    lp.connect(master);

    // Two chirps: "mee-oww" — pitch rises then falls, each with square tone
    const chirps = [
      { t: 0.00, dur: 0.11, f0: 620, f1: 880, gain: 0.22 }, // "mee"
      { t: 0.10, dur: 0.18, f0: 780, f1: 380, gain: 0.28 }, // "oww"
    ];

    chirps.forEach(({ t, dur, f0, f1, gain }) => {
      const osc = c.createOscillator();
      osc.type = 'square';
      osc.frequency.setValueAtTime(f0, now + t);
      osc.frequency.exponentialRampToValueAtTime(Math.max(40, f1), now + t + dur);

      // Tiny vibrato for cuteness
      const lfo = c.createOscillator();
      const lfoGain = c.createGain();
      lfo.frequency.value = 14;
      lfoGain.gain.value = 18;
      lfo.connect(lfoGain);
      lfoGain.connect(osc.frequency);

      // Per-chirp envelope
      const g = c.createGain();
      g.gain.setValueAtTime(0.0001, now + t);
      g.gain.exponentialRampToValueAtTime(gain, now + t + 0.015);
      g.gain.exponentialRampToValueAtTime(0.0001, now + t + dur);

      osc.connect(g);
      g.connect(lp);

      osc.start(now + t);
      lfo.start(now + t);
      osc.stop(now + t + dur + 0.02);
      lfo.stop(now + t + dur + 0.02);
    });

    // Master tail — quick fade so chirps don't click
    master.gain.setValueAtTime(0.0001, now);
    master.gain.exponentialRampToValueAtTime(1.0, now + 0.01);
    master.gain.exponentialRampToValueAtTime(0.0001, now + 0.35);
  }

  const API = {
    meow,
    unlock,
    get muted() { return muted; },
    setMuted(v) { muted = !!v; },
    toggle() { muted = !muted; return muted; },
  };
  window.Audio8 = API;

  // Wire up the existing 🔊 / 🔇 button (cosmetic before now)
  window.addEventListener('DOMContentLoaded', () => {
    const btn = document.getElementById('mute-btn');
    if (!btn) return;

    // Replace any existing onclick (the HTML stub only toggled text)
    btn.onclick = (e) => {
      const nowMuted = API.toggle();
      e.currentTarget.textContent = nowMuted ? '🔇' : '🔊';
      unlock();
    };

    // Unlock AudioContext on first canvas interaction (browsers require gesture)
    const once = () => { unlock(); window.removeEventListener('pointerdown', once); };
    window.addEventListener('pointerdown', once);
  });
})();
