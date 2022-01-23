from argparse import Namespace
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import jsonschema
import yaml

from nmk.cache import cache_remote
from nmk.logs import NmkLogger

# Loading error prefix
ERROR_PREFIX = "While loading "


# Model keys
class NmkModelK:
    REFS = "refs"
    REMOTE = "remote"
    LOCAL = "local"


# Data class for repository reference
@dataclass
class NmkRepo:
    name: str
    remote: str
    local: Path = None


@lru_cache(maxsize=None)
def load_schema() -> dict:
    model_file = Path(__file__).parent / "model.yml"
    NmkLogger.debug(f"Loading model schema from {model_file}")
    with model_file.open() as f:
        schema = yaml.full_load(f)
    return schema


# Recursive model file loader
class NmkModelFile:
    def __init__(self, file: Path, repo_cache: Path):
        # Load YAML model
        self.file = file
        self.repo_cache = repo_cache
        assert self.file.is_file(), "Project file not found"
        NmkLogger.debug(f"Loading model from {self.file}")
        try:
            with self.file.open() as f:
                self.model = yaml.full_load(f)
        except Exception as e:
            raise Exception(f"Project is malformed: {e}")

        # Validate model against grammar
        try:
            jsonschema.validate(self.model, load_schema())
        except Exception as e:
            raise Exception(f"Project contains invalid data: {e}")

        # Cached items
        self._repos = None

    def resolve_ref(self, ref: str) -> str:
        # Repo relative reference?
        for r_name, r in self.repos.items():
            if ref.startswith(f"<{r_name}>/"):
                return self.resolve_repo_ref(ref, r)

        # Repo-like reference?
        assert not ref.startswith("<"), f"Unresolved repo-like relative reference: {ref}"

        # Relative local reference?
        return self.make_absolute(Path(ref))

    def make_absolute(self, p: Path) -> Path:
        # Make relative to current file, if needed
        if not p.is_absolute():
            p = self.file.parent / p
        NmkLogger.warning(f"Absolute path (not portable) used in project: {p}")
        return p

    def resolve_repo_ref(self, ref: str, repo: NmkRepo) -> Path:
        # Reckon relative part of the reference
        rel_ref = Path(*list(Path(ref).parts)[1:])

        # Local path exists?
        if repo.local is not None:
            local_repo_dir = self.make_absolute(repo.local)
            if local_repo_dir.is_dir():
                return local_repo_dir / rel_ref

        # Nothing found locally: go with remote reference
        return cache_remote(self.repo_cache, repo.remote) / rel_ref

    @property
    def refs(self) -> List[str]:
        return list(map(self.resolve_ref, filter(lambda r: isinstance(r, str), self.model[NmkModelK.REFS])))

    @property
    def repos(self) -> Dict[str, NmkRepo]:
        # Lazy loading
        if self._repos is None:
            self._repos = {}
            for repo_dict in filter(lambda r: isinstance(r, dict), self.model[NmkModelK.REFS]):
                # Instantiate new repos
                new_repos = {}
                for k, r in repo_dict.items():
                    if isinstance(r, dict):
                        # Full repo item, with all details
                        new_repos[k] = NmkRepo(k, r[NmkModelK.REMOTE], Path(r[NmkModelK.LOCAL]) if NmkModelK.LOCAL in r else None)
                    else:
                        # Simple repo item, with only remote reference
                        new_repos[k] = NmkRepo(k, r)

                # Handle possible duplicates (if using distinct dictionaries in distinct array items)
                conflicts = list(filter(lambda k: k in self._repos, new_repos.keys()))
                assert len(conflicts) == 0, f"Duplicate repo names: {', '.join(conflicts)}"
                self._repos.update(new_repos)

        return self._repos


class NmkModel:
    def __init__(self, args: Namespace):
        # Iterate recursively on model files
        self.files = {}
        try:
            self.load_model([NmkModelFile(args.project, args.output / "nmk-cache")])
        except Exception as e:
            self.raise_prettier_error(e, args.project)

    def load_model(self, files: List[NmkModelFile], ref_from: List[str] = None):
        # Remember known files
        self.files.update({f.file: f for f in files})

        # Iterate on loaded files
        for file in files:
            try:
                # Recursively load model from new references
                new_ref = (ref_from if ref_from is not None else []) + [f" --> referenced from {file.file}"]
                new_files = []
                for ref_file_path in filter(lambda f: f not in self.files, file.refs):
                    try:
                        new_files.append(NmkModelFile(ref_file_path, file.repo_cache))
                    except Exception as e:
                        self.raise_prettier_error(e, ref_file_path, new_ref)
                self.load_model(new_files, new_ref)
            except Exception as e:
                # Add details to loading error
                self.raise_prettier_error(e, file.file, ref_from)

    def raise_prettier_error(self, e: Exception, file_path: Path, ref_from: List[str] = None):
        if str(e).startswith(ERROR_PREFIX):
            raise e
        raise Exception(f"{ERROR_PREFIX}{file_path}: {e}" + (("\n" + "\n".join(ref_from)) if ref_from is not None else "")).with_traceback(e.__traceback__)
