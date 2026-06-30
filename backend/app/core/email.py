import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_reset_password_email(email: str, token: str):
    """
    Send a password reset email to the user.
    If SMTP variables are not configured, logs the recovery link to the console (Mock mode).
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    # 1. Fallback to console logging if SMTP settings are missing
    if not all([
        settings.SMTP_HOST,
        settings.SMTP_USERNAME,
        settings.SMTP_PASSWORD,
        settings.SMTP_FROM_EMAIL,
    ]):
        logger.warning("SMTP not configured. Logging recovery link to console (Mock mode).")
        print(
            "\n=======================================================\n"
            "PASSWORD RESET MOCK EMAIL:\n"
            f"To:   {email}\n"
            f"Link: {reset_link}\n"
            "=======================================================\n"
        )
        return

    # 2. Real SMTP email sending
    try:
        msg = MIMEMultipart()
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = email
        msg["Subject"] = "Reset Your Password - FinSense"

        body = f"""Hello,

You requested a password reset for your FinSense account.
Click the link below to set a new password. This link is valid for 15 minutes:

{reset_link}

If you did not request this, please ignore this email.

Best regards,
The FinSense Team"""
        
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, email, msg.as_string())

        logger.info("Real recovery email successfully sent to %s", email)
    except Exception as exc:
        logger.error("Failed to send SMTP email: %s. Fallback to console logging.", exc)
        print(
            "\n=======================================================\n"
            "PASSWORD RESET FALLBACK EMAIL (SMTP FAILED):\n"
            f"To:   {email}\n"
            f"Link: {reset_link}\n"
            "=======================================================\n"
        )
