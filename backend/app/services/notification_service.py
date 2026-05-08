from __future__ import annotations

from uuid import uuid4

from app.core.config import Settings
from app.schemas.qa_run import NotificationLog
from app.utils.time import utcnow


class NotificationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def send_whatsapp(self, run_id: str, message: str, recipient: str | None = None) -> NotificationLog:
        target = recipient or self._settings.default_alert_to or "unconfigured"
        return NotificationLog(
            run_id=run_id,
            channel="whatsapp",
            recipient=target,
            message=message,
            status="sent" if self._settings.twilio_whatsapp_from else "simulated",
            provider_sid=f"WA_{uuid4().hex[:12]}",
            created_at=utcnow(),
        )

    async def send_sms(self, run_id: str, message: str, recipient: str | None = None) -> NotificationLog:
        target = recipient or self._settings.default_alert_to or "unconfigured"
        return NotificationLog(
            run_id=run_id,
            channel="sms",
            recipient=target,
            message=message,
            status="sent" if self._settings.twilio_sms_from else "simulated",
            provider_sid=f"SMS_{uuid4().hex[:12]}",
            created_at=utcnow(),
        )
