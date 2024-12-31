import hashlib
import importlib.resources
import re
import shutil
import tarfile
from functools import cache
from pathlib import Path
from zipfile import ZipFile

import requests

from nmk.logs import NmkLogger
from nmk.utils import run_pip

# If remote is not that fast...
DOWNLOAD_TIMEOUT = 30

# Pattern for pip-relative reference
PIP_SCHEME = "pip:"
PIP_PATTERN = re.compile(PIP_SCHEME + "//(([^<>=/ ]+)[^/ ]*)$")

# Global first download flag (to log only once)
first_download = True


def log_install():
    # First download?
    global first_download
    if first_download:  # pragma: no branch
        first_download = False
        NmkLogger.info("arrow_double_down", "Caching remote references...")


# Referenced wheels set
_referenced_wheels: set[str] = set()


# Remember referenced wheels
def _remember_referenced_wheel(referenced_wheel: str):
    _referenced_wheels.add(referenced_wheel)


# Get referenced wheels from references
def get_referenced_wheels() -> list[str]:
    return sorted(list(_referenced_wheels))


@cache
def pip_install(url: str, extra_pip_args: str) -> Path:
    # Check pip names
    m = PIP_PATTERN.match(url)
    assert m is not None, f"Malformed pip reference: {url}"
    pip_ref = m.group(1)
    wheel_name = m.group(2)
    _remember_referenced_wheel(wheel_name)
    package_name = wheel_name.replace("-", "_")

    # Look for installed python module
    def find_python_module(module) -> Path:
        return Path(importlib.resources.files(package_name))

    try:
        # Something to install?
        repo_path = find_python_module(package_name)
    except ModuleNotFoundError:
        # Module not found: trigger install
        log_install()

        # Trigger pip
        run_pip(["install", pip_ref], extra_args=extra_pip_args)

        # Try to find path again
        try:
            repo_path = find_python_module(package_name)
        except ModuleNotFoundError as e:
            # Mismatch between wheel and module name, can't find files...
            raise ValueError(f"Can't find module '{package_name}' even after having installed '{pip_ref}' package") from e

    return repo_path


def safe_tar_extract(tar_path: Path, target_path: Path):
    # Protect against ".." folders in tar -- see https://github.com/advisories/GHSA-gw9q-c7gh-j9vm (CVE-2007-4559)
    with tarfile.open(name=tar_path, mode="r|*") as tar:
        for member in tar.getmembers():
            dest_path = target_path / member.name
            try:
                # Destination path *must* be a sub-folder/file of target path
                dest_path.relative_to(target_path)
            except ValueError as e:  # pragma: no cover
                # Invalid entry
                raise AssertionError(f"Invalid path in tar archive: {member.name}") from e

    # Extract all
    with tarfile.open(name=tar_path, mode="r|*") as tar:
        tar.extractall(target_path)


def download_archive(repo_path: Path, url: str) -> Path:
    # Download binary file
    dest_file = repo_path.parent / (repo_path.name + "".join(Path(url).suffixes))
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    NmkLogger.debug(f"Downloading {url} to {dest_file}...")
    with requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True) as r, dest_file.open("wb") as f:
        shutil.copyfileobj(r.raw, f)
    return dest_file


@cache
def download_file(root: Path, url: str) -> Path:
    # Cache path
    repo_path = root / hashlib.sha1(url.encode("utf-8")).hexdigest()

    # Something to cache?
    if not repo_path.exists():
        log_install()

        # Supported archive format?
        url_path = Path(url)
        remote_exts = [e.lower() for e in url_path.suffixes]
        if len(remote_exts) and remote_exts[-1] == ".zip":
            # Download and extract zip
            with ZipFile(download_archive(repo_path, url)) as z:
                z.extractall(repo_path)
        elif len(remote_exts) and (".tar" in remote_exts or remote_exts[-1] == ".tgz"):
            # Download and extract tar
            safe_tar_extract(download_archive(repo_path, url), repo_path)
        elif len(remote_exts) and remote_exts[-1] == ".yml":
            # Download repo yml
            repo_path.mkdir(parents=True, exist_ok=True)
            repo_path = repo_path / url_path.name
            with requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True) as r, repo_path.open("w") as f:
                f.write(r.text)
        else:
            raise Exception(f"Unsupported remote file format: {''.join(remote_exts)}")

    # Return downloaded (+extracted) local path
    return repo_path


@cache
def cache_remote(root: Path, remote: str, extra_pip_args: str) -> Path:
    # Make sure remote format is valid
    parts = remote.split("!")
    assert len(parts) in [1, 2] and all(len(p) > 0 for p in parts), f"Unsupported repo remote syntax: {remote}"
    remote_url = parts[0]
    sub_folder = Path(parts[1]) if len(parts) == 2 else Path()

    # Path will be relative to extracted folder (if suffix is specified)
    out = (pip_install(remote_url, extra_pip_args) if remote_url.startswith(PIP_SCHEME) else download_file(root, remote_url)) / sub_folder
    NmkLogger.debug(f"Cached remote path: {remote} --> {out}")
    return out
