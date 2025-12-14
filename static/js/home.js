document.addEventListener('DOMContentLoaded', () => {
  console.log("✅ Home page initialized");

  // === Hover Sound Setup ===
  const hoverSoundPath = document.body.getAttribute('data-hover-sound');
  const hoverSound = hoverSoundPath ? new Audio(hoverSoundPath) : null;
  let hoverSoundEnabled = localStorage.getItem('hover-audio') !== 'off';

  function addHoverSoundToCards(selector) {
    if (!hoverSound) return;
    const cards = document.querySelectorAll(selector);
    cards.forEach(card => {
      card.addEventListener('mouseenter', () => {
        if (!hoverSoundEnabled) return;
        try {
          hoverSound.pause();
          hoverSound.currentTime = 0;
          hoverSound.play();
        } catch (err) {
          console.warn("⚠️ Hover sound failed:", err);
        }
      });
    });
  }

  addHoverSoundToCards('.mode-card');
  addHoverSoundToCards('.secondary-card');

  // === Theme Toggle ===
  const toggleThemeBtn = document.getElementById('toggle-theme');
  if (toggleThemeBtn) {
    toggleThemeBtn.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      const isDark = document.body.classList.contains('dark-mode');
      toggleThemeBtn.textContent = isDark ? '☀️ Light Mode' : '🌙 Dark Mode';
      localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    if (localStorage.getItem('theme') === 'dark') {
      document.body.classList.add('dark-mode');
      toggleThemeBtn.textContent = '☀️ Light Mode';
    }
  }

  // === Hover Audio Toggle ===
  const toggleAudioBtn = document.getElementById('toggle-audio');
  if (toggleAudioBtn) {
    toggleAudioBtn.textContent = hoverSoundEnabled ? '🔊 Disable Hover Audio' : '🔇 Enable Hover Audio';
    toggleAudioBtn.addEventListener('click', () => {
      hoverSoundEnabled = !hoverSoundEnabled;
      localStorage.setItem('hover-audio', hoverSoundEnabled ? 'on' : 'off');
      toggleAudioBtn.textContent = hoverSoundEnabled ? '🔊 Disable Hover Audio' : '🔇 Enable Hover Audio';
    });
  }

  // === Dropdowns (Profile & Settings) ===
  document.querySelectorAll('.dropdown').forEach(dropdown => {
    const button = dropdown.querySelector('button');
    if (!button) return;

    button.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('open');
      document.querySelectorAll('.dropdown').forEach(d => {
        if (d !== dropdown) d.classList.remove('open');
      });
    });
  });

  document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('open'));
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.dropdown').forEach(d => d.classList.remove('open'));
    }
  });

  // === Emotion Gallery (Infinite Scroll + Highlight at Center) ===
  const galleryTrack = document.querySelector('.gallery-track');
  if (galleryTrack) {
    galleryTrack.innerHTML += galleryTrack.innerHTML;
    galleryTrack.innerHTML += galleryTrack.innerHTML;

    const galleryItems = galleryTrack.querySelectorAll(".emotion-item");
    const marker = document.querySelector(".highlight-marker");

    let position = 0;
    const scrollSpeed = 0.6;
    let lastHighlighted = null;
    const trackWidth = galleryTrack.scrollWidth / 3;

    function getClosestToMarker() {
      const markerRect = marker.getBoundingClientRect();
      const markerX = markerRect.left + markerRect.width / 2;

      let closest = null;
      let closestDist = Infinity;

      galleryItems.forEach(item => {
        const rect = item.getBoundingClientRect();
        const imgCenterX = rect.left + rect.width / 2;
        const dist = Math.abs(markerX - imgCenterX);

        if (dist < closestDist) {
          closestDist = dist;
          closest = item;
        }
      });

      return closest;
    }

    function highlightImage(item) {
      if (!item || item === lastHighlighted) return;
      lastHighlighted = item;

      galleryItems.forEach(el => {
        el.classList.remove("highlighted");
        const cap = el.querySelector(".caption");
        if (cap) cap.style.opacity = "0";
      });

      item.classList.add("highlighted");
      const caption = item.querySelector(".caption");
      if (caption) caption.style.opacity = "1";

      setTimeout(() => {
        if (item === lastHighlighted) {
          item.classList.remove("highlighted");
          if (caption) caption.style.opacity = "0";
          lastHighlighted = null;
        }
      }, 1000);
    }

    function animate() {
      position -= scrollSpeed;
      if (Math.abs(position) >= trackWidth) {
        position = 0;
      }
      galleryTrack.style.transform = `translateX(${position}px)`;

      const candidate = getClosestToMarker();
      highlightImage(candidate);

      requestAnimationFrame(animate);
    }

    animate();
  }

  // === Emoji mapping for emotions ===
  const emotionEmojis = {
    "anger": "😡",
    "fear": "😨",
    "joy": "😊",
    "love": "❤️",
    "sadness": "😢",
    "surprise": "😲"
  };

  // === Quick Demo: Text Emotion Prediction ===
  const demoForm = document.getElementById('demo-form');
  const demoText = document.getElementById('demo-text');
  const demoResult = document.getElementById('demo-result');
  const resultEmotion = document.getElementById('result-emotion');
  const resultConfidence = document.getElementById('result-confidence');
  const resultTable = document.getElementById('result-table');

  if (demoForm && demoText && demoResult) {
    // Hide result section on load
    demoResult.classList.remove("show");

    demoForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const text = demoText.value.trim();

      if (!text) {
        demoResult.classList.add("show");
        resultEmotion.textContent = "⚠️ Please enter text!";
        resultConfidence.textContent = "-";
        if (resultTable) resultTable.innerHTML = "";
        return;
      }

      demoResult.classList.add("show");
      resultEmotion.textContent = "⏳ Detecting...";
      resultConfidence.textContent = "-";
      if (resultTable) resultTable.innerHTML = "";

      try {
        const response = await fetch('/demo_detect_text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text })
        });

        const data = await response.json();
        if (data.success) {
          // normalize emotion (trim + lowercase)
          const normalizedEmotion = data.emotion.trim().toLowerCase();
          const emoji = emotionEmojis[normalizedEmotion] || "❓";

          resultEmotion.textContent = `${emoji} ${data.emotion}`;
          resultConfidence.textContent = `📊 ${data.confidence}`;

          if (data.probabilities && resultTable) {
            let html = `
              <table class="prob-table">
                <thead>
                  <tr><th>Emotion</th><th>Probability (%)</th></tr>
                </thead>
                <tbody>
            `;
            Object.entries(data.probabilities).forEach(([emotion, prob]) => {
              const normalized = emotion.trim().toLowerCase();
              const emo = emotionEmojis[normalized] || "❓";
              html += `<tr>
                        <td>${emo} ${emotion}</td>
                        <td>${prob}</td>
                      </tr>`;
            });
            html += "</tbody></table>";
            resultTable.innerHTML = html;
          }
        } else {
          resultEmotion.textContent = "❌ Error";
          resultConfidence.textContent = "-";
          if (resultTable) resultTable.innerHTML = "";
        }
      } catch (err) {
        console.error("Demo error:", err);
        resultEmotion.textContent = "⚠️ Server error";
        resultConfidence.textContent = "-";
        if (resultTable) resultTable.innerHTML = "";
      }

      // Clear input after submission
      demoText.value = "";
    });
  }

  // === Card Glow Effect ===
  document.querySelectorAll('.mode-card, .secondary-card').forEach(card => {
    card.addEventListener('mouseenter', () => card.classList.add('glow'));
    card.addEventListener('mouseleave', () => card.classList.remove('glow'));
  });
});
