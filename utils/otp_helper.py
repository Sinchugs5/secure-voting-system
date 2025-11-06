# utils/otp_helper.py
import random

def generate_otp() -> str:
    """
    Generate a 6-digit OTP as a string.
    Example: "034521"
    """
    return f"{random.randint(0, 999999):06d}"

def send_otp_email(to_email, otp):
    """
    Send OTP email using Flask-Mail.
    The import of `app` and `mail` is local to avoid circular imports.
    """
    from app import app, mail
    from flask_mail import Message

    try:
        msg = Message(
            subject="Your OTP",
            sender=app.config['MAIL_USERNAME'],
            recipients=[to_email],
            body=f"Your OTP is: {otp}"
        )
        mail.send(msg)
        return True
    except Exception as e:
        print("Error sending OTP email:", e)
        return False
