from tests.utils import NmkTester


class TestRefs(NmkTester):
    def test_relative_ref_not_found(self):
        self.nmk("relative_ref_not_found.yml", expected_error=f"While loading {self.template('unknownRef.yml')}: Project file not found")

    def test_absolute_ref_not_found(self):
        self.nmk("absolute_ref_not_found.yml", expected_error="While loading /unknownRef.yml: Project file not found")
        self.check_logs("nmk] WARNING ❗ - Absolute path (not portable) used in project: /unknownRef.yml")

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
        (self.test_folder / "nmk/cache/b38e130bed1f28a29781827a5548ac2bdb981eaf").mkdir(parents=True)
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

    def test_clear_cache(self):
        (self.nmk_cache / "cache").mkdir(parents=True)
        self.nmk("remote_repo_ref_valid.yml", extra_args=["--no-cache"])
        self.check_logs(["Nothing to do", "Cache cleared"])

    def test_invalid_url(self):
        self.nmk("remote_repo_bad_url.yml", expected_error="While loading https://github.com/dynod/nmk/fake.zip!foo.yml: File is not a zip file")

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
