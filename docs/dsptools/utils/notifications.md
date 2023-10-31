Module dsptools.utils.notifications
===================================

Functions
---------

    
`send_email(emails: List[str], subject: str, message: str, attachment: Optional[str] = None, email_inbox: str = 'default_placeholder', email_pwd: str = 'default_placeholder', email_server_host: str = 'smtp.office365.com', email_server_port: int = 587) ‑> None`
:   Send an email with an optional attachment to a list of recipients.
    
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

    
`send_teams_message(channel: str, message: str) ‑> None`
:   Send a message to a Microsoft Teams channel using a webhook.
    
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