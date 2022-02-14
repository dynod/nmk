from tests.utils import NmkTester


class TestTasks(NmkTester):
    def test_unknown_emoji(self):
        self.nmk("task_unknown_emoji.yml", expected_error="While loading {project}: No emoji called 'some_unknown_emoji'")

    def test_class_not_found(self):
        self.nmk("task_class_not_found.yml", expected_error="While loading {project}: Can't instantiate class unknown.Builder: No module named 'unknown'")

    def test_class_bad_type(self):
        self.nmk(
            "task_class_bad_type.yml",
            expected_error="While loading {project}: Unexpected type for loaded class tests.sample_resolvers.StrResolver: got StrResolver, expecting NmkTaskBuilder subclass",
        )

    def test_unknown_dep(self):
        self.nmk("task_unknown_dep.yml", expected_error="Unknown someUnknownOtherTask task referenced by someTask task")

    def test_contributing_dep(self):
        self.nmk("task_contributing_dep.yml", extra_args=["--dry-run"])
        self.check_logs_order(["[contribA] prepended task", "[contribB] appended task", "[someTask] main task", "3 built tasks"])

    def test_cyclic_dep(self):
        self.nmk("task_cyclic_dep.yml", expected_error="Cyclic dependency: taskA referenced from tasks taskA -> taskB -> taskC")

    def test_missing_required_config(self):
        self.nmk("task_missing_config.yml", expected_error="Task someTask requires missing config item missingOne")

    def test_bad_type_required_config(self):
        self.nmk("task_bad_type_config.yml", expected_error="Task someTask requires config item stringOne of type str, but got type is int")
