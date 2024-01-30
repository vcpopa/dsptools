# pylint: skip-file
from __future__ import annotations
from typing import List, Optional
import yaml
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import pymsteams  # type: ignore[import-not-found]
from dsptools.errors.data import EmailAttachmentError
from dsptools.errors.execution import TeamsMessageError


def send_email(
    emails: List[str],
    subject: str,
    message: str,
    attachment: Optional[str] = None,
    email_inbox: str = "default_placeholder",
    email_pwd: str = "default_placeholder",
    email_server_host: str = "smtp.office365.com",
    email_server_port: int = 587,
) -> None:
    # TODO implement keyvalut and get rid of inbox and pwd params
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


def send_teams_message(channel: str, message: str) -> None:
    """
    Send a message to a Microsoft Teams channel using a webhook.

    Args:
        channel (str): The name of the channel as configured in teams_config.yml.
        message (str): The message text to send.

    Raises:
        TeamsMessageError: An error occurred while sending the Teams message. This is a custom exception
        that encapsulates various possible errors, including those related to webhook configuration and
        network issues.

    Usage:
        try:
            send_teams_message("general", "Hello, Teams!")
        except TeamsMessageError as e:
            print(f"Failed to send Teams message: {e}")
    """
    try:
        # TODO change webhook config from yaml to keyvault
        with open("teams_config.yml", "r") as file:
            channels = yaml.safe_load(file)
        if channel not in channels.keys():
            raise TeamsMessageError(
                f"The specified '{channel}' channel does not exist. Allowed channels: {', '.join(channels.keys())}"
            )

        webhook = channels[channel]
        if not webhook:
            raise TeamsMessageError(
                f"No webhook configured for the '{channel}' channel. Contact an administrator"
            )

        teams_message = pymsteams.connectorcard(webhook)
        teams_message.text(message)
        teams_message.send()

    except pymsteams.WebhookUrlError as e:
        raise TeamsMessageError(f"Error sending Teams message: {e}") from e

    except pymsteams.TeamsWebhookRequestError as e:
        raise TeamsMessageError(f"Error sending Teams message: {e}") from e

    except pymsteams.TeamsWebhookHTTPError as e:
        raise TeamsMessageError(f"Error sending Teams message: {e}") from e

    except pymsteams.TeamsWebhookValidationError as e:
        raise TeamsMessageError(f"Error sending Teams message: {e}") from e

    except pymsteams.TeamsWebhookProxyError as e:
        raise TeamsMessageError(f"Error sending Teams message: {e}") from e

    except Exception as e:
        raise TeamsMessageError(
            f"An unexpected error occurred while sending the Teams message: {e}"
        )
