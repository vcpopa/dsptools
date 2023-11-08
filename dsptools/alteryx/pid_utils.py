from __future__ import annotations
from typing import Union
import psutil

def list_child_processes(parent_pid: int) -> Union[int,None]:
    for process in psutil.process_iter(attrs=['pid', 'ppid', 'name']):
        process_info = process.info
        if process_info['ppid'] == parent_pid:
            return process_info['pid']
    return None

def check_pid(child_pid: int) -> Union[int,None]:
    if child_pid is not None:
        return child_pid
    return None


def kill_pid(pid: int) -> Union[int,None]:
    try:
        pid_process = psutil.Process(pid)
        pid_process.terminate()
        pid_process.wait(5)  # Wait for the process to exit (5 seconds timeout)
        if not psutil.pid_exists(pid):

            return pid

        return None
    except psutil.NoSuchProcess:
        return None