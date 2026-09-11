export function evaluateDisasterRisk(temperatureC, depthM) {
  const temp = Number(temperatureC);
  const depth = Number(depthM);

  const normalSurfaceRange = temp >= 5 && temp <= 30 && depth <= 200;
  const normalDeepRange = temp >= 2 && temp <= 12 && depth > 200;

  if (normalSurfaceRange || normalDeepRange) {
    return {
      level: "normal",
      score: 0,
      title: "Normal conditions",
      description: "Temperature and depth are within the expected ocean range.",
    };
  }

  let tempScore = 0;
  if (temp > 32 || temp < 1.5) tempScore += 3;
  else if (temp > 29 || temp < 4.0) tempScore += 2;
  else if (temp > 27 || temp < 7.0) tempScore += 1;

  let depthScore = 0;
  if (depth > 980) depthScore += 2;
  else if (depth > 900) depthScore += 1;

  const totalScore = tempScore + depthScore;

  if (totalScore >= 4 || (temp > 33 && depth > 800) || (temp < 2 && depth > 500)) {
    return {
      level: "critical",
      score: totalScore,
      title: "Critical ocean anomaly detected",
      description: "Unusual temperature and depth combination may indicate a hazardous ocean event.",
    };
  }

  if (totalScore >= 2 || (temp > 30 && depth > 600) || (temp < 4 && depth > 500)) {
    return {
      level: "warning",
      score: totalScore,
      title: "Ocean warning",
      description: "Temperature or depth is outside the normal range and should be checked.",
    };
  }

  return {
    level: "normal",
    score: totalScore,
    title: "Normal conditions",
    description: "Temperature and depth are within expected operating limits.",
  };
}

function ensureAlarmAudioContext() {
  if (typeof window === "undefined") return null;

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  if (!AudioCtx) return null;

  if (!window.__oceanembedAudioContext || window.__oceanembedAudioContext.state === "closed") {
    window.__oceanembedAudioContext = new AudioCtx();
  }

  const context = window.__oceanembedAudioContext;
  if (context.state === "suspended") {
    context.resume().catch(() => {});
  }

  return context;
}

function createToneDataUrl(frequency, durationSec, volume = 0.8) {
  const sampleRate = 22050;
  const sampleCount = Math.max(1, Math.floor(sampleRate * durationSec));
  const buffer = new Float32Array(sampleCount);
  const attack = 0.02;
  const decay = durationSec;

  for (let i = 0; i < sampleCount; i += 1) {
    const t = i / sampleRate;
    const envelope = Math.min(1, t / attack) * Math.max(0, 1 - t / decay);
    const sine = Math.sin(2 * Math.PI * frequency * t);
    buffer[i] = sine * envelope * volume;
  }

  const wav = new ArrayBuffer(44 + sampleCount * 2);
  const view = new DataView(wav);

  function writeString(offset, text) {
    for (let i = 0; i < text.length; i += 1) {
      view.setUint8(offset + i, text.charCodeAt(i));
    }
  }

  writeString(0, "RIFF");
  view.setUint32(4, 36 + sampleCount * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, sampleCount * 2, true);

  let offset = 44;
  for (let i = 0; i < sampleCount; i += 1) {
    const s = Math.max(-1, Math.min(1, buffer[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    offset += 2;
  }

  let binary = "";
  const bytes = new Uint8Array(wav);
  for (let i = 0; i < bytes.length; i += 1) {
    binary += String.fromCharCode(bytes[i]);
  }

  return `data:audio/wav;base64,${btoa(binary)}`;
}

if (typeof window !== "undefined" && !window.__oceanembedAlarmUnlocked) {
  const unlockAudio = () => {
    const context = ensureAlarmAudioContext();
    if (context && context.state === "suspended") {
      context.resume().catch(() => {});
    }
    window.__oceanembedAlarmUnlocked = true;
  };

  window.addEventListener("pointerdown", unlockAudio, { once: true });
  window.addEventListener("keydown", unlockAudio, { once: true });
}

export function triggerDisasterAlarm(level = "warning") {
  if (typeof window === "undefined") return;

  const now = Date.now();
  const lastAlarm = window.__oceanembedLastAlarmTs || 0;
  if (now - lastAlarm < 900) return;
  window.__oceanembedLastAlarmTs = now;

  const context = ensureAlarmAudioContext();
  const notes = level === "critical" ? [660, 980, 1320] : [420, 540];
  const duration = level === "critical" ? 0.18 : 0.12;

  if (context) {
    const master = context.createGain();
    master.gain.value = 0.04;
    master.connect(context.destination);

    notes.forEach((frequency, index) => {
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      const startAt = context.currentTime + index * 0.12;

      oscillator.type = level === "critical" ? "sawtooth" : "square";
      oscillator.frequency.setValueAtTime(frequency, startAt);
      gain.gain.setValueAtTime(0.0001, startAt);
      gain.gain.exponentialRampToValueAtTime(0.05, startAt + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);

      oscillator.connect(gain);
      gain.connect(master);

      oscillator.start(startAt);
      oscillator.stop(startAt + duration);
    });
  }

  try {
    notes.forEach((frequency, index) => {
      const toneDuration = level === "critical" ? 0.18 : 0.12;
      const audio = new Audio(createToneDataUrl(frequency, toneDuration, level === "critical" ? 0.75 : 0.55));
      audio.volume = level === "critical" ? 0.9 : 0.7;
      audio.play().catch(() => {});
      setTimeout(() => {
        try {
          audio.pause();
          audio.src = "";
        } catch {
          // Ignore cleanup timing issues.
        }
      }, (toneDuration + 0.2) * 1000 + index * 120);
    });
  } catch {
    // Ignore browser-specific audio errors and keep the app functional.
  }
}
