from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from imaplib import IMAP4_SSL
from pathlib import Path
from smtplib import SMTP
from smtplib import SMTPException
from ssl import create_default_context
from typing import Optional, Union

from mailparser import MailParser, parse_from_bytes


class EmailServiceSettings:
    username: str
    password: str
    server: str
    port: int

    def __init__(
        self,
        username: str,
        password: str,
        server: str,
        port: Union[int, str],
        dev_mode: Union[int, str, bool],
    ) -> None:
        """
                Dev_mode will prevent the email from being sent. It will print the email instead.

                Dev_mode: 1, "1", True, "True", "true" will set dev_mode to True, else False

                :param dev_mode:
                :param username:
                :param password:
                :param server:
                :param port:
                """
        truly = [1, "1", True, "True", "true"]
        self.dev_mode = True if dev_mode in truly else False
        self.username = username
        self.password = password
        self.server = server

        if isinstance(port, int):
            self.port = port
        else:
            try:
                self.port = int(port)
            except ValueError:
                raise ValueError("Port must be an integer or string-int.")


class IMAPEmailService:
    settings: EmailServiceSettings
    timeout: int

    connection: IMAP4_SSL = None
    parsed_emails: list[tuple[any, MailParser]]

    def __init__(self, settings: EmailServiceSettings, timeout: int = 120) -> None:
        self.settings = settings
        self.timeout = timeout
        self.parsed_emails = []

    def __enter__(self):
        self.connection = IMAP4_SSL(
            self.settings.server, self.settings.port, timeout=self.timeout
        )
        try:
            self.connection.login(self.settings.username, self.settings.password)
        except IMAP4_SSL.error:
            raise ConnectionError("Failed to connect to IMAP server.")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection.state == "SELECTED":
            self.connection.close()

        self.connection.logout()
        pass

    def store(self, message_set: str, command: str, flags: str):
        if self.connection:
            self.connection.store(message_set, command, flags)
            return True

        raise ConnectionError("IMAP connection not established. Use with statement.")

    def get_inbox(self) -> list[tuple[any, MailParser]]:
        if self.connection:
            self.connection.select("INBOX")

            _, data = self.connection.search(None, "ALL")
            listed = data[0].split()

            for num in listed:
                _, resp = self.connection.fetch(num, "(RFC822)")
                if resp:
                    raw = resp[0]
                    if isinstance(raw, tuple):
                        self.parsed_emails.append((num, parse_from_bytes(raw[1])))

            return self.parsed_emails

        raise ConnectionError("IMAP connection not established. Use with statement.")

    def __repr__(self) -> str:
        return f"<Class: IMAPEmailService>" f"\n{self.parsed_emails}\n"


class SMTPEmailService:
    settings: EmailServiceSettings

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

    def __init__(self, settings: EmailServiceSettings) -> None:
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

        if self.settings.dev_mode:
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
email_service_settings = EmailServiceSettings(
    username="test0@test.com",
    password="none",
    server="none.none.none",
    port=000
)


# SMTP Service

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


# IMAP Service

with IMAPEmailService(email_service_settings) as service:
    inbox = service.get_inbox()
    
    for inbox_email in inbox:
        email_id, email = inbox_email
        print(email_id, email.text_plain)
        print("-" * 80)


# IMAP Service - Mark as read

with IMAPEmailService(email_service_settings) as service:
    inbox = service.get_inbox()
    
    for inbox_email in inbox:
        email_id, email = inbox_email
        print(email_id, email.text_plain)
        print("-" * 80)
        
        service.store(email_id, "+FLAGS", "\\Seen")


## email.<option>

email.attachments: list of all attachments
email.body
email.date: datetime object in UTC
email.defects: defect RFC not compliance
email.defects_categories: only defects categories
email.delivered_to
email.from_
email.get_server_ipaddress(trust="my_server_mail_trust")
email.headers
email.mail: tokenized mail in a object
email.message: email.message.Message object
email.message_as_string: message as string
email.message_id
email.received
email.subject
email.text_plain: only text plain mail parts in a list
email.text_html: only text html mail parts in a list
email.text_not_managed: all not managed text (check the warning logs to find content subtype)
email.to
email.to_domains
email.timezone: returns the timezone, offset from UTC
email.mail_partial: returns only the mains parts of emails

~~ Save attachments

email.write_attachments(base_path)

"""
