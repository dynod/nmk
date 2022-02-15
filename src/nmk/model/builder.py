from abc import ABC, abstractmethod

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
