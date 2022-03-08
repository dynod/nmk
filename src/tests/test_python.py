# Tests for python plugin
import shutil
import subprocess
from configparser import ConfigParser

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
        self.check_version(monkeypatch, "1.2.3-12-gb95312a-dirty", "1.2.3.post12+gb95312a.dirty")

    def fake_python_src(self, content: str = "", package: str = "fake", name: str = "fake.py"):
        # Prepare fake source python files to enable python tasks
        src = self.test_folder / "src" / package
        src.mkdir(parents=True, exist_ok=True)
        fake = src / name
        with fake.open("w") as f:
            f.write(content)
        (src / "__init__.py")

    def test_python_version_stamp(self):
        # Check python version is not generated (while no python files)
        self.nmk(self.prepare_project("python/ref_python.yml"), extra_args=["py.version"])
        assert not (self.test_folder / "out" / ".pythonversion").is_file()

        # Prepare fake source python files to enable python tasks
        self.fake_python_src()

        # Check python version is generated
        self.nmk(self.prepare_project("python/ref_python.yml"), extra_args=["py.version"])
        self.check_logs("Refresh python version")
        assert (self.test_folder / "out" / ".pythonversion").is_file()

    def test_python_setup_missing_config(self):
        # Prepare fake source python files to enable python tasks
        self.fake_python_src()
        shutil.copyfile(self.template("python/missing_var.cfg"), self.test_folder / "missing_var.cfg")
        self.nmk(
            self.prepare_project("python/setup_missing_var.yml"),
            extra_args=["py.setup"],
            expected_error=f"An error occurred during task py.setup build: Unknown config items referenced from python setup fragment {self.test_folder}/missing_var.cfg: unknownConfig",
        )

    def test_python_setup_ok(self):
        # Prepare fake source python files to enable python tasks
        self.fake_python_src()
        shutil.copyfile(self.template("python/setup1.cfg"), self.test_folder / "setup1.cfg")
        shutil.copyfile(self.template("python/setup2.cfg"), self.test_folder / "setup2.cfg")
        self.nmk(
            self.prepare_project("python/setup_ok.yml"),
            extra_args=["py.setup"],
        )
        assert (self.test_folder / "setup.py").is_file()
        generated_setup = self.test_folder / "setup.cfg"
        assert generated_setup.is_file()

        # Verify merged content
        with generated_setup.open() as f:
            c = ConfigParser()
            c.read_file(f.readlines())
        assert c.get("dummy", "foo") == "bar"
        assert c.get("dummy", "bar") == "venv"
        assert c.get("dummy", "other") == "1,2,3"

    def test_python_format(self):
        # Prepare fake source python files to enable python tasks
        self.fake_python_src()
        self.nmk(self.prepare_project("python/ref_python.yml"), extra_args=["py.sort"])
        assert (self.test_folder / "out" / ".black").is_file()
        assert (self.test_folder / "out" / ".isort").is_file()

    def test_python_flake(self):
        # Prepare fake source with flake errors
        self.fake_python_src("foo=0")
        self.nmk(self.prepare_project("python/ref_python.yml"), extra_args=["py.analyze"], expected_error=f"{self.test_folder}/src/fake/fake.py has issues: ")
        assert (self.test_folder / "out" / "flake-report").is_dir()

        # Prepare fake source without errors
        self.fake_python_src("")
        self.nmk(self.prepare_project("python/ref_python.yml"), extra_args=["py.analyze"])
        assert (self.test_folder / "out" / "flake-report").is_dir()

    def test_python_build(self):
        # Prepare test project for python build
        self.fake_python_src("")
        self.nmk(self.prepare_project("python/ref_python.yml"), extra_args=["py.build"])
        archives = list((self.test_folder / "out" / "artifacts").glob("fake-*"))
        assert len(archives) == 2

    def test_python_test(self):
        # Prepare test project for python build
        self.fake_python_src(
            """
class TestSomething:
    def test_something(self):
        pass
""",
            package="tests",
            name="test_foo.py",
        )
        p = self.prepare_project("python/ref_python.yml")
        self.nmk(p, extra_args=["py.tests"])
        assert self.test_folder / "out" / "tests" / "report.xml"

        # Trigger again to cover clean code
        self.nmk(p, extra_args=["py.tests"])
