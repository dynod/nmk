from tests.utils import NmkTester


class TestBuild(NmkTester):
    def test_unknown_task(self):
        self.nmk("simplest.yml", extra_args=["unknownTask"], expected_error="Unknown task(s): unknownTask")

    def test_dry_run_default(self):
        self.nmk("build_default.yml", extra_args=["--dry-run"])
        self.check_logs_order(["subA]] DEBUG 🛠  - My A task", "subB]] INFO 🛠  - My B task", "parentTask]] INFO 🛠  - The parent task", "3 built tasks"])

    def test_dry_run_specified(self):
        self.nmk("build_default.yml", extra_args=["--dry-run", "subA"])
        self.check_logs_order(["subA]] DEBUG 🛠  - My A task", "1 built tasks"])

    def test_no_builder(self):
        self.nmk("build_default.yml", extra_args=["subB"])
        self.check_logs_order(["subB]] DEBUG 🐛 - Task skipped, nothing to do", "1 built tasks"])

    def test_build_params(self):
        self.nmk("build_default.yml", extra_args=["subA"])
        self.check_logs("foo:bar bar:123 ref:azerty")

    def test_no_inputs(self):
        output = self.test_folder / "someOutput.txt"
        assert not output.is_file()
        self.nmk("build_no_inputs.yml", extra_args=["--config", f'{{"test_folder": "{self.test_folder}"}}'])
        self.check_logs(f"Ready to write some input to {output}")
        assert output.is_file()

        self.nmk("build_no_inputs.yml", extra_args=["--config", f'{{"test_folder": "{self.test_folder}"}}'])
        self.check_logs(f"{output} already exists")

    def test_lazy_rebuild(self):
        test_input = self.test_folder / "someInput.txt"
        test_output = self.test_folder / "someOutput.txt"

        # Missing input
        self.nmk(
            "build_copy.yml", extra_args=["--config", f'{{"test_folder": "{self.test_folder}"}}'], expected_error="Task sampleBuild miss following inputs:"
        )

        # Build 1
        test_input.touch()
        self.nmk("build_copy.yml", extra_args=["--config", f'{{"test_folder": "{self.test_folder}"}}'])
        self.check_logs(f"Copying {test_input} to {test_output}")
        assert test_output.is_file()

        # Build 2
        self.nmk("build_copy.yml", extra_args=["--config", f'{{"test_folder": "{self.test_folder}"}}'])
        self.check_logs("Task skipped, nothing to do")

    def test_failling_build(self):
        self.nmk("build_error.yml", expected_error="An error occurred during task sampleBuild build: Some error happened!")
