import hashlib
import tarfile
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import requests

# If remote is not that fast...
DOWNLOAD_TIMEOUT = 30


@lru_cache(maxsize=None)
def cache_remote(root: Path, remote: str) -> Path:
    # Cache path
    repo_path = root / hashlib.sha1(remote.encode("utf-8")).hexdigest()

    # Something to cache?
    if not repo_path.exists():
        # Supported archive format?
        remote_path = Path(remote)
        remote_exts = list(map(lambda e: e.lower(), remote_path.suffixes))
        if len(remote_exts) and remote_exts[-1] == ".zip":
            # Extract zip without writing file to disk
            with requests.get(remote, timeout=DOWNLOAD_TIMEOUT, stream=True) as r, ZipFile(BytesIO(r.content)) as z:
                z.extractall(repo_path)
        elif len(remote_exts) and (".tar" in remote_exts or remote_exts[-1] == ".tgz"):
            # Extract tar without writing file to disk
            with requests.get(remote, timeout=DOWNLOAD_TIMEOUT, stream=True) as r, tarfile.open(fileobj=BytesIO(r.content), mode="r|*") as z:
                z.extractall(repo_path)
        else:
            raise Exception(f"Unsupported repo remote archive format: {''.join(remote_exts)}")

    return repo_path
