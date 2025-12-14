// ===============================
// Login Page Logic
// ===============================

// Form submission handler
document.addEventListener("DOMContentLoaded", () => {
  const loginForm = document.getElementById("loginForm");
  if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      await loginUser();
    });
  }
});

// Login function
async function loginUser() {
  const identifier = document.querySelector("input[name='identifier']").value.trim();
  const password = document.querySelector("input[name='password']").value.trim();

  if (!identifier) {
    showToast("⚠️ Please enter your email, phone, or username.", "error");
    return;
  }
  if (!password) {
    showToast("⚠️ Please enter your password.", "error");
    return;
  }

  try {
    const response = await fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, password })
    });

    const result = await response.json();
    if (result.success) {
      showToast("✅ Login successful! Redirecting...", "success");
      setTimeout(() => {
        window.location.href = "/home"; // redirect after success
      }, 1200);
    } else {
      showToast(result.message || "❌ Invalid credentials.", "error");
    }
  } catch (err) {
    showToast("⚠️ Server error. Please try again later.", "error");
  }
}

// Show Reset Password Modal
function showResetModal() {
  const modal = document.getElementById("resetModal");
  modal.style.display = "flex";
  document.getElementById("reset-msg").innerText = "";
  document.getElementById("otpSection").style.display = "none";

  // Clear previous values
  ["reset-username", "reset-otp", "new-password"].forEach(id => {
    document.getElementById(id).value = "";
  });
}

// Close Reset Modal
function closeResetModal() {
  document.getElementById("resetModal").style.display = "none";
}

// Send Reset OTP
async function sendResetOTP() {
  const identifier = document.getElementById("reset-username").value.trim();
  const msg = document.getElementById("reset-msg");

  if (!identifier) {
    msg.innerText = "⚠️ Please enter your email or phone number.";
    msg.style.color = "red";
    return;
  }

  try {
    const response = await fetch("/send_reset_otp", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier })
    });

    const result = await response.json();
    if (result.success) {
      msg.innerText = "✅ OTP sent successfully!";
      msg.style.color = "green";
      document.getElementById("otpSection").style.display = "block";
    } else {
      msg.innerText = result.message || "❌ Failed to send OTP.";
      msg.style.color = "red";
    }
  } catch (err) {
    msg.innerText = "⚠️ Error connecting to server.";
    msg.style.color = "red";
  }
}

// Reset Password
async function resetPassword() {
  const identifier = document.getElementById("reset-username").value.trim();
  const otp = document.getElementById("reset-otp").value.trim();
  const newPassword = document.getElementById("new-password").value.trim();
  const msg = document.getElementById("reset-msg");

  if (!otp || !newPassword) {
    msg.innerText = "⚠️ Please enter OTP and new password.";
    msg.style.color = "red";
    return;
  }

  try {
    const response = await fetch("/reset_password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier, otp, new_password: newPassword })
    });

    const result = await response.json();
    if (result.success) {
      msg.innerText = "✅ Password reset successful!";
      msg.style.color = "green";
      setTimeout(closeResetModal, 1500);
    } else {
      msg.innerText = result.message || "❌ Failed to reset password.";
      msg.style.color = "red";
    }
  } catch (err) {
    msg.innerText = "⚠️ Server error. Please try again.";
    msg.style.color = "red";
  }
}

// ===============================
// Toast Notifications (Small popup alerts)
// ===============================
function showToast(message, type = "info") {
  let toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("show");
  }, 100);

  setTimeout(() => {
    toast.classList.remove("show");
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}
