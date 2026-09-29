from email.message import EmailMessage
import smtplib

from trade_ware.core.config import settings


class EmailService:
    """Generic email sender used by all application features."""

    @staticmethod
    def send_email(
        to_email: str, subject: str, body: str, *, html_body: str | None = None
    ) -> None:
        """Send an email if SMTP is configured, otherwise log it for local development."""
        sender = settings.smtp_from_email or "noreply@localhost"

        if settings.smtp_host and settings.smtp_username and settings.smtp_password:
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = sender
            message["To"] = to_email
            message.set_content(body)

            if html_body:
                message.add_alternative(html_body, subtype="html")

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as smtp:
                smtp.starttls()
                smtp.login(settings.smtp_username, settings.smtp_password)
                smtp.send_message(message)
            return

        print(f"[DEV EMAIL] To: {to_email}\nSubject: {subject}\n{body}")
