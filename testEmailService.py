import unittest
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from emailService import EmailService, EmailServiceSettings


class TestEmailService(unittest.TestCase):
    def test_initialization(self) -> None:
        settings = EmailServiceSettings(
            username="test@test.com",
            password="password",
            server="smtp.test.com",
            port=587,
        )
        email_service = EmailService(settings)

        self.assertEqual(email_service.username, "test@test.com")
        self.assertEqual(email_service.password, "password")
        self.assertEqual(email_service.server, "smtp.test.com")
        self.assertEqual(email_service.port, 587)
        self.assertIsInstance(email_service._msg, MIMEMultipart)

    def test_subject(self) -> None:
        settings = EmailServiceSettings(
            username="test@test.com",
            password="password",
            server="smtp.test.com",
            port=587,
        )
        email_service = EmailService(settings)
        email_service.subject("Test Subject")

        self.assertEqual(email_service._subject, "Test Subject")

    def test_body(self) -> None:
        settings = EmailServiceSettings(
            username="test@test.com",
            password="password",
            server="smtp.test.com",
            port=587,
        )
        email_service = EmailService(settings)
        email_service.body("Test Body")

        self.assertIsInstance(email_service._msg_body, MIMEText)
        self.assertEqual(email_service._msg_body.get_payload(), "Test Body")

    # def test_reply_to(self):
    #     settings = EmailServiceSettings(
    #         username="test@test.com",
    #         password="password",
    #         server="smtp.test.com",
    #         port=587,
    #     )
    #     email_service = EmailService(settings)
    #     email_service.reply_to("reply@test.com")

    #     self.assertEqual(email_service._reply_to, "reply@test.com")

    def test_attach_file(self) -> None:
        settings = EmailServiceSettings(
            username="test@test.com",
            password="password",
            server="smtp.test.com",
            port=587,
        )
        email_service = EmailService(settings)
        email_service.attach_file(Path("test.txt"))

        self.assertEqual(len(email_service._attachments), 1)

    def test_send_email(self) -> None:
        settings = EmailServiceSettings(
            username="test@test.com",
            password="password",
            server="smtp.test.com",
            port=587,
            dev_mode=True,
        )
        email_service = EmailService(settings)

        # Replace this with a test-specific email address
        email_service.recipients(["test@test.com"])
        result = email_service.send()

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
