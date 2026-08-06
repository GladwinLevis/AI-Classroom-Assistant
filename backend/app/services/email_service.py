import logging
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class EmailProvider(ABC):
    """Abstract base class for email providers (SMTP, SendGrid, Resend, etc.)."""

    @abstractmethod
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email to the specified recipient. Returns True on success."""
        pass


class SMTPEmailProvider(EmailProvider):
    """
    SMTP email provider supporting Gmail SMTP, SendGrid SMTP relay, Resend SMTP,
    and any standard SMTP server.

    Configuration via environment variables:
        SMTP_HOST       - SMTP server hostname (e.g. smtp.gmail.com, smtp.sendgrid.net)
        SMTP_PORT       - SMTP port (default 587 for STARTTLS)
        SMTP_USERNAME   - Authentication username
        SMTP_PASSWORD   - Authentication password / app password
        SMTP_FROM_EMAIL - Sender email address
        SMTP_USE_TLS    - Whether to use STARTTLS (default "true")
    """

    def __init__(self):
        self.host = os.getenv("SMTP_HOST", "")
        self.port = int(os.getenv("SMTP_PORT", "587"))
        self.username = os.getenv("SMTP_USERNAME", "")
        self.password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@aiclassroom.app")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    async def send_email(self, to: str, subject: str, body: str) -> bool:
        if not self.host or not self.username:
            logger.warning(
                "SMTP not configured (SMTP_HOST or SMTP_USERNAME missing). "
                "Email to %s was not sent.", to
            )
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html", "utf-8"))

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)

            logger.info("Email sent successfully to %s (subject: %s)", to, subject)
            return True
        except Exception as e:
            logger.error("Failed to send email to %s: %s", to, str(e))
            return False


class EmailService:
    """
    High-level email service used throughout the application.
    Supports pluggable providers (SMTP, SendGrid API, Resend API, etc.).
    """

    def __init__(self, provider: EmailProvider | None = None):
        self._provider: EmailProvider = provider or SMTPEmailProvider()

    async def send_verification_otp(self, email: str, otp: str) -> bool:
        """Sends a verification OTP email to the specified address."""
        subject = "AI Classroom Assistant — Your Verification Code"
        body = (
            "<div style='font-family: sans-serif; max-width: 480px; margin: auto;'>"
            "<h2 style='color: #6366f1;'>Verification Code</h2>"
            f"<p>Your one-time verification code is:</p>"
            f"<p style='font-size: 32px; font-weight: bold; letter-spacing: 4px; "
            f"color: #1e293b; background: #f1f5f9; padding: 16px; border-radius: 8px; "
            f"text-align: center;'>{otp}</p>"
            "<p>This code expires in <strong>5 minutes</strong>.</p>"
            "<p style='color: #64748b; font-size: 13px;'>If you did not request this, "
            "please ignore this email.</p>"
            "</div>"
        )
        return await self._provider.send_email(email, subject, body)

    async def send_password_reset(self, email: str, reset_token: str) -> bool:
        """Sends a password reset email to the specified address."""
        subject = "AI Classroom Assistant — Password Reset"
        body = (
            "<div style='font-family: sans-serif; max-width: 480px; margin: auto;'>"
            "<h2 style='color: #6366f1;'>Password Reset</h2>"
            f"<p>Your password reset code is:</p>"
            f"<p style='font-size: 32px; font-weight: bold; letter-spacing: 4px; "
            f"color: #1e293b; background: #f1f5f9; padding: 16px; border-radius: 8px; "
            f"text-align: center;'>{reset_token}</p>"
            "<p>This code expires in <strong>5 minutes</strong>.</p>"
            "</div>"
        )
        return await self._provider.send_email(email, subject, body)
