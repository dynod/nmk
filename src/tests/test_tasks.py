from nmk.completion import TasksCompleter
from nmk.parser import NmkParser
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
        self.nmk("task_unknown_dep.yml", expected_error="Can't find any of candidates (['someUnknownOtherTask']) referenced by someTask task")

    def test_contributing_dep(self):
        self.nmk("task_contributing_dep.yml", extra_args=["--dry-run"])
        self.check_logs(["prepended task", "appended task", "main task", "3 built tasks"], check_order=True)

    def test_cyclic_dep(self):
        self.nmk("task_cyclic_dep.yml", expected_error="Cyclic dependency: taskA referenced from tasks taskA -> taskB -> taskC")

    def test_inputs_list(self):
        self.nmk("task_inputs_list.yml")
        self.check_logs("Inputs count: 1")

    def test_tasks_completion(self):
        tasks = TasksCompleter()(
            "", None, None, NmkParser().parse(["--root", self.test_folder.as_posix(), "-p", self.template("task_contributing_dep.yml").as_posix()])
        )
        assert len(tasks) == 3
        assert all(t in tasks for t in ["someTask", "contribB", "contribA"])
