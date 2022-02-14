from datetime import datetime
from typing import List

from nmk.logs import NmkLogger
from nmk.model.model import NmkModel
from nmk.model.task import NmkTask

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class NmkBuild:
    def __init__(self, model: NmkModel):
        self.model = model
        self.ordered_tasks = []
        self.built_tasks = 0

        # Find root tasks
        if len(self.model.args.tasks):
            # Specified on command line
            unknown = list(filter(lambda t: t not in self.model.tasks, self.model.args.tasks))
            assert len(unknown) == 0, f"Unknown task(s): {', '.join(unknown)}"
            root_tasks = [self.model.tasks[t] for t in self.model.args.tasks]
        elif self.model.default_task is not None:
            # Default task if nothing is specified
            root_tasks = [self.model.default_task]
        else:
            # Nothing to do
            root_tasks = []

        # Prepare build order
        for root_task in root_tasks:
            self._traverse_task(root_task, [])

    def _traverse_task(self, task: NmkTask, refering_tasks: List[NmkTask]):
        # Cyclic dependency?
        assert task not in refering_tasks, f"Cyclic dependency: {task.name} referenced from tasks {' -> '.join(map(lambda t:t.name, refering_tasks))}"

        # Traverse dependencies
        for dep in task.subtasks:
            self._traverse_task(dep, refering_tasks + [task])

        # Add task if not already done
        if task not in self.ordered_tasks:
            self.ordered_tasks.append(task)

    def build(self) -> bool:
        # Do the build
        NmkLogger.debug("Starting the build!")
        for task in self.ordered_tasks:
            if self.model.args.dry_run:
                # Dry-run mode: don't call builder, just log
                self.task_prolog(task)
            elif self.needs_build(task):
                # Task needs to be (re)built
                self.task_build(task)
            else:
                # Task skipped
                NmkLogger.debug(f"Task {task.name} skipped, nothing to do")

        # Something done?
        NmkLogger.debug(f"{self.built_tasks} built tasks")
        return self.built_tasks > 0

    def task_prolog(self, task: NmkTask):
        self.built_tasks += 1
        NmkLogger.info(task.emoji, f"[{task.name}] {task.description}")

    def task_build(self, task: NmkTask):
        # Prolog
        self.task_prolog(task)

        # And build...
        try:
            task.builder.build()
        except Exception as e:
            raise Exception(f"An error occurred during task {task.name} build: {e}").with_traceback(e.__traceback__)

    def needs_build(self, task: NmkTask):
        # Check if task needs to be built

        # No builder = nothing to build
        if task.builder is None:
            NmkLogger.debug(f"Task {task.name} doesn't have a builder defined")
            return False

        # Always build if task doesn't have inputs or outputs (no way to know if something has changed)
        if len(task.inputs) == 0 or len(task.outputs) == 0:
            NmkLogger.debug(f"Task {task.name} misses either inputs or outputs")
            return True

        # All inputs must exist
        missing_inputs = list(filter(lambda p: not p.is_file(), task.inputs))
        assert len(missing_inputs) == 0, f"Task {task.name} miss following inputs:\n" + "\n".join(map(lambda p: f" - {p}", missing_inputs))

        # Check modification times
        in_updates = {p.stat().st_mtime: p for p in task.inputs}
        out_updates = {p.stat().st_mtime if p.is_file() else 0: p for p in task.outputs}
        input_max = max(in_updates.keys())
        output_max = min(out_updates.keys())
        if input_max > output_max:
            # At least one input has been modified after the oldest output
            NmkLogger.debug(
                f"(Re)Build task {task.name}: input ({in_updates[input_max]} - {datetime.fromtimestamp(input_max).strftime(TIME_FORMAT)}) "
                + f"is more recent than output ({out_updates[output_max]} - {datetime.fromtimestamp(output_max).strftime(TIME_FORMAT)})"
            )
            return True

        return False
