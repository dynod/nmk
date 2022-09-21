import shutil
from pathlib import Path
from re import Pattern
from typing import List, Union

from pytest_multilog import TestHelper

from nmk.__main__ import nmk
from nmk.model.files import URL_SCHEMES


class NmkBaseTester(TestHelper):
    @property
    def nmk_cache(self) -> Path:
        return self.test_folder / ".nmk"

    @property
    def templates_root(self) -> Path:  # pragma: no cover
        raise AssertionError("Should be overridden!")

    def template(self, name: str) -> Path:
        return self.templates_root / name

    def prepare_project(self, name: str) -> Path:
        # Copy template in test folder
        src = self.template(name)
        dst = self.test_folder / src.name
        shutil.copyfile(src, dst)
        return dst

    def nmk(
        self, project: Union[Path, str], with_logs: bool = False, extra_args: List[str] = None, expected_error: Union[str, Pattern] = None, expected_rc: int = 0
    ):
        # Prepare args and run nmk
        if isinstance(project, str) and not any(project.startswith(scheme) for scheme in URL_SCHEMES):
            project = self.template(project)
        if isinstance(project, Path):
            project = project.as_posix()
        args = ["--root", self.test_folder.as_posix(), "-p", project]
        if not with_logs:
            args.append("--no-logs")
        if extra_args is not None:
            args.extend(extra_args)
        rc = nmk(args)

        # Expected OK?
        expected_rc = 1 if expected_error is not None else expected_rc
        assert rc == expected_rc, f"Unexpected nmk rc: {rc}"
        if expected_error is not None:
            if isinstance(expected_error, str):
                self.check_logs(f"nmk] ERROR 💀 - {expected_error.format(project=project)}")
            else:
                # Use pattern directly
                self.check_logs(expected_error)
