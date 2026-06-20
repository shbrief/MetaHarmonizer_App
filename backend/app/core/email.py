"""
Transactional email (verification + password reset) via Resend.

Sending is best-effort and isolated here so routers don't touch HTTP/email
details. When ``RESEND_API_KEY`` is set, mail goes out through Resend's REST
API. When it's unset, we fall back to logging the link — convenient for local
development, and never used in production (set the key there).
"""

from __future__ import annotations

import logging

import httpx

from app.core.settings import settings

logger = logging.getLogger("app.email")

RESEND_ENDPOINT = "https://api.resend.com/emails"


async def _send(to: str, subject: str, html: str, *, text_fallback: str) -> None:
    """Send one email via Resend, or log it when no API key is configured."""
    if not settings.resend_api_key:
        # No key: log the link so the flow stays testable in local dev.
        logger.warning("email (no RESEND_API_KEY) -> %s | %s\n%s", to, subject, text_fallback)
        return

    payload = {
        "from": settings.email_from,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    headers = {"Authorization": f"Bearer {settings.resend_api_key}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(RESEND_ENDPOINT, json=payload, headers=headers)
            resp.raise_for_status()
    except Exception:  # noqa: BLE001 — delivery failure must not break the request
        logger.exception("Resend delivery failed for %s", to)


def _button(href: str, label: str) -> str:
    return (
        f'<a href="{href}" style="display:inline-block;padding:10px 18px;'
        f"background:#2986e2;color:#fff;border-radius:8px;text-decoration:none;"
        f'font-weight:600">{label}</a>'
    )


async def send_verification_email(*, to: str, name: str | None, token: str) -> None:
    link = f"{settings.app_base_url}/verify?token={token}"
    greeting = f"Hi {name}," if name else "Hi,"
    html = (
        f"<div style='font-family:system-ui,sans-serif;max-width:480px'>"
        f"<h2>Confirm your email</h2>"
        f"<p>{greeting}</p>"
        f"<p>Welcome to MetaHarmonizer. Please confirm your email address to "
        f"activate your account.</p>"
        f"<p>{_button(link, 'Verify email')}</p>"
        f"<p style='color:#64748b;font-size:13px'>This link expires in 24 hours. "
        f"If you didn't create an account, you can ignore this email.</p>"
        f"</div>"
    )
    await _send(
        to,
        "Confirm your MetaHarmonizer email",
        html,
        text_fallback=f"Verify your email: {link}",
    )


async def send_password_reset_email(*, to: str, name: str | None, token: str) -> None:
    link = f"{settings.app_base_url}/reset?token={token}"
    greeting = f"Hi {name}," if name else "Hi,"
    html = (
        f"<div style='font-family:system-ui,sans-serif;max-width:480px'>"
        f"<h2>Reset your password</h2>"
        f"<p>{greeting}</p>"
        f"<p>We received a request to reset your MetaHarmonizer password. "
        f"Click below to choose a new one.</p>"
        f"<p>{_button(link, 'Reset password')}</p>"
        f"<p style='color:#64748b;font-size:13px'>This link expires in 30 minutes. "
        f"If you didn't request this, you can safely ignore this email — your "
        f"password won't change.</p>"
        f"</div>"
    )
    await _send(
        to,
        "Reset your MetaHarmonizer password",
        html,
        text_fallback=f"Reset your password: {link}",
    )
