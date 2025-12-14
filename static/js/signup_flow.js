// =======================================================
//  SIGNUP FLOW – CLEAN & POLISHED VERSION (WITH GUEST MODE)
// =======================================================

// -------------------------------------------
//  Toast Notification
// -------------------------------------------
function showToast(message, type = "error") {
  let toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.textContent = message;

  const container = document.querySelector(".signup-card") || document.body;
  container.appendChild(toast);

  setTimeout(() => toast.classList.add("show"), 50);

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// -------------------------------------------
//  Button Loading Effect
// -------------------------------------------
function setLoading(button, isLoading) {
  if (!button) return;

  if (isLoading) {
    button.dataset.originalText = button.textContent;
    button.textContent = "Processing...";
    button.disabled = true;
  } else {
    button.textContent = button.dataset.originalText || button.textContent;
    button.disabled = false;
  }
}

// -------------------------------------------
//  Step Switching
// -------------------------------------------
function goToStep(stepId) {
  document.querySelectorAll(".step").forEach((step) => {
    step.style.display = "none";
    step.classList.remove("active");
    step.classList.add("hidden");
  });

  const target = document.getElementById(stepId);
  if (target) {
    target.classList.remove("hidden");
    target.style.display = "block";
    target.classList.add("active");
  }
}

function backToStep1() {
  goToStep("step1");
}

// =======================================================
//  EMAIL FLOW
// =======================================================
function sendEmailOTP(event) {
  const email = document.getElementById("emailInput").value.trim();
  const btn = event.target;

  if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
    showToast("Please enter a valid email address.");
    return;
  }

  setLoading(btn, true);

  fetch("/send_email_otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("showEmail").textContent = email;
        document.getElementById("finalEmail").value = email;
        document.getElementById("finalProvider").value = "email";
        goToStep("step2");
      } else {
        showToast(data.error || "Failed to send email OTP.");
      }
    })
    .finally(() => setLoading(btn, false));
}

function verifyEmailOTP(event) {
  const otp = document.getElementById("emailOtpInput").value.trim();
  const email = document.getElementById("finalEmail").value;
  const btn = event.target;

  if (!otp || otp.length < 4) {
    showToast("Please enter a valid OTP.");
    return;
  }

  setLoading(btn, true);

  fetch("/verify_email_otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, otp }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        goToStep("step4");
      } else {
        showToast(data.error || "Invalid OTP.");
      }
    })
    .finally(() => setLoading(btn, false));
}

// =======================================================
//  PHONE FLOW
// =======================================================
function sendPhoneOTP(event) {
  const phone = document.getElementById("phoneInput").value.trim();
  const btn = event.target;

  if (!/^\d{10}$/.test(phone)) {
    showToast("Please enter a valid 10-digit phone number.");
    return;
  }

  setLoading(btn, true);

  fetch("/send_phone_otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        document.getElementById("showPhone").textContent = phone;
        document.getElementById("finalPhone").value = phone;
        document.getElementById("finalProvider").value = "phone";
        goToStep("step3");
      } else {
        showToast(data.error || "Failed to send phone OTP.");
      }
    })
    .finally(() => setLoading(btn, false));
}

function verifyPhoneOTP(event) {
  const otp = document.getElementById("phoneOtpInput").value.trim();
  const phone = document.getElementById("finalPhone").value;
  const btn = event.target;

  if (!otp || otp.length < 4) {
    showToast("Please enter a valid OTP.");
    return;
  }

  setLoading(btn, true);

  fetch("/verify_phone_otp", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, otp }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        goToStep("step4");
      } else {
        showToast(data.error || "Invalid OTP.");
      }
    })
    .finally(() => setLoading(btn, false));
}

// =======================================================
//  GOOGLE SIGNUP
// =======================================================
function googleSignupDirect() {
  showToast("Redirecting to Google...", "info");
  document.getElementById("finalProvider").value = "google";
  setTimeout(() => {
    window.location.href = "/google_login";
  }, 700);
}

// =======================================================
//  FINAL SIGNUP SUBMISSION
// =======================================================
function submitFinalDetails(event) {
  event.preventDefault();

  const username = document.getElementById("username").value.trim();
  const nickname = document.getElementById("nickname").value.trim();
  const password = document.getElementById("password").value.trim();
  const provider = document.getElementById("finalProvider").value;
  const email = document.getElementById("finalEmail").value;
  const phone = document.getElementById("finalPhone").value;

  if (!username || !password) {
    showToast("Username and password are required.");
    return;
  }

  fetch("/complete_signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      username,
      nickname,
      password,
      provider,
      email,
      phone,
    }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showToast("Signup successful!", "success");
        setTimeout(() => (window.location.href = "/login"), 1200);
      } else {
        showToast(data.error || "Signup failed.");
      }
    });
}

// Attach form event
document.getElementById("step4")?.addEventListener("submit", submitFinalDetails);

// =======================================================
//  GUEST MODE
// =======================================================
function continueAsGuest() {
  window.location.href = "/guest-login";
}
