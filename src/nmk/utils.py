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
    cp = subprocess.run(args, check=False, capture_output=True, text=True, encoding="utf-8", cwd=cwd)
    logger.debug(f">> rc: {cp.returncode}")
    logger.debug(">> stderr:")
    list(map(logger.debug, cp.stderr.splitlines(keepends=False)))
    logger.debug(">> stdout:")
    list(map(logger.debug, cp.stdout.splitlines(keepends=False)))
    assert not check or cp.returncode == 0, (
        f"command returned {cp.returncode}" + (f"\n{cp.stdout}" if len(cp.stdout) else "") + (f"\n{cp.stderr}" if len(cp.stderr) else "")
    )
    return cp


def run_pip(args: List[str], logger=NmkLogger) -> str:
    """
    Execute pip command, with logging
    """
    all_args = [sys.executable, "-m", "pip"] + args
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
