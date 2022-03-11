import shutil
from pathlib import Path
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

    def nmk(self, project: Union[Path, str], with_logs: bool = False, extra_args: List[str] = None, expected_error: str = None, expected_rc: int = 0):
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
            self.check_logs(f"nmk] ERROR 💀 - {expected_error.format(project=project)}")

    def check_logs_order(self, expected: List[str]):
        # Get logs content
        with self.test_logs.open("r") as f:
            lines = f.readlines()

            # Verify all patterns are found in logs, in specified order
            start_index = 0
            not_found_patterns = list(expected)
            for expected_pattern in expected:
                for current_index, line_to_check in enumerate(lines[start_index:], start_index):  # pragma: no branch
                    if expected_pattern in line_to_check:
                        # Line found!
                        start_index = current_index + 1
                        not_found_patterns.remove(expected_pattern)
                        break
            assert len(not_found_patterns) == 0, f"Missing patterns: {not_found_patterns}"
