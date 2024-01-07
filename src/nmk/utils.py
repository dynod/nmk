import os
import subprocess
import sys
from pathlib import Path
from typing import List

from nmk.logs import NmkLogger


def run_with_logs(args: List[str], logger=NmkLogger, check: bool = True, cwd: Path = None) -> subprocess.CompletedProcess:
    """
    Execute subprocess, and logs output/error streams + error code
    """
    logger.debug(f"Running command: {args}")
    cp = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", errors="ignore", cwd=cwd)
    logger.debug(f">> rc: {cp.returncode}")
    logger.debug(">> stderr:")
    list(map(logger.debug, cp.stderr.splitlines(keepends=False)))
    logger.debug(">> stdout:")
    list(map(logger.debug, cp.stdout.splitlines(keepends=False)))
    assert not check or cp.returncode == 0, (
        f"command returned {cp.returncode}" + (f"\n{cp.stdout}" if len(cp.stdout) else "") + (f"\n{cp.stderr}" if len(cp.stderr) else "")
    )
    return cp


def run_pip(args: List[str], logger=NmkLogger, extra_args: str = "") -> str:
    """
    Execute pip command, with logging
    """
    all_args = [sys.executable, "-m", "pip"] + args + list(filter(lambda x: len(x) > 0, extra_args.strip(" ").split(" ")))
    return run_with_logs(all_args, logger).stdout


def is_windows() -> bool:
    """
    Returns true if running on Windows, false otherwise
    """
    return os.name == "nt"


def create_dir_symlink(target: Path, link: Path):
    """
    Create a directory symbolic link (or something close, according to the OS)

    Parameters:
        target(Path): path that will be pointed by the created link
        link(Path): created link location
    """
    # Ready to create symlink (platform dependent --> disable coverage)
    if is_windows():  # pragma: no branch
        # Windows specific: create a directory junction (similar to a Linux symlink)
        import _winapi  # pragma: no cover

        _winapi.CreateJunction(str(target), str(link))  # pragma: no cover
    else:  # pragma: no cover
        # Standard symlink
        os.symlink(target, link)  # pragma: no cover


def is_condition_set(value) -> bool:
    """
    Verify if condition is considered to be "true", depending on provided value

    Parameters:
        value(Any): value to be evaluated
    """
    # Condition depends on value type
    if isinstance(value, list) or isinstance(value, dict):
        # List/dict: should not be empty
        return len(value) > 0
    if isinstance(value, str):
        # String:
        # "false" (case insensitive), 0, empty --> False
        # anything else --> True
        return len(value) > 0 and value != "0" and value.lower() != "false"
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    raise AssertionError(f"Can't compute value type to evaluate conditional behavior: {value}")
