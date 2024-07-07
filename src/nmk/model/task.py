from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

from rich.emoji import Emoji
from rich.text import Text

from nmk.model.config import NmkConfig, NmkDictConfig, NmkListConfig


@dataclass
class NmkTask:
    name: str
    description: str
    silent: bool
    emoji: Union[Emoji, Text]
    builder: object
    params: NmkDictConfig
    _deps: List[str]
    _append_to: Union[str, List[str]]
    _prepend_to: Union[str, List[str]]
    _inputs_cfg: NmkListConfig
    _outputs_cfg: NmkListConfig
    run_if: NmkConfig
    run_unless: NmkConfig
    model: object
    subtasks: List[object] = None
    _inputs: List[Path] = None
    _outputs: List[Path] = None
    skipped: bool = False

    def __resolve_task(self, name: Union[str, List[str]]) -> object:
        if name is not None:
            # Iterate on candidate names until we find a known one
            name_list = name if isinstance(name, list) else [name]
            for name_candidate in name_list:
                if name_candidate in self.model.tasks:
                    return self.model.tasks[name_candidate]
            else:
                raise AssertionError(f"Can't find any of candidates ({name_list}) referenced by {self.name} task")
        return None

    def __contribute_dep(self, name: Union[str, List[str]], append: bool):
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
            path_config = getattr(self, field + "_cfg")
            paths = []
            if path_config is not None:
                for new_path in path_config.value:
                    new_p = Path(new_path)
                    if new_p not in paths:
                        paths.append(new_p)
            setattr(self, field, paths)
        return getattr(self, field)

    @property
    def inputs(self) -> List[Path]:
        return self._resolve_files("_inputs")

    @property
    def outputs(self) -> List[Path]:
        return self._resolve_files("_outputs")
