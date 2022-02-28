# Tests for python plugin
import subprocess

from tests.utils import NmkTester


class TestPythonPlugin(NmkTester):
    def check_version(self, monkeypatch, git_version: str, expected_python_version: str):
        # Fake git subprocess behavior
        monkeypatch.setattr(
            subprocess, "run", lambda all_args, check, capture_output, text, encoding, cwd: subprocess.CompletedProcess(all_args, 0, git_version, "")
        )
        self.nmk(self.prepare_project("python/ref_python.yml"), extra_args=["--print", "pythonVersion"])
        self.check_logs(f'Config dump: {{ "pythonVersion": "{expected_python_version}" }}')

    def test_python_version(self, monkeypatch):
        self.check_version(monkeypatch, "\n", "")
        self.check_version(monkeypatch, "1.2.3", "1.2.3")
        self.check_version(monkeypatch, "1.2.3-dirty", "1.2.3+dirty")
        self.check_version(monkeypatch, "1.2.3-12-gb95312a", "1.2.3.post12+gb95312a")
        self.check_version(monkeypatch, "1.2.3-12-gb95312a-dirty", "1.2.3.post12+gb95312a-dirty")

    def test_python_version_stamp(self):
        self.nmk(self.prepare_project("python/ref_python.yml"), extra_args=["py.version"])
        self.check_logs("Refresh python version")
        assert (self.test_folder / "out" / ".pythonversion").is_file()
