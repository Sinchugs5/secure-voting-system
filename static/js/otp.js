// static/js/otp.js
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("verifyForm");
    form.addEventListener("submit", async function (e) {
      e.preventDefault();
      const email = document.getElementById("email").value;
      const otp = document.getElementById("otp").value;
  
      const resp = await fetch("/auth/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });
  
      const data = await resp.json();
      if (resp.ok) {
        // OTP verified: redirect to vote page (change if you want another page)
        window.location.href = "/vote.html"; // adjust to your route (or '/vote')
        // If your app uses a different route, replace above with correct path.
      } else {
        alert(data.error || data.message || "OTP verification failed");
      }
    });
  });
  