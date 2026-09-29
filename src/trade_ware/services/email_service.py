import smtplib
from email.message import EmailMessage

from trade_ware.core.config import settings


class EmailService:
    """Generic email sender used by all application features."""

    @staticmethod
    def send_email(
        to_email: str, subject: str, body: str, *, html_body: str | None = None
    ) -> None:
        """Send email via SMTP, or log it when SMTP is not configured."""

        if (
            settings.smtp_host
            and settings.smtp_username
            and settings.smtp_password
        ):
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = settings.smtp_username
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
