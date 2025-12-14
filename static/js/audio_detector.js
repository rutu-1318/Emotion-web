document.addEventListener("DOMContentLoaded", () => {
  // === Elements ===
  const micBtn = document.getElementById("recordBtn");
  const micStatus = document.getElementById("micStatus");
  const uploadInput = document.getElementById("audio-file");
  const spinner = document.createElement("div");
  spinner.id = "spinner";
  spinner.classList.add("spinner");
  document.body.appendChild(spinner);

  const MAX_DURATION = 10; // seconds
  let isRecording = false;
  let emotionChart = null;

  // === Theme Toggle ===
  const themeToggleBtn = document.getElementById("toggle-theme");
  const currentTheme = localStorage.getItem("theme") || "light";
  if (currentTheme === "dark") document.body.classList.add("dark-mode");

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      localStorage.setItem(
        "theme",
        document.body.classList.contains("dark-mode") ? "dark" : "light"
      );
    });
  }

  // === Microphone Recording & WAV conversion ===
  micBtn.addEventListener("click", async () => {
    if (isRecording) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const processor = audioContext.createScriptProcessor(4096, 1, 1);

      let audioData = [];
      processor.onaudioprocess = e => {
        if (!isRecording) return;
        audioData.push(new Float32Array(e.inputBuffer.getChannelData(0)));
      };

      source.connect(processor);
      processor.connect(audioContext.destination);

      isRecording = true;
      micStatus.textContent = "Recording... Max 10 seconds";
      spinner.classList.add("visible");
      micBtn.disabled = true;

      const autoStopTimeout = setTimeout(stopRecording, MAX_DURATION * 1000);

      function stopRecording() {
        if (!isRecording) return;
        isRecording = false;
        micStatus.textContent = "Recording stopped";
        processor.disconnect();
        source.disconnect();
        audioContext.close();
        micBtn.disabled = false;
        clearTimeout(autoStopTimeout);

        const wavBlob = encodeWAV(audioData, audioContext.sampleRate);
        sendAudio(wavBlob);
      }

      // Attach manual stop on click again
      micBtn.onclick = stopRecording;

    } catch (err) {
      console.error(err);
      alert("Microphone access denied or not available.");
      micBtn.disabled = false;
    }
  });

  // === File Upload Validation & send ===
  if (uploadInput) {
    uploadInput.addEventListener("change", () => {
      const file = uploadInput.files[0];
      if (!file) return;

      const audio = document.createElement("audio");
      audio.src = URL.createObjectURL(file);
      audio.onloadedmetadata = () => {
        if (audio.duration > MAX_DURATION) {
          alert(`Audio too long! Maximum duration is ${MAX_DURATION} seconds.`);
          uploadInput.value = "";
        } else {
          sendAudio(file);
        }
      };
    });
  }

  // === Send audio to Flask ===
  async function sendAudio(blob) {
    const formData = new FormData();
    formData.append("audio_blob", blob, "recording.wav");

    try {
      const res = await fetch("/record_audio", { method: "POST", body: formData });
      const result = await res.json();
      spinner.classList.remove("visible");

      if (result.success) {
        micStatus.textContent = `🎵 Emotion: ${result.emotion} (${result.confidence}%)`;
        updateChart(result.probabilities);
      } else {
        alert(result.error || "Audio processing failed");
      }
    } catch (err) {
      console.error(err);
      alert("Server error during audio processing");
      spinner.classList.remove("visible");
    }
  }

  // === WAV Encoder ===
  function encodeWAV(samples, sampleRate) {
    const merge = flattenArray(samples);
    const buffer = new ArrayBuffer(44 + merge.length * 2);
    const view = new DataView(buffer);

    writeString(view, 0, "RIFF");
    view.setUint32(4, 36 + merge.length * 2, true);
    writeString(view, 8, "WAVE");

    writeString(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);

    writeString(view, 36, "data");
    view.setUint32(40, merge.length * 2, true);

    floatTo16BitPCM(view, 44, merge);
    return new Blob([view], { type: "audio/wav" });
  }

  function flattenArray(channelBuffers) {
    const length = channelBuffers.reduce((sum, arr) => sum + arr.length, 0);
    const result = new Float32Array(length);
    let offset = 0;
    channelBuffers.forEach(arr => {
      result.set(arr, offset);
      offset += arr.length;
    });
    return result;
  }

  function floatTo16BitPCM(output, offset, input) {
    for (let i = 0; i < input.length; i++, offset += 2) {
      let s = Math.max(-1, Math.min(1, input[i]));
      output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
  }

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) view.setUint8(offset + i, string.charCodeAt(i));
  }

  // === Chart.js Update ===
  function updateChart(probabilities) {
    const ctx = document.getElementById("emotionChart").getContext("2d");
    const labels = Object.keys(probabilities);
    const data = Object.values(probabilities);

    if (emotionChart) emotionChart.destroy();

    emotionChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [{
          label: "Emotion Probability (%)",
          data: data,
          backgroundColor: "rgba(54, 162, 235, 0.5)"
        }]
      },
      options: {
        responsive: true,
        scales: { y: { beginAtZero: true, max: 100 } }
      }
    });
  }
});
