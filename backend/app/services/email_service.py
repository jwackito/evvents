"""Email sending abstraction with pluggable providers.

Providers are configured via ``EMAIL_PROVIDER`` env var:

``console`` (default)
    Logs email content to structured logs. No external service needed.
    Perfect for development.

``resend``
    Uses Resend API (https://resend.com). Set ``EMAIL_API_KEY`` to your
    Resend API key. Resend handles SPF, DKIM, and domain reputation.

``mailgun``
    Uses Mailgun API (https://mailgun.com). Set ``EMAIL_API_KEY`` to your
    Mailgun API key. The sender domain is derived from ``EMAIL_FROM``.

``smtp``
    Uses standard SMTP with STARTTLS. Configure ``EMAIL_SMTP_HOST``,
    ``EMAIL_SMTP_PORT`` (default 587), ``EMAIL_SMTP_USER``, and
    ``EMAIL_SMTP_PASSWORD``.

Usage from application code::

    from app.tasks.email_tasks import send_magic_link

    send_magic_link(email="user@example.com", token="...", base_url="https://evvents.io")

The function enqueues an RQ job so email sending does not block the
request-response cycle. The actual provider delivery happens in the
background worker.
"""

from __future__ import annotations

import json
import smtplib
import structlog
from email.mime.text import MIMEText
from urllib import request as urllib_request

from flask import current_app

logger = structlog.get_logger()


def send_email(to: str, subject: str, body: str) -> dict:
    provider = current_app.config.get("EMAIL_PROVIDER", "console")

    if provider == "console":
        return _send_console(to, subject, body)
    elif provider == "resend":
        return _send_resend(to, subject, body)
    elif provider == "mailgun":
        return _send_mailgun(to, subject, body)
    elif provider == "smtp":
        return _send_smtp(to, subject, body)
    else:
        logger.warning("unknown_email_provider", provider=provider)
        return _send_console(to, subject, body)


def send_magic_link_email(email: str, token: str, base_url: str | None = None) -> dict:
    base_url = base_url or current_app.config.get("APP_BASE_URL", "http://localhost:5000")
    link = f"{base_url}/api/v1/auth/magic-link/verify?token={token}"
    subject = "Sign in to Evvents"
    body = f"""Sign in to Evvents

Click the link below to sign in:

{link}

This link expires in 15 minutes.

If you didn't request this, you can ignore this email.
"""
    return send_email(email, subject, body)


def _send_console(to: str, subject: str, body: str) -> dict:
    logger.info("email_console", to=to, subject=subject, body_preview=body[:200])
    return {"provider": "console", "message_id": None}


def _send_smtp(to: str, subject: str, body: str) -> dict:
    host = current_app.config.get("EMAIL_SMTP_HOST", "")
    port = current_app.config.get("EMAIL_SMTP_PORT", 587)
    user = current_app.config.get("EMAIL_SMTP_USER", "")
    password = current_app.config.get("EMAIL_SMTP_PASSWORD", "")
    from_addr = current_app.config.get("EMAIL_FROM", "noreply@evvents.io")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        if user:
            server.login(user, password)
        server.send_message(msg)

    logger.info("email_smtp_sent", to=to, subject=subject)
    return {"provider": "smtp", "message_id": None}


def _send_resend(to: str, subject: str, body: str) -> dict:
    api_key = current_app.config.get("EMAIL_API_KEY", "")
    from_addr = current_app.config.get("EMAIL_FROM", "noreply@evvents.io")

    payload = json.dumps({
        "from": from_addr,
        "to": to,
        "subject": subject,
        "text": body,
    }).encode()

    req = urllib_request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    resp = urllib_request.urlopen(req)
    result = json.loads(resp.read().decode())

    logger.info("email_resend_sent", to=to, subject=subject, message_id=result.get("id"))
    return {"provider": "resend", "message_id": result.get("id")}


def _send_mailgun(to: str, subject: str, body: str) -> dict:
    api_key = current_app.config.get("EMAIL_API_KEY", "")
    from_addr = current_app.config.get("EMAIL_FROM", "noreply@evvents.io")
    domain = from_addr.split("@")[1]

    import base64

    credentials = base64.b64encode(f"api:{api_key}".encode()).decode()

    payload = (
        f"from={from_addr}&to={to}&subject={subject}&text={body}"
    ).encode()

    req = urllib_request.Request(
        f"https://api.mailgun.net/v3/{domain}/messages",
        data=payload,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    resp = urllib_request.urlopen(req)
    result = json.loads(resp.read().decode())

    logger.info("email_mailgun_sent", to=to, subject=subject, message_id=result.get("id"))
    return {"provider": "mailgun", "message_id": result.get("id")}
