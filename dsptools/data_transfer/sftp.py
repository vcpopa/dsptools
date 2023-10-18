import subprocess
from typing import Tuple, List, Dict, Any
import concurrent
import paramiko
from dsptools.errors.data import SFTPError


def download_sftp(
    username: str,
    password: str,
    host: str,
    sftp_file_path: str,
    destination_folder_path: str,
) -> Tuple[str, str]:
    """
    Download a file from an SFTP server to a local destination folder using pscp.

    Args:
        username (str): The SFTP username.
        password (str): The SFTP password.
        host (str): The SFTP host address.
        sftp_file_path (str): The path to the file on the SFTP server.
        destination_folder_path (str): The local destination folder to save the downloaded file.

    Returns:
        Tuple[str, str]: A tuple containing the standard output and standard error from the pscp command.

    Example:
        download_sftp(username="myuser", password="mypassword", host="sftp.example.com",
                      sftp_file_path="/remote/file.txt", destination_folder_path="/local/folder")
    """
    command = f"pscp -pw {password} {username}@{host}:{sftp_file_path} {destination_folder_path}"
    print(f"Downloading {sftp_file_path} to {destination_folder_path}")
    try:
        with subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
        ) as process:
            output, error = process.communicate(input=f"{password}\n")
        if error:
            raise SFTPError(f"pscp process raised the following error: {error}")

    except subprocess.CalledProcessError as e:
        raise SFTPError(f"Error downloading file: {e}")

    return output, error


def download_sftp_concurrently(
    username: str,
    password: str,
    host: str,
    sftp_file_paths: List[str],
    destination_folder_path: str,
    max_workers: int = 4,
) -> List[str]:
    """
    Download multiple files from an SFTP server to a local destination folder concurrently.

    Args:
        username (str): The SFTP username.
        password (str): The SFTP password.
        host (str): The SFTP host address.
        sftp_file_paths (List[str]): List of paths to files on the SFTP server.
        destination_folder_path (str): The local destination folder to save the downloaded files.
        max_workers (int, optional): The maximum number of concurrent download workers (default is 4).

    Returns:
        List[str]: A list of messages indicating the download status of each file.

    Example:
        download_sftp_concurrently(username="myuser", password="mypassword", host="sftp.example.com",
                                   sftp_file_paths=["/remote/file1.txt", "/remote/file2.txt"],
                                   destination_folder_path="/local/folder")
    """
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for file_path in sftp_file_paths:
            _, error = download_sftp(
                username, password, host, file_path, destination_folder_path
            )
            if error:
                results.append(f"Error downloading {file_path}: {error}")
            else:
                results.append(f"Downloaded {file_path} successfully.")

    return results


def list_files_with_properties(
    sftp_server: str,
    username: str,
    password: str = None,
    keyfile: str = None,
    sftp_path: str = "/",
) -> List[Dict[str, Any]]:
    """
    List files in a specific path of an SFTP server with their properties.

    Args:
        sftp_server (str): SFTP server address (e.g., "sftp.example.com").
        username (str): SFTP username.
        password (str, optional): SFTP password. Use either 'password' or 'keyfile', not both.
        keyfile (str, optional): Path to the private key file (PEM or PPK format). Use either 'password' or 'keyfile', not both.
        sftp_path (str, optional): Path within the SFTP server to list files from (default is root).

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing file properties.

    Raises:
        ValueError: If both 'password' and 'keyfile' are provided.

    Example:
        list_files_with_properties(
            sftp_server="sftp.example.com",
            username="myuser",
            password="mypassword",
            sftp_path="/remote/folder",
        )
    """
    if password and keyfile:
        raise ValueError("Use either 'password' or 'keyfile', not both.")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        if keyfile:
            ssh.connect(sftp_server, username=username, key_filename=keyfile)
        else:
            ssh.connect(sftp_server, username=username, password=password)

        sftp = ssh.open_sftp()
        sftp.chdir(sftp_path)
        file_list = []
        files = sftp.listdir()
        for filename in files:
            file_attributes = sftp.stat(filename)
            file_list.append(
                {
                    "filename": filename,
                    "size": file_attributes.st_size,
                    "permissions": file_attributes.st_mode,
                }
            )
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e from e
    finally:
        if "sftp" in locals():
            sftp.close()

    return file_list
