import asyncio
import smtplib
from email.message import EmailMessage

from app.core.config import Settings


class SmtpPasswordResetDelivery:
    def __init__(self, settings: Settings) -> None:
        if not all(
            [settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]
        ):
            raise ValueError("SMTP is not configured")
        assert settings.smtp_host is not None
        assert settings.smtp_username is not None
        assert settings.smtp_password is not None
        assert settings.smtp_from is not None
        self._host = settings.smtp_host
        self._port = settings.smtp_port
        self._username = settings.smtp_username
        self._password = settings.smtp_password
        self._from = settings.smtp_from

    async def send(self, *, email: str, reset_url: str) -> None:
        await asyncio.to_thread(self._send_sync, email, reset_url)

    def _send_sync(self, email: str, reset_url: str) -> None:
        message = EmailMessage()
        message["Subject"] = "Restablece tu acceso a ProcessOS"
        message["From"] = self._from
        message["To"] = email
        message.set_content(
            "Se ha solicitado restablecer tu contraseña de ProcessOS. "
            f"Usa este enlace temporal: {reset_url}"
        )
        with smtplib.SMTP(self._host, self._port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(self._username, self._password.get_secret_value())
            smtp.send_message(message)
