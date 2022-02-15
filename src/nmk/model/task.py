from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from rich.emoji import Emoji

from nmk.model.config import NmkListConfig


@dataclass
class NmkTask:
    name: str
    description: str
    silent: bool
    emoji: Emoji
    builder: object
    required_config: Dict[str, object]
    _deps: List[str]
    _append_to: str
    _prepend_to: str
    _inputs_cfg: NmkListConfig
    _outputs_cfg: NmkListConfig
    model: object
    subtasks: List[object] = None
    _inputs: List[Path] = None
    _outputs: List[Path] = None

    def __resolve_task(self, name: str) -> object:
        if name is not None:
            # If reference is set, get matching task object
            assert name in self.model.tasks, f"Unknown {name} task referenced by {self.name} task"
            return self.model.tasks[name]
        return None

    def __contribute_dep(self, name: str, append: bool):
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
            # Map names to
            self.subtasks = list(filter(lambda t: t is not None, map(self.__resolve_task, self._deps)))
        return self.subtasks

    def _resolve_contribs(self):
        # Contribute to dependencies
        self.__contribute_dep(self._append_to, True)
        self.__contribute_dep(self._prepend_to, False)

    def _resolve_files(self, field: str) -> List[Path]:
        if getattr(self, field) is None:
            # Convert strings to paths
            setattr(self, field, list(map(Path, getattr(self, field + "_cfg").value)))
        return getattr(self, field)

    @property
    def inputs(self) -> List[Path]:
        return self._resolve_files("_inputs")

    @property
    def outputs(self) -> List[Path]:
        return self._resolve_files("_outputs")

    def _verify_config(self):
        # Make sure all required config items exist, with the correct type
        for cfg_name, cfg_type in self.required_config.items():
            assert cfg_name in self.model.config, f"Task {self.name} requires missing config item {cfg_name}"
            actual_type = self.model.config[cfg_name].value_type
            assert (
                actual_type == cfg_type
            ), f"Task {self.name} requires config item {cfg_name} of type {cfg_type.__name__}, but got type is {actual_type.__name__}"
