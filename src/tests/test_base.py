# Tests for base plugin
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
        self.check_logs_order(["setup]] INFO 🛫 - Setup project configuration", "build]] INFO 🛠  - Build project artifacts", "2 built tasks"])

    def test_test(self):
        self.nmk(self.prepare_project("base/ref_base.yml"), extra_args=["--dry-run", "tests"])
        self.check_logs_order(["tests]] INFO 🤞 - Run automated tests", "3 built tasks"])
