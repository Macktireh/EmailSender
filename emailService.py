from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from smtplib import SMTP
from smtplib import SMTPException
from ssl import create_default_context
from typing import Optional


class SMTPEmailServiceSettings:
    username: str
    password: str
    server: str
    port: int

    def __init__(
        self,
        username: str,
        password: str,
        server: str,
        port: int,
        dev_mode: bool = False,
    ) -> None:
        self.dev_mode = dev_mode
        self.username = username
        self.password = password
        self.server = server
        self.port = port


class SMTPEmailService:
    settings: SMTPEmailServiceSettings

    _subject: str
    _msg: Optional[MIMEMultipart]
    _msg_body: Optional[MIMEText]
    _original_sender: str
    _reply_to: str
    _from: str
    _recipients: set[str]
    _cc_recipients: set[str]
    _bcc_recipients: set[str]
    _attachments: set[tuple[Path, str]]

    def __init__(self, settings: SMTPEmailServiceSettings) -> None:
        self.settings = settings

        self._subject = ""
        self._msg_body = MIMEText("")
        self._original_msg_body = MIMEText("")
        self._original_sender = settings.username
        self._reply_to = settings.username
        self._from = settings.username
        self._recipients = set()
        self._cc_recipients = set()
        self._bcc_recipients = set()
        self._attachments = set()

        self._msg = MIMEMultipart()
        self._msg.set_type("multipart/alternative")

    def __repr__(self) -> str:
        attachments = "\n".join(
            [f"{file} - {status}" for file, status in self._attachments]
        )
        return (
            f"<Class: SMTPEmailService>"
            f"\n{self._msg}\n"
            "Files set for attachment:\n"
            f"{attachments}"
        )

    def subject(
        self,
        subject: str,
    ) -> "SMTPEmailService":
        self._subject = subject
        return self

    def body(
        self,
        body: str,
    ) -> "SMTPEmailService":
        self._original_msg_body = body
        self._msg_body = MIMEText(body)
        self._msg_body.set_type("text/html")
        self._msg_body.set_param("charset", "UTF-8")
        self._msg.attach(self._msg_body)
        return self

    def reply_to(self, reply_to: str) -> "SMTPEmailService":
        self._msg.replace_header("Reply-To", reply_to)
        return self

    def from_(self, from_: str) -> "SMTPEmailService":
        self._from = from_
        return self

    def recipients(self, recipients: list[str]) -> "SMTPEmailService":
        self._recipients.update(set(recipients))
        if "To" in self._msg:
            self._msg.replace_header("To", ", ".join(self._recipients))
            return self

        self._msg.add_header("To", ", ".join(self._recipients))
        return self

    def cc_recipients(self, cc_recipients: list[str]) -> "SMTPEmailService":
        self._cc_recipients.update(set(cc_recipients))
        if "CC" in self._msg:
            self._msg.replace_header("CC", ", ".join(self._cc_recipients))
            return self

        self._msg.add_header("CC", ", ".join(self._cc_recipients))
        return self

    def bcc_recipients(self, bcc_recipients: list[str]) -> "SMTPEmailService":
        self._bcc_recipients.update(set(bcc_recipients))
        if "BCC" in self._msg:
            self._msg.replace_header("BCC", ", ".join(self._bcc_recipients))
            return self

        self._msg.add_header("BCC", ", ".join(self._bcc_recipients))
        return self

    def attach_files(self, files: list[str | Path]) -> "SMTPEmailService":
        for file in files:
            if isinstance(file, Path):
                filepath: Path = file
            else:
                filepath: Path = Path(file)

            self._attachments.update(
                [(filepath, "Exists" if filepath.exists() else "Missing")]
            )

            if filepath.exists():
                contents = MIMEApplication(
                    filepath.read_bytes(), _subtype=filepath.suffix
                )
                contents.add_header(
                    "Content-Disposition", "attachment", filename=filepath.name
                )
                self._msg.attach(contents)

        return self

    def attach_file(self, file: str | Path) -> "SMTPEmailService":
        self.attach_files([file])
        return self

    def send(self, debug: bool = False) -> bool:
        """
        Sends the email. If debug is True, it will print the email.
        :param debug:
        :return:
        """

        self._msg.add_header("Original-Sender", self._original_sender)
        self._msg.add_header("Reply-To", self._reply_to)
        self._msg.add_header("From", self._from)
        self._msg.add_header("Subject", self._subject)

        if self.dev_mode:
            print()
            print("printing email:")
            print(self)
            print()
            print("Original message:")
            print(self._original_msg_body)
            print()
            return True

        try:
            with SMTP(self.settings.server, self.settings.port) as connection:
                connection.starttls(context=create_default_context())
                connection.login(self.settings.username, self.settings.password)
                connection.sendmail(
                    self.settings.username,
                    [*self._recipients, *self._cc_recipients, *self._bcc_recipients],
                    self._msg.as_string(),
                )
        except SMTPException as error:
            if debug:
                print(error)

            return False

        if debug:
            print()
            print("printing email after sending:")
            print(self)
            print()
            print("Original message:")
            print(self._original_msg_body)
            print()

        return True


# usage:
"""
email_service_settings = SMTPEmailServiceSettings(
    username="test0@test.com",
    password="none",
    server="none.none.none",
    port=000
)

email_service = SMTPEmailService(
    email_service_settings
)

email_service.adjust_from("Test 0 <test0@test.com>")

email_service.recipients(
    ["test1@test.com"]
)

email_service.cc_recipients(
    ["test2@test.com"]
)

email_service.bcc_recipients(
    ["test3@test.com"]
)

email_service.subject(
    "test"
)

email_service.body(
    "test"
)

email_service.attach_files(
    [
        Path(Path.cwd() / "test1.txt"),
        Path(Path.cwd() / "test2.txt")
    ]
)

email_service.send()
"""
