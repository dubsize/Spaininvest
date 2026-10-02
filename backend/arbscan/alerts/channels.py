"""Notification channels. Add WhatsApp/Discord/Slack/push by implementing ``Channel``."""

from __future__ import annotations

import html
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage

import httpx

from arbscan.core.config import Settings, get_settings
from arbscan.core.logging import get_logger

log = get_logger(__name__)


@dataclass
class AlertMessage:
    subject: str
    text: str  # plain text (also used for Telegram, HTML-escaped)
    url: str | None = None


class Channel(ABC):
    name: str

    @abstractmethod
    def is_configured(self) -> bool: ...

    @abstractmethod
    def send(self, msg: AlertMessage) -> None: ...


class LogChannel(Channel):
    """Always available; records the alert in the logs (useful in development)."""

    name = "log"

    def is_configured(self) -> bool:
        return True

    def send(self, msg: AlertMessage) -> None:
        log.info("ALERT", extra={"subject": msg.subject, "body": msg.text, "url": msg.url})


class TelegramChannel(Channel):
    """Telegram Bot API ``sendMessage`` (https://core.telegram.org/bots/api#sendmessage)."""

    name = "telegram"

    def __init__(self, settings: Settings | None = None, transport: httpx.BaseTransport | None = None):
        self.s = settings or get_settings()
        self.transport = transport

    def is_configured(self) -> bool:
        return bool(self.s.telegram_bot_token and self.s.telegram_chat_id)

    def send(self, msg: AlertMessage) -> None:
        body = html.escape(msg.text)
        payload: dict = {
            "chat_id": self.s.telegram_chat_id,
            "text": body[:4000],
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        if msg.url:
            payload["reply_markup"] = {"inline_keyboard": [[{"text": "OPEN LISTING", "url": msg.url}]]}
        with httpx.Client(timeout=15, transport=self.transport) as client:
            resp = client.post(f"https://api.telegram.org/bot{self.s.telegram_bot_token}/sendMessage", json=payload)
            if resp.status_code >= 400:
                raise RuntimeError(f"Telegram error {resp.status_code}: {resp.text[:200]}")


class EmailChannel(Channel):
    name = "email"

    def __init__(self, settings: Settings | None = None):
        self.s = settings or get_settings()

    def is_configured(self) -> bool:
        return bool(self.s.smtp_host and self.s.alert_email_to and (self.s.smtp_from or self.s.smtp_username))

    def send(self, msg: AlertMessage) -> None:
        em = EmailMessage()
        em["Subject"] = msg.subject
        em["From"] = self.s.smtp_from or self.s.smtp_username
        em["To"] = self.s.alert_email_to
        em.set_content(msg.text + (f"\n\nOpen listing: {msg.url}" if msg.url else ""))
        with smtplib.SMTP(self.s.smtp_host, self.s.smtp_port, timeout=20) as smtp:
            if self.s.smtp_starttls:
                smtp.starttls()
            if self.s.smtp_username:
                smtp.login(self.s.smtp_username, self.s.smtp_password)
            smtp.send_message(em)


def available_channels(settings: Settings | None = None) -> dict[str, Channel]:
    chans: list[Channel] = [LogChannel(), TelegramChannel(settings), EmailChannel(settings)]
    return {c.name: c for c in chans}
