import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import jsonschema
import yaml

from nmk.errors import NmkFileLoadingError
from nmk.logs import NmkLogger
from nmk.model.cache import cache_remote
from nmk.model.keys import NmkRootConfig
from nmk.model.model import NmkModel
from nmk.model.resolver import NmkConfigResolver

# Known URL schemes
GITHUB_SCHEME = "github:"
URL_SCHEMES = ["http:", "https:", GITHUB_SCHEME]

# Github URL extraction pattern
GITHUB_PATTERN = re.compile("github://([^ /]+)/([^ /]+)/([^ /]+)(/.+)?")


# Model keys
class NmkModelK:
    REFS = "refs"
    REMOTE = "remote"
    LOCAL = "local"
    CONFIG = "config"
    RESOLVER = "__resolver__"


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
    def __init__(self, project_ref: str, repo_cache: Path, model: NmkModel, refs: List[str]):
        # Init properties
        self._repos = None
        self.repo_cache = repo_cache

        try:
            # Resolve local file from project reference
            self.file = self.resolve_project(project_ref)

            # Remember project dir if first file
            if not len(refs):
                p_dir = self.file.parent.resolve()
                NmkLogger.debug(f"{NmkRootConfig.PROJECT_DIR} updated to {p_dir}")
                model.config[NmkRootConfig.PROJECT_DIR].static_value = p_dir

            # Remember file in model (if not already done)
            if self.file in model.files:
                # Already known file
                NmkLogger.debug(f"{self.file} file already loaded, ignore...")
                return
            model.files[self.file] = self

            # Load YAML model
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

            # Load references
            for ref_file_path in self.refs:
                NmkModelFile(ref_file_path, self.repo_cache, model, refs + [project_ref])

            # Load config
            self.load_config(model)

        except Exception as e:
            if isinstance(e, NmkFileLoadingError):
                raise e
            raise NmkFileLoadingError(
                project_ref, str(e) + (("\n" + "\n".join(map(lambda r: f" --> referenced from {r}", refs))) if len(refs) else "")
            ).with_traceback(e.__traceback__)

    def resolve_project(self, project_ref: str) -> Path:
        # Look at first segment
        project_path = Path(project_ref)
        scheme_candidate = project_path.parts[0]
        if not project_path.is_absolute() and scheme_candidate in URL_SCHEMES:
            # Cache-able reference
            return cache_remote(self.repo_cache, self.convert_url(project_ref))

        # Default case: assumed to be a local path
        return project_path

    def convert_url(self, url: str) -> str:
        # Github-like URL
        if url.startswith(GITHUB_SCHEME):
            m = GITHUB_PATTERN.match(url)
            assert m is not None, f"Invalid github:// URL: {url}"
            # Pattern groups:
            # 1: people
            # 2: repo
            # 3: version -> tag is start with a digit, assume branch otherwise
            # 4: sub-path (optional)
            people, repo, version, subpath = tuple(m.groups())
            first_char = version[0]
            is_tag = first_char >= "0" and first_char <= "9"
            return f"https://github.com/{people}/{repo}/archive/refs/{'tags' if is_tag else 'heads'}/{version}.zip!{repo}-{version}{subpath}"

        # Default: no conversion
        return url

    def resolve_ref(self, ref: str) -> str:
        # Repo relative reference?
        for r_name, r in self.repos.items():
            if ref.startswith(f"<{r_name}>/"):
                return self.resolve_repo_ref(ref, r)

        # Repo-like reference?
        assert not ref.startswith("<"), f"Unresolved repo-like relative reference: {ref}"

        # Relative local reference?
        return self.make_absolute(Path(ref))

    def make_absolute(self, p: Path) -> str:
        # Make relative to current file, if needed
        if not p.is_absolute():
            p = self.file.parent / p
        NmkLogger.warning(f"Absolute path (not portable) used in project: {p}")
        return str(p)

    def resolve_repo_ref(self, ref: str, repo: NmkRepo) -> str:
        # Reckon relative part of the reference
        rel_ref = Path(*list(Path(ref).parts)[1:])

        # Local path exists?
        if repo.local is not None:
            local_repo_dir = Path(self.make_absolute(repo.local))
            if local_repo_dir.is_dir():
                return str(local_repo_dir / rel_ref)

        # Nothing found locally: go with remote reference
        return f"{repo.remote}{'!' if '!' not in repo.remote else '/'}{rel_ref}"

    @property
    def all_refs(self) -> List[str]:
        return self.model[NmkModelK.REFS] if NmkModelK.REFS in self.model else []

    @property
    def refs(self) -> List[str]:
        return list(map(self.resolve_ref, filter(lambda r: isinstance(r, str), self.all_refs)))

    @property
    def repos(self) -> Dict[str, NmkRepo]:
        # Lazy loading
        if self._repos is None:
            self._repos = {}
            for repo_dict in filter(lambda r: isinstance(r, dict), self.all_refs):
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

    def load_config(self, model: NmkModel):
        # Is this file providing config items?
        if NmkModelK.CONFIG not in self.model:
            return

        # Iterate on config items
        for name, candidate in self.model[NmkModelK.CONFIG].items():
            # Complex item?
            if isinstance(candidate, dict) and NmkModelK.RESOLVER in candidate:
                # With a resolver
                model.add_config(name, self.file.parent, resolver=model.load_class(candidate[NmkModelK.RESOLVER], NmkConfigResolver))
            else:
                # Simple config item, direct add
                model.add_config(name, self.file.parent, candidate)
