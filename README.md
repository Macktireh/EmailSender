# EmailService Class

The `EmailService` class is designed to provide an easy and organized way to handle email services in your application. It offers support for sending HTML-formatted emails, including attachments, recipients, CC recipients, and BCC recipients. Below, we'll provide an overview of how to use the `EmailService` class effectively.

## Usage

To use the `EmailService` class, follow these steps:

1. Import the `EmailService` class: You need to import the EmailService class in your

```py
from email_service import EmailService, EmailServiceSettings
```

2. Set up your email service settings: Create an `EmailServiceSettings` instance with the necessary parameters. Here's an example:

```py
email_service_settings = EmailServiceSettings(
    username="your_email@example.com",
    password="your_email_password",
    server="your_email_server",
    port=your_email_port
    dev_mode=True  # Activate development mode
)
```

If `dev_mode` is set to True, the e-mail will be printed at the console instead of actually being sent. This is useful for checking the contents of the e-mail without actually sending it. For production use, you can set dev_mode to False.

3. Create an `EmailService` instance: Instantiate the `EmailService` class with your email service settings:

```py
email_service = EmailService(email_service_settings)
```
4. Specify email details: Customize your email by specifying the subject, email body (in HTML format), recipients, CC recipients, BCC recipients, and attachments. For example:

```py
email_service.subject("Subject of your email")
email_service.body("HTML-formatted email content")
email_service.recipients(["recipient1@example.com", "recipient2@example.com"])
email_service.cc_recipients(["cc_recipient@example.com"])
email_service.bcc_recipients(["bcc_recipient@example.com"])
email_service.attach_files(["attachment1.txt", "attachment2.pdf"])
```

5. Send the email: Finally, use the send() method to send your email:

```py
email_service.send()
```

## Debugging Mode

You can activate debug mode by setting `debug=True` when calling the `send()` method. In this mode, the contents of the email will be sent and printed on the console.

**Note**: Ensure you have the required SMTP server information, such as the server address, port, email credentials, and recipient email addresses, correctly configured in your `EmailServiceSettings` instance.

This `EmailService` class offers a convenient and well-organized way to manage your email communications within a Flask application.

## Attribution

The EmailService class was originally created by [CheeseCake87](https://github.com/CheeseCake87) and has been documented and integrated into this repository by [Macktireh](https://github.com/Macktireh).
