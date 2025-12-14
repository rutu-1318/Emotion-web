// ==========================
// FACE DETECTOR JS (FINAL UPDATED + LIVE EMOJI FIX)
// ==========================

// ---- DOM Elements ----
const video = document.getElementById("video");
const emotionLabel = document.getElementById("emotionLabel");
const emotionBar = document.getElementById("emotionBar");
const emoji = document.getElementById("emoji");
const emotionType = document.getElementById("emotionType");

const topEmoji = document.getElementById("topEmoji");
const quoteSection = document.getElementById("quote-section");

const uploadCard = document.getElementById("uploadCard");
const webcamCard = document.getElementById("webcamCard");

let stream = null;
let intervalId = null;
let paused = false;

// ======================
// Emotion → Emoji
// ======================
const emojiMap = {
    Anger: "😡",
    Fear: "😨",
    Joy: "😊",
    Love: "❤️",
    Sadness: "😢",
    Surprise: "😲",
    Neutral: "😐"
};

// ======================
// Emotion → Quote
// ======================
const quoteMap = {
    Anger: "Take a deep breath. Let your anger flow away, peace brings clarity. 🌿",
    Fear: "Courage is not the absence of fear, but the triumph over it. 💪",
    Joy: "Happiness shared is happiness multiplied. Keep smiling! 🌸",
    Love: "Love makes the world brighter — never stop spreading it. 💖",
    Sadness: "Every storm passes, and the sun will shine again. Stay strong. ☀️",
    Surprise: "Life’s surprises are the universe’s way of keeping us excited! 🎁",
    Neutral: "Calm mind, steady heart. You're balanced today. 🌱"
};

// ======================
// THEME SYNC (Dark Mode)
// ======================
document.addEventListener("DOMContentLoaded", () => {
    const savedTheme = localStorage.getItem("theme") || "light";
    if (savedTheme === "dark") document.body.classList.add("dark-mode");

    const themeToggleBtn = document.getElementById("toggle-theme-btn");
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            document.body.classList.toggle("dark-mode");
            localStorage.setItem(
                "theme",
                document.body.classList.contains("dark-mode") ? "dark" : "light"
            );
        });
    }
});

// ======================
// Toggle Between Upload / Webcam
// ======================
function toggleMethod(method) {
    const buttons = document.querySelectorAll(".toggle-buttons button");

    buttons.forEach(btn => btn.classList.remove("active-mode"));

    if (method === "webcam") {
        buttons[0].classList.add("active-mode");

        uploadCard.classList.remove("active");
        webcamCard.classList.add("active");

        startWebcam();

    } else {
        buttons[1].classList.add("active-mode");

        webcamCard.classList.remove("active");
        uploadCard.classList.add("active");

        stopWebcam();
    }
}

window.activateWebcamMode = () => toggleMethod("webcam");
window.useUpload = () => toggleMethod("upload");

// ======================
// Webcam Start / Stop
// ======================
async function startWebcam() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
        paused = false;

        if (!intervalId) detectEmotionLive();
    } catch (error) {
        console.error("Webcam error:", error);
    }
}

function stopWebcam() {
    if (stream) {
        stream.getTracks().forEach(t => t.stop());
        stream = null;
    }

    clearInterval(intervalId);
    intervalId = null;
    paused = false;
    video.srcObject = null;

    // Reset UI
    emoji.textContent = "😊";
    emotionLabel.textContent = "Neutral";
    emotionBar.style.width = "0%";
    emotionType.textContent = "";
}

window.beginWebcamStream = startWebcam;
window.stopWebcam = stopWebcam;
window.pauseWebcam = () => (paused = true);
window.resumeWebcam = () => (paused = false);

// ======================
// Real-time Emotion Detection
// ======================
function detectEmotionLive() {
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    intervalId = setInterval(async () => {
        if (!video.videoWidth || paused) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const base64Image = canvas.toDataURL("image/jpeg");

        try {
            const response = await fetch("/webcam_face_live", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ image: base64Image })
            });

            const result = await response.json();

            if (result.success && result.emotion) {
                updateWebcamUI(result.emotion, result.confidence);
            }
        } catch (err) {
            console.error("Emotion detect error:", err);
        }
    }, 1200);
}

// ======================
// Update Webcam UI (Emoji + Quote LIVE)
// ======================
function updateWebcamUI(emotion, confidence = 0) {
    const normalizedEmotion =
        emotion.trim().charAt(0).toUpperCase() +
        emotion.trim().slice(1).toLowerCase();

    const emojiChar = emojiMap[normalizedEmotion] || "❓";

    // LIVE UI Update
    emoji.textContent = emojiChar;
    emotionLabel.textContent = normalizedEmotion;
    emotionBar.style.width = `${confidence * 100}%`;
    emotionType.textContent = `${emojiChar} ${normalizedEmotion} (${(confidence ).toFixed(1)}%)`;

    // LIVE quote update
    if (quoteSection) {
        quoteSection.textContent = quoteMap[normalizedEmotion] || "Stay mindful. 🌟";
    }
}

// ======================
// Upload Image Result Chart
// ======================
document.addEventListener("DOMContentLoaded", () => {
    const dataScript = document.getElementById("emotion-data");
    if (!dataScript) return;

    const { labels, probabilities } = JSON.parse(dataScript.textContent);

    const formattedLabels = labels.map(l =>
        l.trim().charAt(0).toUpperCase() + l.trim().slice(1).toLowerCase()
    );

    const maxIndex = probabilities.indexOf(Math.max(...probabilities));
    const topEmotion = formattedLabels[maxIndex];

    if (topEmoji) topEmoji.textContent = emojiMap[topEmotion] || "❓";

    if (quoteSection)
        quoteSection.textContent =
            quoteMap[topEmotion] ||
            "Emotions guide us — listen to them wisely. 🌟";

    // ---- Chart ----
    const ctx = document.getElementById("emotionChart").getContext("2d");

    new Chart(ctx, {
        type: "bar",
        data: {
            labels: formattedLabels,
            datasets: [
                {
                    label: "Emotion Probability (%)",
                    data: probabilities.map(v => v * 100),
                    backgroundColor: formattedLabels.map((_, i) =>
                        i === maxIndex ? "#ff7eb3" : "#6dd5ed"
                    ),
                    borderRadius: 12
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: v => `${v}%`
                    }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
});
