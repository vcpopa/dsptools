from __future__ import annotations
from typing import List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from azure.storage.blob import BlobServiceClient, ContainerClient  # type: ignore[import-not-found]
from dsptools.errors.data import AzureStorageBlobError, AzureStorageBlobConnectionError


# TODO implement keyvault and remove credentials params
def connect_to_azure_blob(
    storage_account_name: str, storage_account_key: str, container_name: str
) -> ContainerClient:
    """
    Connect to an Azure Storage Blob container.

    Args:
        storage_account_name (str): Azure Storage account name.
        storage_account_key (str): Azure Storage account key or connection string.
        container_name (str): Name of the container to connect to.

    Returns:
        container_client (ContainerClient): Azure Blob Storage container client, or None if failure.

    Raises:
        AzureStorageBlobError: A catch all error class
        AzureStorageBlobConnectionError: If there is an issue connecting to the Azure Blob Storage container.

    Example:
        try:
            container_client = connect_to_azure_blob("your_account_name", "your_account_key", "your_container_name")
            # Use container_client for further operations
        except AzureStorageBlobConnectionError as e:
            print(f"Failed to connect to the '{container_name}' container:\n{e}")
    """
    try:
        # Create a connection string from the account name and key
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={storage_account_name};AccountKey={storage_account_key}"

        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient.from_connection_string(
            connection_string
        )

        # Get a reference to the container
        container_client = blob_service_client.get_container_client(container_name)

        # Check if the container exists
        if not container_client.exists():
            raise AzureStorageBlobError(
                f"The container '{container_name}' does not exist."
            )

        return container_client

    except Exception as e:
        raise AzureStorageBlobConnectionError(
            f"Failed to connect to the '{container_name}' container:\n{str(e)}"
        ) from e


def download_file(
    container_client: ContainerClient,
    source_blob_path: str,
    destination_file_path: str,
    verbose: bool = False,
) -> str:
    """
    Download a file from an Azure Storage Blob container to a local file.

    Args:
        container_client (ContainerClient): Azure Blob Storage container client.
        source_blob_path (str): Path to the blob in the container to download.
        destination_file_path (str): Local path to save the downloaded file.
        verbose (bool): Whether to print a message upon successful download. Defaults to False

    Returns:
        str: The local path to the downloaded file.

    Raises:
        AzureStorageBlobError: If there is an issue with downloading the file from Azure Blob Storage.

    Example:
        try:
            download_file(container_client, "source_blob_path", "local_destination_file", verbose=True)
        except AzureStorageBlobError as e:
            print(f"Download failed: {e}")
    """
    try:
        # Create a BlobClient for the source blob
        blob_client = container_client.get_blob_client(source_blob_path)

        # Download the blob to the specified local file
        with open(destination_file_path, "wb") as local_file:
            data = blob_client.download_blob()
            local_file.write(data.readall())
        if verbose is True:
            print(f"{source_blob_path} downloaded to {destination_file_path}")

        return destination_file_path

    except Exception as e:
        raise AzureStorageBlobError(f"An error occurred: {str(e)}") from e


def download_files_concurrently(
    container_client: ContainerClient,
    file_pairs: List[Tuple[str, str]],
    verbose: bool = False,
    max_workers: int = 4,
) -> List[str]:
    """
    Download files from Azure Blob Storage concurrently.

    Args:
        container_client (ContainerClient): Azure Blob Storage container client.
        file_pairs (List[Tuple[str, str]]): A list of pairs, where each pair is (source_blob_path, destination_file_path).
        verbose (bool): Whether to print messages for each successful download. Defaults to False
        max_workers (int, optional): The maximum number of concurrent workers. Default is 4.

    Returns:
        List[str]: A list of paths to the downloaded files.

    Example:
        result = download_files_concurrently(container_client, [("blob1.txt", "local1.txt"), ("blob2.txt", "local2.txt")], verbose=True, max_workers=4)
        # The 'result' dictionary will contain 'succeeded_files' and 'failed_files' lists.
    """

    def download_file_wrapper(pair, verbose=verbose):
        source_blob_path, destination_file_path = pair
        result = download_file(
            container_client, source_blob_path, destination_file_path, verbose=verbose
        )
        return result

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_file_wrapper, pair) for pair in file_pairs]

        results = []
        for future in futures:
            result = future.result()
            results.append(result)

    return results


def list_files_with_properties(
    container_client: ContainerClient, container_path: str
) -> List[Dict[str, Any]]:
    """
    List files in a specific path of an Azure Storage Blob container with their properties.

    Args:
        container_client (ContainerClient): Azure Blob Storage container client.
        container_path (str): Path within the container to list files from.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing file properties.

    Example:
        file_properties = list_files_with_properties(container_client, "folder/subfolder/")
        # 'file_properties' will contain a list of dictionaries with file properties.
    """
    file_list = []
    try:
        # List all blobs in the container with the specified prefix
        blobs = container_client.list_blobs(name_starts_with=container_path)
        for blob in blobs:
            file_list.append(blob)
    except Exception as e:
        raise AzureStorageBlobError(f"An error occurred: {str(e)}") from e

    return file_list
