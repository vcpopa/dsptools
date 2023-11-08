from __future__ import annotations
from typing import Union
import psutil


#!THIS IS TO ENBALE THE LOGIC OF dsptools.utils.execution.conditional_polling
def list_child_processes(parent_pid: int) -> Union[int, None]:
    """
    List child processes of a given parent process.

    Args:
        parent_pid (int): The parent process ID to search for child processes.

    Returns:
        Union[int, None]: The process ID of a child process, or None if no child process is found.
    """
    for process in psutil.process_iter(attrs=["pid", "ppid", "name"]):
        process_info = process.info
        if process_info["ppid"] == parent_pid:
            return process_info["pid"]
    return None


def check_pid(child_pid: int) -> Union[int, None]:
    """
    Check if a process ID is valid.

    Args:
        child_pid (int): The process ID to check.

    Returns:
        Union[int, None]: The same process ID if valid, or None if the process ID is None.
    """
    if child_pid is not None:
        return child_pid
    return None


def kill_pid(pid: int) -> Union[int, None]:
    """
    Terminate a process with the given process ID and check if it was successfully killed.

    Args:
        pid (int): The process ID to terminate.

    Returns:
        Union[int, None]: The process ID if it was successfully killed, or None if not.
    """
    try:
        pid_process = psutil.Process(pid)
        pid_process.terminate()
        pid_process.wait(5)  # Wait for the process to exit (5 seconds timeout)
        if not psutil.pid_exists(pid):
            return pid
        return None
    except psutil.NoSuchProcess:
        return None
