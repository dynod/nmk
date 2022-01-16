from pathlib import Path

from tests.utils import NmkTester


class TestBasics(NmkTester):
    def test_project_not_found(self):
        self.nmk(Path("/missing/project.yml"), expected_error="Project file not found: /missing/project.yml")

    def test_simplest_project_with_logs(self):
        expected_log = self.test_folder / "some.log"
        self.nmk("simplest.yml", extra_args=["--log-file", expected_log.as_posix()], with_logs=True)
        assert expected_log.is_file()

    def test_simplest_project_without_logs(self):
        self.nmk("simplest.yml", extra_args=["--log-file", ""], with_logs=True)
        assert not self.nmk_out.exists()
        self.check_logs("Nothing to do")

    def test_invalid_yml(self):
        self.nmk("invalid.yml", expected_error="Project '{project}' is malformed: ")

    def test_empty_validation_fails(self):
        self.nmk("empty.yml", expected_error="Project '{project}' contains invalid data: ")
