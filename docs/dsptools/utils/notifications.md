Module dsptools.utils.notifications
===================================

Functions
---------

    
`handle_failure(handle: Optional[List[Union[Exception, BaseException]]], on_error: Literal['skip', 'warn', 'raise'] = 'warn', *args, **kwargs)`
:   A decorator to send an email notification when specific exceptions occur within a function.
    
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

    
`timeout(max_timeout: int, on_timeout: Literal['skip', 'warn', 'raise'] = 'warn', *args, **kwargs)`
:   Timeout decorator for limiting the execution time of a function.
    
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