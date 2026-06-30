import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_reset_password_email(email: str, token: str):
    """
    Send a password reset email to the user.
    Uses Brevo HTTP API if BREVO_API_KEY is configured (bypasses Render port blocks).
    Otherwise, falls back to SMTP, and then console logging (Mock mode).
    """
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    # 1. Try Brevo HTTP API (Best for Render Free Tier since it uses Port 443 HTTPS - never blocked!)
    if settings.BREVO_API_KEY:
        logger.info("BREVO_API_KEY detected. Sending email via Brevo HTTP API...")
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY,
            "content-type": "application/json"
        }
        data = {
            "sender": {
                "name": "FinSense Team",
                "email": settings.SMTP_FROM_EMAIL or "spancersam518@gmail.com"
            },
            "to": [
                {
                    "email": email
                }
            ],
            "subject": "Reset Your Password - FinSense",
            "textContent": f"""Hello,

You requested a password reset for your FinSense account.
Click the link below to set a new password. This link is valid for 15 minutes:

{reset_link}

If you did not request this, please ignore this email.

Best regards,
The FinSense Team"""
        }
        try:
            response = httpx.post(url, headers=headers, json=data, timeout=10.0)
            if response.status_code in [200, 201, 202]:
                logger.info("Real recovery email successfully sent via Brevo HTTP API to %s", email)
                return
            else:
                logger.error("Failed to send email via Brevo HTTP API (Status %s): %s", response.status_code, response.text)
        except Exception as exc:
            logger.error("Exception occurred sending email via Brevo HTTP API: %s", exc)
        
        logger.warning("Brevo HTTP API failed. Falling back to SMTP/Console.")

    # 2. Try SMTP
    if all([
        settings.SMTP_HOST,
        settings.SMTP_USERNAME,
        settings.SMTP_PASSWORD,
        settings.SMTP_FROM_EMAIL,
    ]):
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

            logger.info("Real recovery email successfully sent via SMTP to %s", email)
            return
        except Exception as exc:
            logger.error("Failed to send SMTP email: %s. Fallback to console logging.", exc)

    # 3. Fallback to console logging (Mock mode / Local development)
    print(
        "\n=======================================================\n"
        "PASSWORD RESET FALLBACK EMAIL:\n"
        f"To:   {email}\n"
        f"Link: {reset_link}\n"
        "=======================================================\n"
    )
