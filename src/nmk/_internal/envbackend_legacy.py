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
    def use_requirements(self) -> bool:
        """This backend uses requirements.txt files"""

        return True


# Dummy factory
class EnvBackendFactory:
    @staticmethod
    def create(name: str, project_path: Path) -> EnvBackend:
        return EnvBackend(project_path)

    @staticmethod
    def detect(project_path: Union[Path, None] = None) -> EnvBackend:
        return EnvBackend(project_path)
