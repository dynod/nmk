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
