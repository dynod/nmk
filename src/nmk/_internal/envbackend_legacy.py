from pathlib import Path

from buildenv.loader import BuildEnvLoader


# Mimic the buildenv 2.0 environment backend
class EnvBackend:
    def __init__(self, project_path: Path):
        self._project_path = project_path
        self._pip_args = BuildEnvLoader(self._project_path).pip_args

    def is_mutable(self) -> bool:
        """
        State if this backend supports installing packages update once created

        :return: True if environment is mutable
        """

        # buildenv 1.X implementation: mutable (based on pip)
        return True


# Dummy factory
class EnvBackendFactory:
    @staticmethod
    def create(name: str, project_path: Path) -> EnvBackend:
        return EnvBackend(project_path)

    @staticmethod
    def detect(project_path: Path) -> EnvBackend:
        return EnvBackend(project_path)
