from functools import wraps
from typing import List, Optional, Union, Literal
import yaml
import multiprocessing
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import pymsteams
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


def handle_failure(
    handle: Union[List[Union[Exception, BaseException]], None],
    on_error: Literal["skip", "warn", "raise"] = "warn",
    *args,
    **kwargs,
):
    """
    A decorator to send an email notification when specific exceptions occur within a function.

    This decorator allows you to specify a list of exception types that, when raised within
    the decorated function, trigger an email notification. The decorator wraps the original
    function and sends an email with the specified parameters if any of the specified exceptions
    are raised.

    Args:
        handle (Union[List[Union[Exception, BaseException]], None]): A list of exception types to email on, or None to handle any exception.
        on_error (Literal['skip', 'warn', 'raise']): The action to take when an exception occurs.
        *args: Positional arguments to be passed to the `send_email` function.
        **kwargs: Keyword arguments to be passed to the `send_email` function.

    Returns:
        Callable: The decorated function.

    Example:
        @handle_failure([ValueError, FileNotFoundError], on_error='warn', ["recipient@example.com"], subject="Function Failed", message="An error occurred.")
        def my_function():
            # Your function logic here
            raise ValueError("This is an example error")

    The example above will send an email if a `ValueError` or `FileNotFoundError` is raised within `my_function.

    :param handle: List of exception types to handle, or None to handle any exception
    :param on_error: Action to take when an exception occurs ('skip', 'warn', 'raise')
    :param *args: Additional positional arguments for the `send_email` function
    :param **kwargs: Additional keyword arguments for the `send_email` function
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*func_args, **func_kwargs):
            try:
                print(f"Decorator triggered with {on_error}")
                print(f"Sending to {func_args}")
                print(*func_args)
                return func(*func_args, **func_kwargs)
            except Exception as e:
                if handle is None or any(
                    isinstance(e, exception_type) for exception_type in handle
                ):
                    if on_error == "warn":
                        send_email(
                            message=f"Error in {func.__name__}: {str(e)}\n This is a warning, this error has been caught and skipped",
                            *args,
                            **kwargs,
                        )
                    elif on_error == "raise":
                        send_email(
                            message=f"Error in {func.__name__}: {str(e)}\n This error raised an exit",
                            *args,
                            **kwargs,
                        )
                        raise e  # Re-raise the exception after sending the email
                    else:
                        print(
                            f"Decorator set to {on_error}. The following error was caught and handled:\n{str(e)}"
                        )
                else:
                    raise e  # Re-raise the exception if it's not in the list of exceptions to handle

        return wrapper

    return decorator


def timeout(
    max_timeout: int,
    on_timeout: Literal["skip", "warn", "raise"] = "warn",
    *args,
    **kwargs,
):
    """
    Timeout decorator for limiting the execution time of a function.

    This decorator allows you to set a maximum execution time for a function. If the function
    execution time exceeds the specified timeout, the decorator can take action based on the
    `on_timeout` parameter, which can be set to 'skip', 'warn', or 'raise'. By default, it warns
    when a timeout occurs.

    Args:
        max_timeout (int): The maximum execution time allowed for the decorated function, in seconds.
        on_timeout (Literal['skip', 'warn', 'raise'], optional): The action to take when a timeout occurs.
            'skip' will continue executing the function, 'warn' will display a warning message, and 'raise'
            will raise a `multiprocessing.TimeoutError`. Defaults to 'warn'.
        *args: Additional positional arguments to be passed to the email sending function when a timeout occurs.
        **kwargs: Additional keyword arguments to be passed to the email sending function when a timeout occurs.

    Returns:
        Callable: The decorated function.

    Example Usage:
    ```python
    @timeout(max_timeout=60, on_timeout='warn', emails=['admin@example.com'], subject='Function Timeout', message='Function execution time exceeded')
    def my_function():
        # Function logic here
    ```

    Args:
        max_timeout (int): The maximum execution time allowed for the decorated function, in seconds.
        on_timeout (Literal['skip', 'warn', 'raise'], optional): The action to take when a timeout occurs.
        *args: Additional positional arguments for the email sending function.
        **kwargs: Additional keyword arguments for the email sending function.

    Returns:
        Callable: The decorated function.

    """

    def timeout_decorator(item):
        """Wrap the original function."""

        @wraps(item)
        def func_wrapper(*args, **kwargs):
            """Closure for function."""
            pool = multiprocessing.pool.ThreadPool(processes=1)
            async_result = pool.apply_async(item, args, kwargs)

            try:
                # Get the result within the specified timeout
                result = async_result.get(max_timeout)
                return result
            except multiprocessing.TimeoutError as e:
                if on_timeout == "warn":
                    send_email(
                        *args,
                        **kwargs,
                    )
                elif on_timeout == "raise":
                    send_email(
                        *args,
                        **kwargs,
                    )
                    raise e  # Re-raise the exception after sending the email
                else:
                    print(
                        f"Decorator set to {on_timeout}. The following error was caught and handled:\n{str(e)}"
                    )

            # Allow the decorated function to continue running even after timeout
            return None  # You may choose to return a default value or None on timeout

        return func_wrapper

    return timeout_decorator


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
