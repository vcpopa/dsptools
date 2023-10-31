# pylint: disable = unnecessary-pass
class EmailAttachmentError(Exception):
    """
    Exception raised for errors related to email attachment handling.

    This exception is used for errors encountered when working with email attachments, such as
    attachment file handling, sending email with attachments, or receiving email with problematic
    attachments.

    """

    pass


class SFTPError(Exception):
    """
    Exception raised for errors related to Secure File Transfer Protocol (SFTP) operations.

    This exception is used to handle errors occurring during SFTP file transfers, connections,
    or other SFTP-related operations.

    """

    pass


class AzureStorageBlobError(Exception):
    """
    Exception raised for errors related to Azure Storage Blob operations.

    This exception is used for errors encountered when working with Azure Storage Blobs, such as
    uploading, downloading, or managing blobs within an Azure Storage account.

    """

    pass


class AzureStorageBlobConnectionError(Exception):
    """
    Exception raised for connection errors to Azure Storage Blob services.

    This exception is used to handle errors related to connecting to Azure Storage Blob services,
    including issues like authentication failures, network problems, or service unavailability.

    """

    pass
