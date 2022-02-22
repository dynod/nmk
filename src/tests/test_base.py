# Tests for base plugin
import subprocess

from nmk import __version__
from tests.utils import NmkTester


class TestBasePlugin(NmkTester):
    def test_output(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["--print", "outputDir"])
        self.check_logs(f'Config dump: {{ "outputDir": "{self.test_folder}/out" }}')

    def test_clean_missing(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["clean"])
        self.check_logs(f"Nothing to clean (folder not found: {self.test_folder}/out)")

    def test_clean_folder(self):
        fake_out = self.test_folder / "out"
        fake_out.mkdir()
        assert fake_out.is_dir()
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["clean"])
        self.check_logs(f"Cleaning folder: {self.test_folder}")
        assert not fake_out.exists()

    def test_build(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["--dry-run"])
        self.check_logs_order(["setup]] INFO 🛫 - Setup project configuration", "build]] INFO 🛠  - Build project artifacts", "4 built tasks"])

    def test_test(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["--dry-run", "tests"])
        self.check_logs_order(["tests]] INFO 🤞 - Run automated tests", "5 built tasks"])

    def test_loadme(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["loadme"])

        # Check generated Linux loadme
        loadme = self.test_folder / "loadme.sh"
        assert loadme.is_file()
        with loadme.open() as f:
            assert "python3 -m venv venv" in f.read()

        # Check generated Windows loadme
        loadme = self.test_folder / "loadme.bat"
        assert loadme.is_file()
        with loadme.open() as f:
            assert "python -m venv venv" in f.read()

    def test_version(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["version"])
        self.check_logs(f" 👉 nmk: {__version__}")

    def test_help(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["help"])
        self.check_logs(" 👉 nmk: https://github.com/dynod/nmk/wiki")

    def test_tasks(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["tasks"])
        self.check_logs(" 👉 tasks: List all available tasks")

    def test_git_version_config(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["--print", "gitVersion"])
        self.check_logs(f'Config dump: {{ "gitVersion": "{__version__[:5]}')

    def test_git_version_stamp(self):
        # Try 1: git version is persisted
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["gitVersion"])
        self.check_logs("Refresh git version")
        assert (self.test_folder / "out" / ".gitversion").is_file()

        # Try 2: shouldn't be persisted
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["gitVersion"])
        self.check_logs("Persisted git version already up to date")

    def test_deepclean(self, monkeypatch):
        # Stub to avoid real git clean command executed
        monkeypatch.setattr(subprocess, "run", lambda args, cwd, check: None)
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["deepclean"])
        self.check_logs("Clean all git ignored files")
