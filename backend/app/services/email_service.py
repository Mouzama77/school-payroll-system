"""SMTP email delivery service.

Sends transactional emails (currently password-reset OTPs). Designed to be
safe for local development: when SMTP is not configured or EMAIL_DEV_MODE is
enabled, the email is logged to the console instead of being sent, so the
flow remains fully testable without a mail server.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_otp_html(otp: str, expire_minutes: int) -> str:
    """Return a professional, self-contained HTML email for an OTP."""
    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Password Reset Code</title>
</head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:32px 0;">
    <tr>
      <td align="center">
        <table role="presentation" width="480" cellpadding="0" cellspacing="0"
               style="background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 12px rgba(15,23,42,0.08);">
          <tr>
            <td style="background:linear-gradient(135deg,#2563eb,#1e40af);padding:28px 32px;">
              <h1 style="margin:0;color:#ffffff;font-size:20px;font-weight:700;">
                {settings.EMAIL_FROM_NAME}
              </h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              <h2 style="margin:0 0 12px 0;color:#0f172a;font-size:18px;">Password reset code</h2>
              <p style="margin:0 0 20px 0;color:#475569;font-size:14px;line-height:1.6;">
                We received a request to reset your password. Enter the verification
                code below to continue. This code expires in
                <strong>{expire_minutes} minutes</strong>.
              </p>
              <div style="text-align:center;margin:24px 0;">
                <span style="display:inline-block;background-color:#eff6ff;color:#1d4ed8;
                             font-size:34px;font-weight:700;letter-spacing:10px;
                             padding:16px 28px;border-radius:12px;border:1px solid #bfdbfe;">
                  {otp}
                </span>
              </div>
              <p style="margin:0 0 8px 0;color:#475569;font-size:13px;line-height:1.6;">
                If you did not request a password reset, you can safely ignore this
                email — your password will remain unchanged.
              </p>
              <p style="margin:20px 0 0 0;color:#94a3b8;font-size:12px;line-height:1.6;">
                For your security, never share this code with anyone. Our team will
                never ask you for it.
              </p>
            </td>
          </tr>
          <tr>
            <td style="background-color:#f8fafc;padding:18px 32px;border-top:1px solid #e2e8f0;">
              <p style="margin:0;color:#94a3b8;font-size:12px;">
                &copy; {settings.EMAIL_FROM_NAME}. This is an automated message.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def _build_otp_text(otp: str, expire_minutes: int) -> str:
    return (
        f"{settings.EMAIL_FROM_NAME} - Password reset code\n\n"
        f"Your verification code is: {otp}\n"
        f"This code expires in {expire_minutes} minutes.\n\n"
        "If you did not request a password reset, you can ignore this email.\n"
        "Never share this code with anyone."
    )


class EmailService:
    @staticmethod
    def _send(to_email: str, subject: str, html_body: str, text_body: str) -> None:
        """Low-level send. Falls back to console logging in dev mode."""
        if settings.EMAIL_DEV_MODE or not settings.smtp_configured:
            logger.warning(
                "[EMAIL DEV MODE] To=%s | Subject=%s\n%s",
                to_email,
                subject,
                text_body,
            )
            return

        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = formataddr(
            (settings.EMAIL_FROM_NAME, settings.EMAIL_FROM)
        )
        message["To"] = to_email
        message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        try:
            if settings.SMTP_USE_SSL:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    settings.SMTP_HOST, settings.SMTP_PORT, context=context, timeout=15
                ) as server:
                    if settings.SMTP_USERNAME:
                        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.sendmail(settings.EMAIL_FROM, [to_email], message.as_string())
            else:
                with smtplib.SMTP(
                    settings.SMTP_HOST, settings.SMTP_PORT, timeout=15
                ) as server:
                    server.ehlo()
                    if settings.SMTP_USE_TLS:
                        context = ssl.create_default_context()
                        server.starttls(context=context)
                        server.ehlo()
                    if settings.SMTP_USERNAME:
                        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.sendmail(settings.EMAIL_FROM, [to_email], message.as_string())
            logger.info("Sent email to %s (subject=%s)", to_email, subject)
        except Exception as exc:  # noqa: BLE001 - log and swallow in background task
            # Runs inside a BackgroundTask; raising would be silently dropped
            # by Starlette, so log with full context for observability.
            logger.error("Failed to send email to %s: %s", to_email, exc)

    @staticmethod
    def send_password_reset_otp(to_email: str, otp: str) -> None:
        """Send the password-reset OTP email."""
        expire_minutes = settings.OTP_EXPIRE_MINUTES
        EmailService._send(
            to_email=to_email,
            subject="Your password reset code",
            html_body=_build_otp_html(otp, expire_minutes),
            text_body=_build_otp_text(otp, expire_minutes),
        )
