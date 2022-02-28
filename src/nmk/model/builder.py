from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

from nmk.logs import NmkLogWrapper
from nmk.model.model import NmkModel
from nmk.model.task import NmkTask


class NmkTaskBuilder(ABC):
    def __init__(self, model: NmkModel):
        self.task: NmkTask = None
        self.logger: NmkLogWrapper = None
        self.model = model

    def update_task(self, task: NmkTask):
        self.task = task

    def update_logger(self, logger: NmkLogWrapper):
        self.logger = logger

    @abstractmethod
    def build(self):  # pragma: no cover
        pass

    @property
    def inputs(self) -> List[Path]:
        return self.task.inputs

    @property
    def outputs(self) -> List[Path]:
        return self.task.outputs

    @property
    def main_input(self) -> Path:
        return self.inputs[0]

    @property
    def main_output(self) -> Path:
        return self.outputs[0]

    def allow_missing_input(self, missing_input: Path) -> bool:
        """
        This builder method will be called to check if the implementation allows for a given input to be missing
        (sometimes, the task builder implementation may have conditional behavior WRT. if a given input exists or not).

        Default implementation is that all inputs are mandatory (always return False)
        """
        return False
