from functools import wraps
from typing import List, Optional
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from dsptools.errors.data import EmailAttachmentError


def send_email(
    email_inbox: str,
    email_pwd: str,
    emails: List[str],
    subject: str,
    message: str,
    attachment: Optional[str] = None,
    email_server_host: str = "smtp.office365.com",
    email_server_port: int = 587,
):
    """
    Send an email with an optional attachment to a list of recipients.

    Args:
        emails (List[str]): List of email addresses to send the email to.
        subject (str): The email subject.
        message (str): The email message content (HTML).
        attachment (str, optional): Path to the attachment file (PDF, DOC, CSV, TXT, or LOG). Default is None.
        email_inbox (str, optional): The sender's email address.
        email_pwd (str, optional): The sender's email password.
        email_server_host (str, optional): The SMTP server host. Default is "smtp.office365.com".
        email_server_port (int, optional): The SMTP server port. Default is 587.

    Raises:
        smtplib.SMTPException: If there is an issue with the SMTP server connection.
        FileNotFoundError: If the attachment file is not found.
        ValueError: If the attachment file type is not supported.

    Example:
        send_email(
            emails=["recipient@example.com"],
            subject="Important Report",
            message="<html><body>...</body></html>",
            attachment="report.pdf",
            email_inbox="sender@example.com",
            email_pwd="password123"
        )
    """
    supported_attachment_types = (".pdf", ".doc", ".csv", ".txt", ".log")

    if attachment and not attachment.endswith(supported_attachment_types):
        raise EmailAttachmentError(
            "Unsupported attachment file type. Supported types: PDF, DOC, CSV, TXT, LOG"
        )

    for emailto in emails:
        msg = MIMEMultipart()
        msg["From"] = email_inbox
        msg["To"] = emailto
        msg["Subject"] = subject
        msg.attach(MIMEText(message, "html"))

        if attachment:
            try:
                with open(attachment, "rb") as file:
                    attach = MIMEApplication(
                        file.read(), _subtype=attachment.split(".")[-1]
                    )
                    attach.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=attachment.replace("logs", ""),
                    )
                    msg.attach(attach)
            except FileNotFoundError:
                raise FileNotFoundError("Attachment file not found")

        try:
            server = smtplib.SMTP(email_server_host, email_server_port)
            server.starttls()
            server.login(email_inbox, email_pwd)
            server.sendmail(email_inbox, emailto, msg.as_string())
            server.quit()
        except smtplib.SMTPException as e:
            raise smtplib.SMTPException(f"Error sending email: {str(e)}")


def email_on_failure(exceptions_to_email: List[Exception], *args, **kwargs):
    """
    A decorator to send an email notification when specific exceptions occur within a function.

    This decorator allows you to specify a list of exception types that, when raised within
    the decorated function, trigger an email notification. The decorator wraps the original
    function and sends an email with the specified parameters if any of the specified exceptions
    are raised.

    Args:
        exceptions_to_email (List[Exception]): A list of exception types to email on.
        *args: Positional arguments to be passed to the `send_email` function.
        **kwargs: Keyword arguments to be passed to the `send_email` function.

    Returns:
        Callable: The decorated function.

    Example:
        @email_on_failure([ValueError, FileNotFoundError], ["recipient@example.com"], subject="Function Failed", message="An error occurred.")
        def my_function():
            # Your function logic here
            raise ValueError("This is an example error")

    The example above will send an email if a `ValueError` or `FileNotFoundError` is raised within `my_function`.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*func_args, **func_kwargs):
            try:
                return func(*func_args, **func_kwargs)
            # TODO find some different way to do this so pylint stops freaking out
            except tuple(exceptions_to_email) as e:
                send_email(
                    message=f"Error in {func.__name__}: {str(e)}",
                    *args,
                    **kwargs,
                )
                raise e  # Re-raise the exception after sending the email

        return wrapper

    return decorator
