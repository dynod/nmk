import hashlib
import tarfile
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import requests

from nmk.logs import NmkLogger

# If remote is not that fast...
DOWNLOAD_TIMEOUT = 30

# Global first download flag (to log only once)
first_download = True


@lru_cache(maxsize=None)
def cache_remote(root: Path, remote: str) -> Path:
    # Make sure remote format is valid
    parts = remote.split("!")
    assert len(parts) in [1, 2] and all(len(p) > 0 for p in parts), f"Unsupported repo remote syntax: {remote}"
    remote_url = parts[0]
    sub_folder = Path(parts[1]) if len(parts) == 2 else Path()

    # Cache path
    repo_path = root / hashlib.sha1(remote.encode("utf-8")).hexdigest()

    # Something to cache?
    if not repo_path.exists():
        # First download?
        global first_download
        if first_download:
            first_download = False
            NmkLogger.info("arrow_double_down", "Caching remote references...")

        # Supported archive format?
        remote_exts = list(map(lambda e: e.lower(), Path(remote_url).suffixes))
        if len(remote_exts) and remote_exts[-1] == ".zip":
            # Extract zip without writing file to disk
            with requests.get(remote_url, timeout=DOWNLOAD_TIMEOUT, stream=True) as r, ZipFile(BytesIO(r.content)) as z:
                z.extractall(repo_path)
        elif len(remote_exts) and (".tar" in remote_exts or remote_exts[-1] == ".tgz"):
            # Extract tar without writing file to disk
            with requests.get(remote_url, timeout=DOWNLOAD_TIMEOUT, stream=True) as r, tarfile.open(fileobj=BytesIO(r.content), mode="r|*") as z:
                z.extractall(repo_path)
        else:
            raise Exception(f"Unsupported repo remote archive format: {''.join(remote_exts)}")

    # Path will be relative to extracted folder (is suffix is specified)
    return repo_path / sub_folder
