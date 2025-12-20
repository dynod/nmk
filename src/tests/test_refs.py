import re
import subprocess

from _pytest.monkeypatch import MonkeyPatch

from nmk.utils import is_windows
from tests.utils import NmkTester


class TestRefs(NmkTester):
    def test_relative_ref_not_found(self):
        self.nmk("relative_ref_not_found.yml", expected_error=f"While loading {self.template('unknownRef.yml')}: Project file not found")

    def test_absolute_ref_not_found(self):
        project_name = "absolute_ref_not_found_win.yml" if is_windows() else "absolute_ref_not_found.yml"
        self.nmk(project_name, expected_error=re.compile("While loading [^ ]+unknownRef.yml: Project file not found"))
        self.check_logs(re.compile(r"Absolute path \(not portable\) used in project: [^ ]+unknownRef.yml"))

    def test_repo_ref_not_found(self):
        self.nmk("repo_ref_not_found.yml", expected_error="While loading {project}: Unresolved repo-like relative reference: <unknownRepo>/unknownRef.yml")

    def test_local_repo_unresolved(self):
        self.nmk("local_repo_ref_not_found.yml", expected_error=f"While loading {self.template('sub/unknownRef.yml')}: Project file not found")

    def test_duplicate_repo(self):
        self.nmk("duplicate_repo.yml", expected_error="While loading {project}: Duplicate repo names: someRepo")

    def test_self_ref(self):
        self.nmk("self_ref.yml")
        self.check_logs("Nothing to do")

    def test_repo_no_local(self):
        self.nmk(
            "remote_repo_ref_no_local.yml",
            expected_error="While loading https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main/src/tests/templates/invalid.yml: Project is malformed: ",
        )

    def test_repo_already_exists(self):
        # Fake cache folder: download won't occur
        (self.test_folder / ".nmk/cache/b38e130bed1f28a29781827a5548ac2bdb981eaf").mkdir(parents=True)
        self.nmk(
            "remote_repo_ref_no_local.yml",
            expected_error="While loading https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main/src/tests/templates/invalid.yml: Project file not found",
        )

    def test_repo_unknown_local(self):
        self.nmk(
            "remote_repo_ref_missing_local.yml",
            expected_error="While loading https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main/src/tests/templates/invalid.yml: Project is malformed: ",
        )

    def test_repo_unknown_format(self):
        self.nmk(
            "remote_repo_ref_unknown_format.yml",
            expected_error="While loading https://github.com/dynod/nmk/archive/refs/heads/main.foo!nmk-main/src/tests/templates/invalid.yml: Unsupported remote file format: .foo",
        )

    def test_repo_override(self):
        self.nmk("remote_repo_override.yml")
        self.check_logs(["Nothing to do", 'Replacing remote ref "'])

    def test_unknown_tar_ref(self):
        self.nmk(
            "remote_repo_ref_tar.yml",
            expected_error="While loading https://github.com/dynod/pytest-multilog/archive/refs/tags/1.2.tar.gz!pytest-multilog-1.2/README.md: Project is malformed: ",
        )

    def test_ref_bad_format(self):
        self.nmk("remote_repo_ref_bad_format1.yml", expected_error="While loading http://foo!bar!12/foo.yml: Unsupported repo remote syntax: http://foo!bar!12")
        self.nmk("remote_repo_ref_bad_format2.yml", expected_error="While loading http://foo!/foo.yml: Unsupported remote file format:  ")
        self.nmk("remote_repo_ref_bad_format3.yml", expected_error="While loading !http://foo/foo.yml: Project file not found")

    def test_ref_sub_folder(self):
        self.nmk("remote_repo_ref_valid.yml")
        self.check_logs("Nothing to do")

    def test_ref_repo_github(self):
        self.nmk("remote_repo_ref_github.yml")
        self.check_logs("Nothing to do")

    def test_clear_cache(self):
        (self.nmk_cache / "cache").mkdir(parents=True)
        self.nmk("remote_repo_ref_valid.yml", extra_args=["--no-cache"])
        self.check_logs(["Nothing to do", "Cache cleared"])

    def test_invalid_url(self):
        self.nmk("remote_repo_bad_url.yml", expected_error="While loading https://github.com/dynod/nmk/fake.zip!foo.yml: File is not a zip file")

    def test_http_ref(self):
        self.nmk("ref_http_without_repo.yml")
        self.check_logs("Nothing to do")

    def test_direct_url_ref_raw(self):
        self.nmk("https://github.com/dynod/nmk/raw/main/src/tests/templates/simplest.yml")
        self.check_logs("Nothing to do")

    def test_github_url(self):
        self.nmk("github://dynod/nmk/main/src/tests/templates/simplest.yml")
        self.check_logs("Nothing to do")

        # Another reference from the same URL
        self.nmk(
            "https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main/src/tests/templates/invalid.yml",
            expected_error="While loading https://github.com/dynod/nmk/archive/refs/heads/main.zip!nmk-main/src/tests/templates/invalid.yml: Project is malformed:",
        )

        # Check only one repo cached
        cache_folders = list(filter(lambda d: d.is_dir() and not d.name.startswith("."), (self.nmk_cache / "cache").glob("*")))
        assert len(cache_folders) == 1

    def test_malformed_pip_url(self):
        self.nmk("pip://foo/bar", expected_error="While loading pip://foo/bar: Malformed pip reference: pip://foo/bar")

    def test_unknown_pip_reference(self):
        self.nmk("pip://nmk!unknown.yml", expected_error="While loading pip://nmk!unknown.yml: Project file not found")

    def test_pip_install(self, monkeypatch: MonkeyPatch):
        found_args = []

        def record_process(args: list[str], *p_args, **kwargs):  # pyright: ignore[reportUnknownParameterType, reportMissingParameterType]
            nonlocal found_args
            found_args = args
            return subprocess.CompletedProcess(args, 0, "", "")

        monkeypatch.setattr(subprocess, "run", record_process)  # pyright: ignore[reportUnknownArgumentType]
        self.nmk(
            "pip://definitely-unknown-package>=1.2!inside/unknown.yml",
            expected_error="While loading pip://definitely-unknown-package>=1.2!inside/unknown.yml: Can't find module 'definitely_unknown_package' even after having installed 'definitely-unknown-package>=1.2' package",
        )
        assert found_args[1:] == ["-m", "pip", "install", "definitely-unknown-package>=1.2"]

    def test_pip_ref_not_mutable(self, monkeypatch: MonkeyPatch):
        # Test a pip ref with a (faked) non-mutable backend
        try:
            from buildenv2._backends.pip import LegacyPipBackend as EnvBackend
        except ImportError:
            from nmk._internal.envbackend_legacy import EnvBackend
        monkeypatch.setattr(EnvBackend, "is_mutable", lambda slf: False)  # pyright: ignore[reportUnknownLambdaType, reportUnknownArgumentType]
        self.nmk("pip://foo!bar.yml")
        self.check_logs("Can't install plugins in this environment; just adding foo to requirements and skip reference for now.")
