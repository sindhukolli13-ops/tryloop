"""
Email service — sends verification and password reset emails via SMTP.
Uses the 'emails' library with settings from core.config.
"""

import logging

import emails
from emails.template import JinjaTemplate

from core.config import settings

logger = logging.getLogger(__name__)


def _send_email(to: str, subject: str, html_body: str) -> bool:
    """
    Send an email via SMTP. Returns True on success, False on failure.
    Logs errors but does not raise — callers should handle gracefully.
    """
    if not settings.SMTP_HOST:
        logger.warning("SMTP not configured — skipping email to %s: %s", to, subject)
        return False

    message = emails.Message(
        subject=subject,
        html=JinjaTemplate(html_body),
        mail_from=(settings.EMAIL_FROM, "Tryloop"),
    )

    response = message.send(
        to=to,
        smtp={
            "host": settings.SMTP_HOST,
            "port": settings.SMTP_PORT,
            "user": settings.SMTP_USER,
            "password": settings.SMTP_PASSWORD,
            "tls": True,
        },
    )

    if response.status_code not in (250, None):
        logger.error("Failed to send email to %s: %s", to, response.error)
        return False

    logger.info("Email sent to %s: %s", to, subject)
    return True


def send_verification_email(to: str, name: str, token: str) -> bool:
    """Send an email verification link to a new user."""
    verify_url = f"{settings.NEXTAUTH_URL}/auth/verify?token={token}"
    html = f"""
    <h2>Welcome to Tryloop, {name}!</h2>
    <p>Please verify your email address by clicking the link below:</p>
    <p><a href="{verify_url}" style="
        display: inline-block;
        padding: 12px 24px;
        background-color: #1a1a1a;
        color: #ffffff;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 500;
    ">Verify Email</a></p>
    <p>This link expires in 24 hours.</p>
    <p>If you didn't create an account, you can ignore this email.</p>
    <br>
    <p>— Tryloop</p>
    """
    return _send_email(to, "Verify your Tryloop account", html)


def send_password_reset_email(to: str, name: str, token: str) -> bool:
    """Send a password reset link."""
    reset_url = f"{settings.NEXTAUTH_URL}/auth/reset-password?token={token}"
    html = f"""
    <h2>Password Reset</h2>
    <p>Hi {name}, we received a request to reset your password.</p>
    <p><a href="{reset_url}" style="
        display: inline-block;
        padding: 12px 24px;
        background-color: #1a1a1a;
        color: #ffffff;
        text-decoration: none;
        border-radius: 6px;
        font-weight: 500;
    ">Reset Password</a></p>
    <p>This link expires in 1 hour.</p>
    <p>If you didn't request this, you can safely ignore this email.</p>
    <br>
    <p>— Tryloop</p>
    """
    return _send_email(to, "Reset your Tryloop password", html)
