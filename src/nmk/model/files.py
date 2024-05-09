import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Dict, List, Union

import jsonschema
import yaml
from buildenv import BuildEnvLoader
from rich.emoji import Emoji
from rich.text import Text

from nmk.errors import NmkFileLoadingError
from nmk.logs import NmkLogger
from nmk.model.builder import NmkTaskBuilder
from nmk.model.cache import PIP_SCHEME, cache_remote
from nmk.model.config import NmkConfig, NmkDictConfig, NmkListConfig
from nmk.model.keys import NmkRootConfig
from nmk.model.model import NmkModel, contribute_python_path
from nmk.model.resolver import NmkConfigResolver
from nmk.model.task import NmkTask

# Known URL schemes
GITHUB_SCHEME = "github:"
URL_SCHEMES = ["http:", "https:", GITHUB_SCHEME, PIP_SCHEME]

# Github URL extraction pattern
GITHUB_PATTERN = re.compile(GITHUB_SCHEME + "//([^ /]+)/([^ /]+)/([^ /]+)(/.+)?")


# Model keys
class NmkModelK:
    REFS = "refs"
    REMOTE = "remote"
    LOCAL = "local"
    OVERRIDE = "override"
    CONFIG = "config"
    RESOLVER = "__resolver__"
    TASKS = "tasks"
    DESCRIPTION = "description"
    EMOJI = "emoji"
    BUILDER = "builder"
    PARAMS = "params"
    DEFAULT = "default"
    DEPS = "deps"
    APPEND_TO = "appendToDeps"
    PREPEND_TO = "prependToDeps"
    INPUT = "input"
    OUTPUT = "output"
    SILENT = "silent"
    IF = "if"
    UNLESS = "unless"
    PATH = "path"


# Data class for repository reference
@dataclass
class NmkRepo:
    name: str
    remote: str
    local: Path = None
    override: bool = False


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
        self.global_model = model
        self.project_ref = project_ref
        self.parent_refs = refs

        try:
            # Resolve local file from project reference
            self.file = self.resolve_project(project_ref)

            # Remember project dir if first file
            if not len(refs):
                p_dir = self.file.parent.resolve()
                NmkLogger.debug(f"{NmkRootConfig.PROJECT_DIR} updated to {p_dir}")
                model.config[NmkRootConfig.PROJECT_DIR].static_value = p_dir
                model.config[NmkRootConfig.PROJECT_NMK_DIR].static_value = p_dir / ".nmk"

                # Also remember pip args from buildenv
                model.pip_args = BuildEnvLoader(p_dir).pip_args

            # Remember file path in model (to avoid recursive loading)
            if self.file in model.file_paths:
                # Already known file
                NmkLogger.debug(f"{self.file} file already loaded, ignore...")
                return
            model.file_paths.append(self.file)

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

            # Remember file model (in loading order)
            model.file_models[self.file] = self

        except Exception as e:
            if isinstance(e, NmkFileLoadingError):
                raise e
            self.__raise_with_refs(e)

    def __raise_with_refs(self, e: Exception):
        # Raise an exception with parent files
        raise NmkFileLoadingError(
            self.project_ref, str(e) + (("\n" + "\n".join(f" --> referenced from {r}" for r in self.parent_refs)) if len(self.parent_refs) else "")
        ).with_traceback(e.__traceback__)

    def is_url(self, project_ref: str) -> bool:
        # Is this ref a known URL?
        project_path = Path(project_ref)
        scheme_candidate = project_path.parts[0]
        return not project_path.is_absolute() and scheme_candidate in URL_SCHEMES

    def resolve_project(self, project_ref: str) -> Path:
        # URL?
        if self.is_url(project_ref):
            # Cache-able reference
            return cache_remote(self.repo_cache, self.convert_url(project_ref), self.global_model.pip_args)

        # Default case: assumed to be a local path
        return Path(project_ref)

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

        # Remote ref may be overridden by a local path
        checked_ref = self.global_model.check_remote_ref(ref) if self.is_url(ref) else ref
        if self.is_url(checked_ref):
            # Still a remote ref (not overridden)
            return checked_ref
        if checked_ref == ref:
            # Local ref (not overridden)
            return self.make_absolute(Path(checked_ref))
        return checked_ref

    def make_absolute(self, p: Path) -> str:
        # Make relative to current file, if needed
        current_file_path = (self.file if self.file.is_absolute() else Path.cwd() / self.file).parent
        if not p.is_absolute():
            p = current_file_path / p
        else:
            NmkLogger.warning(f"Absolute path (not portable) used in project: {p}")
        return str(p)

    def resolve_repo_ref(self, ref: str, repo: NmkRepo) -> str:
        # Reckon relative part of the reference
        rel_ref = Path(*list(Path(ref).parts)[1:])

        # Local path exists?
        if repo.local is not None:
            assert not repo.override or repo.local.is_dir(), f'Local path "{repo.local}" not found for repository "{repo.name}" using override option'
            if repo.local.is_dir():
                return str(repo.local / rel_ref)

        # Nothing found locally: go with remote reference
        # Use "as_posix" to keep "/" slashes in URL even on Windows
        return f"{repo.remote}{'!' if '!' not in repo.remote and not repo.remote.startswith(GITHUB_SCHEME) else '/'}{rel_ref.as_posix()}"

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
                        r = NmkRepo(
                            k,
                            r[NmkModelK.REMOTE],
                            Path(self.make_absolute(Path(r[NmkModelK.LOCAL]))) if NmkModelK.LOCAL in r else None,
                            r[NmkModelK.OVERRIDE] if NmkModelK.OVERRIDE in r else False,
                        )
                        new_repos[k] = r

                        # If override option is set, remember remote ref to be replaced
                        if r.override:
                            self.global_model.replace_remote(r.remote, r.local)
                    else:
                        # Simple repo item, with only remote reference
                        new_repos[k] = NmkRepo(k, r)

                # Handle possible duplicates (if using distinct dictionaries in distinct array items)
                conflicts = list(filter(lambda k: k in self._repos, new_repos.keys()))
                assert len(conflicts) == 0, f"Duplicate repo names: {', '.join(conflicts)}"
                self._repos.update(new_repos)

        return self._repos

    def load_config(self):
        try:
            # Is this file providing config items?
            if NmkModelK.CONFIG not in self.model:
                return

            # Iterate on config items
            for name, candidate in self.model[NmkModelK.CONFIG].items():
                # Complex item?
                if isinstance(candidate, dict) and NmkModelK.RESOLVER in candidate:
                    # With a resolver, and eventually params
                    self.global_model.add_config(
                        name,
                        self.file.parent,
                        resolver=self.global_model.load_class(candidate[NmkModelK.RESOLVER], NmkConfigResolver),
                        resolver_params=self.load_property(candidate, NmkModelK.PARAMS, mapper=lambda v, n: self.load_param_dict(v, n), task_name=name),
                    )
                else:
                    # Simple config item, direct add
                    self.global_model.add_config(name, self.file.parent, candidate)
        except Exception as e:
            self.__raise_with_refs(e)

    def load_tasks(self):
        try:
            # Is this file providing config items?
            if NmkModelK.TASKS not in self.model:
                return

            # Iterate on task items
            for name, candidate in self.model[NmkModelK.TASKS].items():
                # Contribute to model
                self.global_model.add_task(
                    NmkTask(
                        name,
                        self.load_property(candidate, NmkModelK.DESCRIPTION),
                        self.load_property(candidate, NmkModelK.SILENT, False),
                        self.load_property(candidate, NmkModelK.EMOJI, mapper=self.load_emoji),
                        self.load_property(candidate, NmkModelK.BUILDER, mapper=lambda cls: self.global_model.load_class(cls, NmkTaskBuilder)),
                        self.load_property(candidate, NmkModelK.PARAMS, mapper=lambda v, n: self.load_param_dict(v, n), task_name=name),
                        self.load_property(
                            candidate, NmkModelK.DEPS, [], mapper=lambda dp: [i for n, i in enumerate(dp) if i not in dp[:n]]
                        ),  # Remove duplicates
                        self.load_property(candidate, NmkModelK.APPEND_TO),
                        self.load_property(candidate, NmkModelK.PREPEND_TO),
                        self.load_property(candidate, NmkModelK.INPUT, mapper=lambda v, n: self.load_str_list_cfg(v, n, NmkModelK.INPUT), task_name=name),
                        self.load_property(candidate, NmkModelK.OUTPUT, mapper=lambda v, n: self.load_str_list_cfg(v, n, NmkModelK.OUTPUT), task_name=name),
                        self.load_property(candidate, NmkModelK.IF, mapper=lambda v, n: self.load_str_cfg(v, n, NmkModelK.IF), task_name=name),
                        self.load_property(candidate, NmkModelK.UNLESS, mapper=lambda v, n: self.load_str_cfg(v, n, NmkModelK.UNLESS), task_name=name),
                        self.global_model,
                    ),
                )

                # If declared as default task, remember it in model
                if self.load_property(candidate, NmkModelK.DEFAULT, False):
                    self.global_model.set_default_task(name)

        except Exception as e:
            self.__raise_with_refs(e)

    def load_paths(self):
        try:
            # Is this file providing python path contribution?
            if NmkModelK.PATH not in self.model:
                return

            # Prepare paths list
            contributed_paths = []
            for p in self.model[NmkModelK.PATH]:
                candidate = Path(p)
                if not candidate.is_absolute():  # pragma: no branch
                    candidate = self.file.parent / candidate
                contributed_paths.append(candidate)

            # Extend python path
            contribute_python_path(contributed_paths)

        except Exception as e:
            self.__raise_with_refs(e)

    def load_emoji(self, candidate: str) -> Union[Emoji, Text]:
        # May be a renderable text
        return Text.from_markup(candidate) if ":" in candidate else Emoji(candidate)

    def load_property(self, candidate: dict, key: str, default=None, mapper: Callable = None, task_name: str = None):
        # Load value from yml model (if any, otherwise handle default value), and potentially map it
        mapper = mapper if mapper is not None else (lambda x: x if task_name is None else lambda x, v: x)
        value = candidate[key] if key in candidate else default
        if task_name is None:
            return mapper(value) if value is not None else None
        else:
            return mapper(value, task_name) if value is not None else None

    def load_str_list_cfg(self, v: list, task_name: str, in_out: str) -> NmkListConfig:
        # Add string list config
        return self.global_model.add_config(f"{task_name}_{in_out}", self.file.parent, v if isinstance(v, list) else [v], task_config=True)

    def load_str_cfg(self, v: list, task_name: str, condition: str) -> NmkConfig:
        # Add string config
        return self.global_model.add_config(f"{task_name}_{condition}", self.file.parent, v, task_config=True)

    def load_param_dict(self, v: dict, task_name: str) -> NmkDictConfig:
        # Map builder/resolver parameters
        return self.global_model.add_config(f"{task_name}_params", self.file.parent, v, task_config=True)
