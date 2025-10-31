import sys
from pathlib import Path
from typing import Union

from buildenv.loader import BuildEnvLoader

from nmk.utils import run_pip


# Mimic the buildenv 2.0 environment backend
class EnvBackend:
    def __init__(self, project_path: Union[Path, None] = None):
        self._project_path = project_path

    def is_mutable(self) -> bool:
        """
        State if this backend supports installing packages update once created

        :return: True if environment is mutable
        """

        # buildenv 1.X implementation: mutable (based on pip)
        return True

    def add_packages(self, packages: list[str]):
        """
        Add packages to the environment

        :param packages: list of packages to add
        """

        # Delegate to deprecated run_pip utility
        pip_args = BuildEnvLoader(self._project_path).pip_args if self._project_path is not None else ""
        run_pip(["install"] + packages, extra_args=pip_args)

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

    def is_legacy(self) -> bool:
        """
        State if this backend is considered legacy
        """
        return True

    def lock(self, lockfile: Union[Path, None] = None) -> int:
        """
        Create a lockfile for this environment, so that next time the environment is loaded, it will be restored to this state

        :param lockfile: path to the lockfile to create (None to use default path for this backend)
        :return: command exit code
        """
        assert self._project_path is not None, "project path must be set to use lock"
        pkg_list = run_pip(["freeze"])
        with (lockfile or self._project_path / "requirements.txt").open("w") as f:
            f.write(pkg_list)

        return 0

    def upgrade(self, full: bool = True) -> int:
        """
        Upgrade all packages in the environment to their latest versions

        :return: command exit code
        """
        self.add_packages(["-r", "requirements.txt"] + (["--upgrade"] if full else []))
        return 0


# Dummy factory
class EnvBackendFactory:
    @staticmethod
    def create(name: str, project_path: Path, verbose_subprocess: bool = True) -> EnvBackend:
        return EnvBackend(project_path)

    @staticmethod
    def detect(project_path: Union[Path, None] = None, verbose_subprocess: bool = True) -> EnvBackend:
        return EnvBackend(project_path)
