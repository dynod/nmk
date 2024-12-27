"""
Nmk task module
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from rich.emoji import Emoji
from rich.text import Text

from nmk.model.config import NmkConfig, NmkDictConfig, NmkListConfig


@dataclass
class NmkTask:
    """
    Task model class
    """

    name: str
    """Task name"""

    description: str
    """Task description text"""

    silent: bool
    """Task silent mode"""

    emoji: Union[Emoji, Text]
    """Task emoji or rich text string"""

    builder: object
    """Task builder instance"""

    params: NmkDictConfig
    """Task builder parameters"""

    _deps: list[str]
    _append_to: Union[str, list[str]]
    _prepend_to: Union[str, list[str]]
    _inputs_cfg: NmkListConfig
    _outputs_cfg: NmkListConfig

    run_if: NmkConfig
    """Task "if" condition"""

    run_unless: NmkConfig
    """Task "unless" condition"""

    model: object
    """model instance"""

    subtasks: list[object] = None
    """Task dependencies"""

    refering_tasks: list[object] = field(default_factory=list)
    """Tasks that reference this task"""

    _inputs: list[Path] = None
    _outputs: list[Path] = None

    skipped: bool = False
    """Task skip mode"""

    def __resolve_task(self, name: Union[str, list[str]]) -> object:
        if name is not None:
            # Iterate on candidate names until we find a known one
            name_list = name if isinstance(name, list) else [name]
            for name_candidate in name_list:
                if name_candidate in self.model.tasks:
                    return self.model.tasks[name_candidate]
            else:
                raise AssertionError(f"Can't find any of candidates ({name_list}) referenced by {self.name} task")
        return None

    def __contribute_dep(self, name: Union[str, list[str]], append: bool):
        t = self.__resolve_task(name)
        if t is not None and self.name not in t._deps:
            # Ascendant dependency which is not yet contributed:
            # - first resolve (if not done yet)
            t._resolve_subtasks()

            # - then add to list
            if append:
                t._deps.append(self.name)
                t.subtasks.append(self)
            else:
                t._deps.insert(0, self.name)
                t.subtasks.insert(0, self)

    def _resolve_subtasks(self):
        # Resolved yet?
        if self.subtasks is None:
            # Map names to tasks
            self.subtasks = []
            for task in filter(lambda t: t is not None, map(self.__resolve_task, self._deps)):
                # Append to sub-tasks
                self.subtasks.append(task)

                # Remember the current task as a refering task
                task.refering_tasks.append(self)
        return self.subtasks

    def _resolve_contribs(self):
        # Contribute to dependencies
        self.__contribute_dep(self._append_to, True)
        self.__contribute_dep(self._prepend_to, False)

    def _resolve_files(self, field: str) -> list[Path]:
        if getattr(self, field) is None:
            # Convert strings to paths
            path_config = getattr(self, field + "_cfg")
            paths = []
            if path_config is not None:
                for new_path in path_config.value:
                    new_p = Path(new_path)
                    if new_p not in paths:
                        paths.append(new_p)
            setattr(self, field, paths)
        return getattr(self, field)

    def _skip(self):
        # Skip this task
        self.skipped = True

        # Iterate on sub-tasks
        for sub_task in self.subtasks:
            # Are all refering tasks skipped?
            if all(t.skipped for t in sub_task.refering_tasks):
                # Skip this sub-task as well
                sub_task._skip()

    @property
    def inputs(self) -> list[Path]:
        """Task input paths"""
        return self._resolve_files("_inputs")

    @property
    def outputs(self) -> list[Path]:
        """Task output paths"""
        return self._resolve_files("_outputs")
