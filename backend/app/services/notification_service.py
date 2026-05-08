try:
    from twilio.rest import Client
except ImportError:
    Client = None

from uuid import uuid4

from app.core.config import Settings
from app.schemas.qa_run import NotificationLog
from app.utils.time import utcnow


class NotificationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = None
        if Client and settings.twilio_account_sid and settings.twilio_auth_token:
            self._client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

    async def send_whatsapp(self, run_id: str, message: str, recipient: str | None = None) -> NotificationLog:
        target = recipient or self._settings.default_alert_to or "unconfigured"
        status = "simulated"
        sid = f"WA_{uuid4().hex[:12]}"

        if self._client and self._settings.twilio_whatsapp_from:
            try:
                # Twilio requires WhatsApp numbers to be prefixed with 'whatsapp:'
                msg = self._client.messages.create(
                    from_=f"whatsapp:{self._settings.twilio_whatsapp_from}",
                    body=message,
                    to=f"whatsapp:{target}"
                )
                sid = msg.sid
                status = "sent"
            except Exception as e:
                status = f"failed: {str(e)}"

        return NotificationLog(
            run_id=run_id,
            channel="whatsapp",
            recipient=target,
            message=message,
            status=status,
            provider_sid=sid,
            created_at=utcnow(),
        )

    async def send_sms(self, run_id: str, message: str, recipient: str | None = None) -> NotificationLog:
        target = recipient or self._settings.default_alert_to or "unconfigured"
        status = "simulated"
        sid = f"SMS_{uuid4().hex[:12]}"

        if self._client and self._settings.twilio_sms_from:
            try:
                msg = self._client.messages.create(
                    from_=self._settings.twilio_sms_from,
                    body=message,
                    to=target
                )
                sid = msg.sid
                status = "sent"
            except Exception as e:
                status = f"failed: {str(e)}"

        return NotificationLog(
            run_id=run_id,
            channel="sms",
            recipient=target,
            message=message,
            status=status,
            provider_sid=sid,
            created_at=utcnow(),
        )
