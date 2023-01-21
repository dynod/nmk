import json
import logging
from datetime import datetime
from typing import List

from nmk.errors import NmkStopHereError
from nmk.logs import NmkLogger, NmkLogWrapper
from nmk.model.keys import NmkRootConfig
from nmk.model.model import NmkModel
from nmk.model.task import NmkTask
from nmk.utils import is_condition_set

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
        assert task not in refering_tasks, f"Cyclic dependency: {task.name} referenced from tasks {' -> '.join(t.name for t in refering_tasks)}"

        # Traverse dependencies
        for dep in task.subtasks:
            self._traverse_task(dep, refering_tasks + [task])

        # Add task if not already done
        if task not in self.ordered_tasks:
            self.ordered_tasks.append(task)

    def print_config(self, print_list: List[str]):
        # Print config is required
        for k in print_list:
            assert k in self.model.config, f"Unknown config item key: {k}"

        def prepare_for_json(v):
            if isinstance(v, list):
                return list(map(prepare_for_json, v))
            if isinstance(v, dict):
                return {k: prepare_for_json(v) for k, v in v.items()}
            return v if type(v) in [int, str, bool] else str(v)

        dump_dict = json.dumps({k: prepare_for_json(c.value) for k, c in filter(lambda t: t[0] in print_list, self.model.config.items())}, indent=-1).replace(
            "\n", " "
        )
        if self.model.args.log_level >= logging.WARNING:
            # Quiet mode
            print(dump_dict)
        else:
            # Normal mode
            NmkLogger.info("newspaper", f"Config dump: {dump_dict}")

        # Stop here
        raise NmkStopHereError()

    def build(self) -> bool:
        # Print if necessary
        print_list = self.model.args.print
        if print_list is not None and len(print_list):
            self.print_config(print_list)

        # Something to build?
        if len(self.ordered_tasks):
            # Do the build
            NmkLogger.debug("Starting the build!")
            max_task_len = max(len(t.name) for t in self.ordered_tasks)
            for task in self.ordered_tasks:
                build_logger = NmkLogWrapper(logging.getLogger((" " * (max_task_len - len(task.name))) + f"[{task.name}]"))
                if self.model.args.dry_run:
                    # Dry-run mode: don't call builder, just log
                    self.task_prolog(task, build_logger)
                elif self.needs_build(task, build_logger):
                    # Task needs to be (re)built
                    self.task_build(task, build_logger)
                else:
                    # Task skipped
                    build_logger.debug("Task skipped, nothing to do")

        # Something done?
        NmkLogger.debug(f"{self.built_tasks} built tasks")
        return self.built_tasks > 0

    def task_prolog(self, task: NmkTask, build_logger: NmkLogWrapper):
        self.built_tasks += 1
        build_logger.log(logging.DEBUG if task.silent else logging.INFO, task.emoji, task.description)

    def task_build(self, task: NmkTask, build_logger: NmkLogWrapper):
        # Prolog
        self.task_prolog(task, build_logger)

        # And build...
        try:
            # Prepare logger
            task.builder.update_logger(build_logger)

            # Invoke builder with provided params (if any)
            params = task.params.value if task.params is not None else {}
            task.builder.build(**params)
        except Exception as e:
            raise e if isinstance(e, NmkStopHereError) else Exception(f"An error occurred during task {task.name} build: {e}").with_traceback(e.__traceback__)

    def needs_build(self, task: NmkTask, build_logger: NmkLogWrapper):
        # Check if task needs to be built

        # No builder = nothing to build
        if task.builder is None:
            build_logger.debug("Task doesn't have a builder defined")
            return False

        # Unless/if conditions
        if task.run_unless is not None and is_condition_set(task.run_unless.value):
            build_logger.debug(f'Task "unless" condition is set: {task.run_unless.value}')
            return False
        if task.run_if is not None and not is_condition_set(task.run_if.value):
            build_logger.debug(f'Task "if" condition is not set: {task.run_if.value}')
            return False

        # Always build if task doesn't have inputs or outputs (no way to know if something has changed)
        if len(task.inputs) == 0 or len(task.outputs) == 0:
            build_logger.debug("Task misses either inputs or outputs")
            return True

        # All inputs must exist
        missing_inputs = list(filter(lambda p: not p.is_file() and not task.builder.allow_missing_input(p), task.inputs))
        assert len(missing_inputs) == 0, f"Task {task.name} miss following inputs:\n" + "\n".join(f" - {p}" for p in missing_inputs)

        # Force build?
        if self.model.args.force:
            build_logger.debug("Force build, don't check inputs vs outputs")
            return True

        # Add all project files to existing inputs
        all_inputs = set(task.inputs + self.model.config[NmkRootConfig.PROJECT_FILES].value)

        # Check modification times
        in_updates = {p.stat().st_mtime: p for p in filter(lambda p: p.exists(), all_inputs)}
        out_updates = {p.stat().st_mtime if p.exists() else 0: p for p in task.outputs}
        input_max = max(in_updates.keys())
        output_max = min(out_updates.keys())
        if input_max > output_max:
            # At least one input has been modified after the oldest output
            build_logger.debug(
                f"(Re)Build task: input ({in_updates[input_max]} - {datetime.fromtimestamp(input_max).strftime(TIME_FORMAT)}) "
                + f"is more recent than output ({out_updates[output_max]} - {datetime.fromtimestamp(output_max).strftime(TIME_FORMAT)})"
            )
            return True

        build_logger.debug("Output is already up to date: skip task")
        return False
