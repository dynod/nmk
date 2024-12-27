"""
nmk task builder definition module
"""

from abc import ABC, abstractmethod
from pathlib import Path

from nmk.logs import NmkLogWrapper
from nmk.model.model import NmkModel
from nmk.model.task import NmkTask


class NmkTaskBuilder(ABC):
    """
    Task builder base class

    :param model: nmk model instance
    """

    def __init__(self, model: NmkModel):
        self.task: NmkTask = None
        """Associated task instance"""

        self.logger: NmkLogWrapper = None
        """Logger for this builder"""

        self.model = model
        """nmk model instance"""

    def update_task(self, task: NmkTask):
        """
        Task instance setter

        :param task: task instance
        """
        self.task = task

    def update_logger(self, logger: NmkLogWrapper):
        """
        Logger instance setter

        :param logger: logger instance
        """
        self.logger = logger

    @abstractmethod
    def build(self):  # pragma: no cover
        """
        Build method; invoked when task is executed. Shall be overridden by sub-classes
        """
        pass

    @property
    def inputs(self) -> list[Path]:
        """
        List of task input paths
        """
        return self.task.inputs

    @property
    def outputs(self) -> list[Path]:
        """
        List of task output paths
        """
        return self.task.outputs

    @property
    def main_input(self) -> Path:
        """
        Path to main input (first input of the list)
        """
        return self.inputs[0]

    @property
    def main_output(self) -> Path:
        """
        Path to main output (first output of the list)
        """
        return self.outputs[0]

    def allow_missing_input(self, missing_input: Path) -> bool:
        """
        This builder method will be called to check if the implementation allows for a given input to be missing
        (sometimes, the task builder implementation may have conditional behavior WRT. if a given input exists or not).

        Default implementation is that all inputs are mandatory (always return False)

        :param missing_input: path to missing input
        """
        return False
