Module dsptools.data_transfer.sftp
==================================

Functions
---------

    
`download_sftp(username: str, password: str, host: str, sftp_file_path: str, destination_file_path: str, verbose: bool = False) ‑> str`
:   Download a file from an SFTP server to a local destination folder using pscp.
    
    Args:
        username (str): The SFTP username.
        password (str): The SFTP password.
        host (str): The SFTP host address.
        sftp_file_path (str): The path to the file on the SFTP server.
        destination_file_path (str): The local destination folder to save the downloaded file.
        verbose (bool): Whether to print a message upon successful download. Defaults to False
    
    Returns:
        Tuple[str, str]: A tuple containing the standard output and standard error from the pscp command.
    
    Example:
        download_sftp(username="myuser", password="mypassword", host="sftp.example.com",
                      sftp_file_path="/remote/file.txt", destination_folder_path="/local/folder")

    
`download_sftp_concurrently(username: str, password: str, host: str, file_pairs: List[Tuple[str, str]], max_workers: int = 4, verbose: bool = False) ‑> List[str]`
:   Download multiple files from an SFTP server to a local destination folder concurrently.
    
    Args:
        username (str): The SFTP username.
        password (str): The SFTP password.
        host (str): The SFTP host address.
        file_pairs (List[Tuple[str, str]]): A list of file pairs, where each pair is (SFTP file path, local destination file path).
        max_workers (int, optional): The maximum number of concurrent download workers (default is 4).
        verbose (bool): Whether to print a message upon successful download. Defaults to False.
    
    Returns:
        List[str]: A list of messages indicating the download status of each file.
    
    Example:
        download_sftp_concurrently(username="myuser", password="mypassword", host="sftp.example.com",
                                   file_pairs=[("/remote/file1.txt", "/local/file1.txt"), ("/remote/file2.txt", "/local/file2.txt")],
                                   max_workers=4, verbose=True)

    
`list_files_with_properties(sftp_server: str, username: str, password: str = None, keyfile: str = None, sftp_path: str = '/') ‑> List[Dict[str, Any]]`
:   List files in a specific path of an SFTP server with their properties.
    
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