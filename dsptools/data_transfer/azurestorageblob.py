from typing import Union, List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from azure.storage.blob import BlobServiceClient, ContainerClient


def connect_to_azure_blob(
    storage_account_name: str, storage_account_key: str, container_name: str
) -> Union[ContainerClient, None]:
    """
    Connect to an Azure Storage Blob container.

    Args:
        storage_account_name (str): Azure Storage account name.
        storage_account_key (str): Azure Storage account key or connection string.
        container_name (str): Name of the container to connect to.

    Returns:
        container_client (ContainerClient): Azure Blob Storage container client, or None if the connection fails.
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
            raise Exception(f"The container '{container_name}' does not exist.")

        return container_client

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return None


def download_file(
    container_client: ContainerClient,
    source_blob_path: str,
    destination_file_path: str,
) -> bool:
    """
    Download a file from an Azure Storage Blob container to a local file.

    Args:
        container_client (ContainerClient): Azure Blob Storage container client.
        source_blob_path (str): Path to the blob in the container to download.
        destination_file_path (str): Local path to save the downloaded file.

    Returns:
        bool: True if the download is successful, False otherwise.
    """
    try:
        # Create a BlobClient for the source blob
        blob_client = container_client.get_blob_client(source_blob_path)

        # Download the blob to the specified local file
        with open(destination_file_path, "wb") as local_file:
            data = blob_client.download_blob()
            local_file.write(data.readall())

        return True

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return False


def download_files_concurrently(
    container_client: ContainerClient,
    file_pairs: List[Tuple[str, str]],
    max_workers: int,
) -> Dict[str, List]:
    """
    Download files from Azure Blob Storage concurrently.

    Args:
        container_client (ContainerClient): Azure Blob Storage container client.
        file_pairs (list): A list of pairs, where each pair is (source_blob_path, destination_file_path).
        max_workers (int): The maximum number of concurrent workers.

    Returns:
        dict: A dictionary containing lists of succeeded and failed downloads.

    Example:
    download_files_concurrently(container_client, [("blob1.txt", "local1.txt"), ("blob2.txt", "local2.txt")], 4)
    """

    def download_file_wrapper(pair):
        source_blob_path, destination_file_path = pair
        result = download_file(
            container_client, source_blob_path, destination_file_path
        )
        return (source_blob_path, result)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_file_wrapper, pair) for pair in file_pairs]

        succeeded_files = []
        failed_files = []

        for future in futures:
            source_blob_path, result = future.result()
            if result is True:
                succeeded_files.append(source_blob_path)
            else:
                failed_files.append(source_blob_path)

    return {"succeeded_files": succeeded_files, "failed_files": failed_files}


def list_files_with_properties(
    container_client: ContainerClient, container_path: str
) -> List[Dict[str, Any]]:
    """
    List files in a specific path of an Azure Storage Blob container with their properties.

    Args:
        container_client (ContainerClient): Azure Blob Storage container client.
        container_path (str): Path within the container to list files from.

    Returns:
        dict: A list of dictionaries containing file properties
    """
    file_list = []
    try:
        # List all blobs in the container with the specified prefix
        blobs = container_client.list_blobs(name_starts_with=container_path)
        for blob in blobs:
            file_list.append(blob)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e

    return file_list
