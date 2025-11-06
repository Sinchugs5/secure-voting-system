# routes/otp_routes.py
from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from utils.otp_helper import generate_otp, send_otp_email
import time

otp_bp = Blueprint("otp_bp", __name__, template_folder="../templates")

# OTP settings
OTP_TTL_SECONDS = 300  # 5 minutes
otp_store = {}  # In-memory store: { email: {otp, expires} }

# ---------------- Step 1: Send OTP ----------------
@otp_bp.route("/send-otp", methods=["POST"])
def send_otp_route():
    """
    Accepts JSON or form with { "email": "user@example.com" }.
    Generates OTP, stores it, sends email, sets session["pending_otp_email"].
    """
    data = request.get_json() or request.form
    email = data.get("email")
    if not email:
        if request.is_json:
            return jsonify({"error": "email_required"}), 400
        flash("Email is required!", "error")
        return redirect(url_for("student_login"))

    otp = generate_otp()
    otp_store[email] = {"otp": otp, "expires": time.time() + OTP_TTL_SECONDS}
    
    success = send_otp_email(email, otp)
    if not success:
        otp_store.pop(email, None)
        if request.is_json:
            return jsonify({"error": "failed_to_send"}), 500
        flash("Failed to send OTP. Try again.", "error")
        return redirect(url_for("student_login"))

    session["pending_otp_email"] = email

    if request.is_json:
        return jsonify({"message": "otp_sent"}), 200
    flash("OTP sent to your email!", "success")
    return redirect(url_for("otp_bp.otp_page"))

# ---------------- Step 2: Verify OTP ----------------
@otp_bp.route("/verify-otp", methods=["POST"])
def verify_otp_route():
    """
    Accepts JSON or form { "email": "...", "otp": "123456" }.
    On success, sets session["otp_verified_<email>"] = True.
    """
    data = request.get_json() or request.form
    email = data.get("email") or session.get("pending_otp_email")
    otp = data.get("otp")

    if not email or not otp:
        if request.is_json:
            return jsonify({"error": "email_and_otp_required"}), 400
        flash("Email and OTP are required!", "error")
        return redirect(url_for("otp_bp.otp_page"))

    rec = otp_store.get(email)
    if not rec:
        if request.is_json:
            return jsonify({"error": "no_otp_found_or_expired"}), 400
        flash("No OTP found or expired. Please request again.", "error")
        return redirect(url_for("student_login"))

    if time.time() > rec["expires"]:
        otp_store.pop(email, None)
        if request.is_json:
            return jsonify({"error": "otp_expired"}), 400
        flash("OTP expired. Please request again.", "error")
        return redirect(url_for("student_login"))

    if str(rec["otp"]).strip() == str(otp).strip():
        session[f"otp_verified_{email}"] = True
        otp_store.pop(email, None)
        if request.is_json:
            return jsonify({"message": "otp_verified"}), 200
        flash("OTP verified successfully!", "success")
        return redirect(url_for("voter_details"))  # redirect to voter details
    else:
        if request.is_json:
            return jsonify({"error": "invalid_otp"}), 400
        flash("Invalid OTP!", "error")
        return render_template("otp_verify.html", email=email)

# ---------------- Step 3: OTP input page ----------------
@otp_bp.route("/otp", methods=["GET"])
def otp_page():
    """
    Renders a small page where user can input OTP.
    Pre-fills email from session or query param.
    """
    email = request.args.get("email") or session.get("pending_otp_email", "")
    return render_template("otp_verify.html", email=email)
