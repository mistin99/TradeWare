from unittest.mock import patch

from trade_ware.core.config import settings
from trade_ware.services.email_service import EmailService


def test_send_email_uses_mocked_smtp():
    with (
        patch.multiple(
            settings,
            smtp_host="smtp.test.invalid",
            smtp_port=587,
            smtp_username="sender@example.com",
            smtp_password="test-password",
        ),
        patch(
            "trade_ware.services.email_service.smtplib.SMTP"
        ) as smtp_factory,
    ):
        smtp_client = smtp_factory.return_value.__enter__.return_value
        EmailService.send_email(
            "recipient@example.com",
            "Test subject",
            "Plain text body",
            html_body="<p>HTML body</p>",
        )

    smtp_factory.assert_called_once_with("smtp.test.invalid", 587)
    smtp_client.starttls.assert_called_once_with()
    smtp_client.login.assert_called_once_with(
        "sender@example.com", "test-password"
    )
    message = smtp_client.send_message.call_args.args[0]
    assert message["To"] == "recipient@example.com"
    assert message["From"] == "sender@example.com"
    assert message["Subject"] == "Test subject"
    assert message.get_body(preferencelist=("plain",)).get_content() == (
        "Plain text body\n"
    )
    assert message.get_body(preferencelist=("html",)).get_content() == (
        "<p>HTML body</p>\n"
    )


def test_send_email_logs_when_smtp_is_not_configured():
    with (
        patch.multiple(
            settings,
            smtp_host="",
            smtp_username="",
            smtp_password="",
        ),
        patch(
            "trade_ware.services.email_service.smtplib.SMTP"
        ) as smtp_factory,
        patch("builtins.print") as print_mock,
    ):
        EmailService.send_email("recipient@example.com", "Subject", "Body")

    smtp_factory.assert_not_called()
    print_mock.assert_called_once()
    output = print_mock.call_args.args[0]
    assert "recipient@example.com" in output
    assert "Subject" in output
    assert "Body" in output

