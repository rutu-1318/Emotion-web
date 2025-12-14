// static/js/text_detector.js
document.addEventListener("DOMContentLoaded", function () {
  // === THEME SYNC ===
  const currentTheme = localStorage.getItem("theme") || "light";
  if (currentTheme === "dark") {
    document.body.classList.add("dark-mode");
  }

  const themeToggleBtn = document.getElementById("toggle-theme");
  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      document.body.classList.toggle("dark-mode");
      const newTheme = document.body.classList.contains("dark-mode")
        ? "dark"
        : "light";
      localStorage.setItem("theme", newTheme);
    });
  }

  // === EMOTION DATA ===
  const dataElement = document.getElementById("emotion-data");
  if (!dataElement) return;

  const emotionData = JSON.parse(dataElement.textContent);
  const labels = emotionData.labels;
  const data = emotionData.probabilities;

  // === EMOJI & QUOTES MAPPING ===
  const emojiMap = {
    Anger: "😡",
    Fear: "😨",
    Joy: "😊",
    Love: "❤️",
    Sadness: "😢",
    Surprise: "😲",
  };

  const quoteMap = {
    Anger: "Take a deep breath. Let your anger flow away, peace brings clarity. 🌿",
    Fear: "Courage is not the absence of fear, but the triumph over it. 💪",
    Joy: "Happiness shared is happiness multiplied. Keep smiling! 🌸",
    Love: "Love makes the world brighter — never stop spreading it. 💖",
    Sadness: "Every storm passes, and the sun will shine again. Stay strong. ☀️",
    Surprise: "Life’s surprises are the universe’s way of keeping us excited! 🎁",
  };

  // === Find top emotion (with normalization) ===
  const maxIndex = data.indexOf(Math.max(...data));
  const rawEmotion = labels[maxIndex] || "";
  const topEmotion =
    rawEmotion.trim().charAt(0).toUpperCase() +
    rawEmotion.trim().slice(1).toLowerCase();

  console.log("Backend labels:", labels);
  console.log("Detected rawEmotion:", `"${rawEmotion}"`);
  console.log("Normalized topEmotion:", `"${topEmotion}"`);

  const topEmoji = emojiMap[topEmotion] || "❓";

  // === Update Result Section with Emoji & Confidence ===
  const resultLabel = document.querySelector(".result-label");
  if (resultLabel) {
    resultLabel.innerHTML = `
      Emotion Detected: <strong>${topEmotion} ${topEmoji}</strong><br/>
      Confidence: ${data[maxIndex].toFixed(2)}%
    `;
  }

  // === Update Quote Section ===
  const quoteSection = document.getElementById("quote-section");
  if (quoteSection) {
    const quote =
      quoteMap[topEmotion] || "Emotions guide us — listen to them wisely. 🌟";
    quoteSection.textContent = quote;
  }

  // === CHART SETUP (Bar Chart for current detection) ===
  const ctx = document.getElementById("emotionChart").getContext("2d");

  const baseGradient = (ctx) => {
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "#6dd5ed");
    gradient.addColorStop(1, "#2193b0");
    return gradient;
  };

  const highlightGradient = (ctx) => {
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "#ff758c");
    gradient.addColorStop(1, "#ff7eb3");
    return gradient;
  };

  const backgroundColors = labels.map((_, index) =>
    index === maxIndex ? highlightGradient(ctx) : baseGradient(ctx)
  );

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Emotion Probability (%)",
          data: data,
          backgroundColor: backgroundColors,
          borderRadius: 10,
          borderSkipped: false,
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      animation: {
        duration: 1000,
        easing: "easeOutQuart",
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => `${context.parsed.y.toFixed(2)}%`,
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#333",
            font: { size: 14 },
          },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20,
            color: "#444",
            font: { size: 13 },
            callback: (value) => `${value}%`,
          },
          grid: {
            color: "#e0e0e0",
            borderDash: [4, 4],
          },
        },
      },
    },
  });
});
