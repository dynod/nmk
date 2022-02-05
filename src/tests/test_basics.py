from pathlib import Path

from tests.utils import NmkTester


class TestBasics(NmkTester):
    def test_project_not_found(self):
        self.nmk(Path("/missing/project.yml"), expected_error="While loading /missing/project.yml: Project file not found")

    def test_simplest_project_with_logs(self):
        expected_log = self.test_folder / "some.log"
        self.nmk("simplest.yml", extra_args=["--log-file", expected_log.as_posix()], with_logs=True)
        assert expected_log.is_file()

    def test_simplest_project_without_logs(self):
        self.nmk("simplest.yml", extra_args=["--log-file", ""], with_logs=True)
        assert not self.nmk_cache.exists()
        self.check_logs("Nothing to do")

    def test_invalid_yml(self):
        self.nmk("invalid.yml", expected_error="While loading {project}: Project is malformed: ")

    def test_empty_validation_fails(self):
        self.nmk("empty.yml", expected_error="While loading {project}: Project contains invalid data: ")

    def test_root_not_found(self):
        self.nmk("empty.yml", extra_args=["--root", "/missing/folder"], expected_rc=1)
