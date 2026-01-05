import importlib.metadata
import logging
import sys
from pathlib import Path

from buildenv.loader import BuildEnvLoader

from nmk.utils import run_pip


# Mimic the buildenv 2.0 environment backend
class EnvBackend:
    def __init__(self, project_path: Path | None = None):
        self._project_path = project_path

    @property
    def version(self) -> int:
        """Backend version number (always legacy)"""

        return 1

    @property
    def name(self) -> str:
        """Backend name (always 'legacy')"""

        return "legacy"

    def is_mutable(self) -> bool:
        """
        State if this backend supports installing packages update once created

        :return: True if environment is mutable
        """

        # buildenv 1.X implementation: mutable (based on pip)
        return True

    @property
    def _pip_args(self) -> str:
        # Pip install args loaded from legacy buildenv configuration
        return BuildEnvLoader(self._project_path).pip_args if self._project_path is not None else ""

    @property
    def project_path(self) -> Path:
        assert self._project_path is not None, "Project path is not set"
        return self._project_path

    def subprocess(self, args: list[str], check: bool = True, cwd: Path | None = None, env: dict[str, str] | None = None, verbose: bool | None = None):
        # Delegate to deprecated run_pip utility
        return run_pip(args, extra_args=self._pip_args if args[0] == "install" else "")

    def add_packages(self, packages: list[str]):
        """
        Add packages to the environment

        :param packages: list of packages to add
        """

        self.subprocess(["install"] + packages)

    @property
    def venv_name(self) -> str:
        """venv folder name"""

        return "venv"

    @property
    def venv_root(self) -> Path:
        """venv root path"""

        return Path(sys.executable).parent.parent

    @property
    def use_requirements(self) -> bool:
        """This backend uses requirements.txt files"""

        return True

    def dump(self, output_file: Path, log_level: int = logging.INFO):
        """
        Dump installed packages to a requirements-style file
        """
        assert self._project_path is not None, "project path must be set to use dump"
        pkg_list = run_pip(["freeze"])
        output_file.write_text(pkg_list)

    def upgrade(self, full: bool = True, only_deps: bool = False) -> int:
        """
        Upgrade all packages in the environment to their latest versions

        :return: command exit code
        """
        self.add_packages(["-r", "requirements.txt"] + (["--upgrade"] if full else []))
        return 0

    def print_updates(self, old_packages: dict[str, str]):
        """
        Pretty print packages updates to stdout

        :param old_packages: map of old installed packages versions (indexed by package name)
        """

        # Nothing to do in legacy mode
        pass

    @property
    def installed_packages(self) -> dict[str, str]:
        """
        List installed packages in this environment

        :return: map of installed packages versions (indexed by package name)
        """

        # Just list stuff from distributions metadata
        return {dist.metadata["Name"]: dist.metadata["Version"] for dist in importlib.metadata.distributions()}


# Dummy factory
class EnvBackendFactory:
    @staticmethod
    def create(name: str, project_path: Path, verbose_subprocess: bool = True) -> EnvBackend:
        return EnvBackend(project_path)

    @staticmethod
    def detect(project_path: Path | None = None, verbose_subprocess: bool = True) -> EnvBackend:
        return EnvBackend(project_path)
