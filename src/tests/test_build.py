import os

from tests.utils import NmkTester


class TestBuild(NmkTester):
    def test_unknown_task(self):
        self.nmk("simplest.yml", extra_args=["unknownTask"], expected_error="Unknown task(s): unknownTask")

    def test_dry_run_default(self):
        self.nmk("build_default.yml", extra_args=["--dry-run"])
        self.check_logs(
            ["subA]] DEBUG 🛠  - My A task", "subB]] INFO 🛠  - My B task", "parentTask]] INFO 🛠  - The parent task", "3 built tasks"], check_order=True
        )

    def test_dry_run_specified(self):
        self.nmk("build_default.yml", extra_args=["--dry-run", "subA"])
        self.check_logs(["subA]] DEBUG 🛠  - My A task", "1 built tasks"], check_order=True)

    def test_skip_unknown(self):
        self.nmk("build_default.yml", extra_args=["--skip", "unknown.task"], expected_error="unknown skipped task(s): unknown.task")

    def test_skip(self):
        self.nmk("build_default.yml", extra_args=["--skip", "subA"])
        self.check_logs(["subA]] DEBUG 🐛 - Task skipped, nothing to do", "0 built tasks"], check_order=True)

    def test_no_builder(self):
        self.nmk("build_default.yml", extra_args=["subB"])
        self.check_logs(["subB]] DEBUG 🐛 - Task skipped, nothing to do", "1 built tasks"], check_order=True)

    def test_build_params(self):
        self.nmk("build_default.yml", extra_args=["subA"])
        self.check_logs("foo:bar bar:123 ref:azerty")

    def test_no_inputs(self):
        output = self.test_folder / "someOutput.txt"
        assert not output.is_file()
        self.nmk("build_no_inputs.yml", extra_args=["--config", f"test_folder={self.test_folder}"])
        self.check_logs(f"Ready to write some input to {output}")
        assert output.is_file()

        self.nmk("build_no_inputs.yml", extra_args=["--config", f"test_folder={self.test_folder}"])
        self.check_logs(f"{output} already exists")

    def test_lazy_rebuild(self):
        test_input = self.test_folder / "someInput.txt"
        test_output = self.test_folder / "someOutput.txt"

        # Missing input
        project_file = self.prepare_project("build_copy.yml")
        self.nmk(project_file, extra_args=["--config", f"test_folder={self.test_folder}"], expected_error="Task sampleBuild miss following inputs:")

        # Build 1: input > output --> build
        test_input.touch()
        self.nmk(project_file, extra_args=["--config", f"test_folder={self.test_folder}"])
        self.check_logs(f"Copying {test_input} to {test_output}")
        assert test_output.is_file()

        # Build 2: output > input --> skip
        self.nmk(project_file, extra_args=["--config", f"test_folder={self.test_folder}"])
        self.check_logs("Task skipped, nothing to do")

        # Build 3: project file updated --> build
        project_file.touch()
        self.nmk(project_file, extra_args=["--config", f"test_folder={self.test_folder}"])
        self.check_logs(f"(Re)Build task: input ({project_file} - ")

        # Build 4: force build
        project_file.touch()
        self.nmk(project_file, extra_args=["--config", f"test_folder={self.test_folder}", "--force"])
        self.check_logs("Force build, don't check inputs vs outputs")

    def test_failling_build(self):
        self.nmk("build_error.yml", expected_error="An error occurred during task sampleBuild build: Some error happened!")

    def test_conditional_if_build(self):
        # Try 1: all tasks skipped because of if conditions
        self.nmk("build_conditional_if.yml")
        self.check_logs(
            [
                'Task "if" condition is not set: []',
                'Task "if" condition is not set: ' + str({}),
                'Task "if" condition is not set: 0',
                'Task "if" condition is not set: False',
                'Task "if" condition is not set: FaLsE',
            ]
        )

        # Try 2: all tasks triggered because of if conditions
        self.nmk(
            "build_conditional_if.yml",
            extra_args=["--config", '{"str_config":"ok","list_config":[0],"dict_config":{"foo":"bar"},"int_config":3,"bool_config":true}'],
        )
        self.check_logs(
            [
                " WARNING ❗ - list condition",
                " WARNING ❗ - dict condition",
                " WARNING ❗ - int condition",
                " WARNING ❗ - bool condition",
                " WARNING ❗ - string condition",
            ]
        )

    def test_conditional_unless_build(self):
        # Try 1: all tasks triggered because of unless conditions
        self.nmk("build_conditional_unless.yml")
        self.check_logs(
            [
                " WARNING ❗ - list condition",
                " WARNING ❗ - dict condition",
                " WARNING ❗ - int condition",
                " WARNING ❗ - bool condition",
                " WARNING ❗ - string condition",
            ]
        )

        # Try 2: all tasks skipped because of unless conditions
        self.nmk(
            "build_conditional_unless.yml",
            extra_args=["--config", '{"str_config":"ok","list_config":[0],"dict_config":{"foo":"bar"},"int_config":3,"bool_config":true}'],
        )
        self.check_logs(
            [
                'Task "unless" condition is set: [0]',
                "Task \"unless\" condition is set: {'foo': 'bar'}",
                'Task "unless" condition is set: 3',
                'Task "unless" condition is set: True',
                'Task "unless" condition is set: ok',
            ]
        )

    def test_conditional_error(self):
        # Try with unhandled config condition type
        self.nmk(
            "build_conditional_if.yml", extra_args=["errorBuild"], expected_error=f"Can't compute value type to evaluate conditional behavior: {os.path.sep}tmp"
        )
