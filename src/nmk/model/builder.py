import logging
from abc import ABC, abstractmethod

from nmk.model.model import NmkModel
from nmk.model.task import NmkTask


class NmkTaskBuilder(ABC):
    def __init__(self, model: NmkModel):
        self.task: NmkTask = None
        self.logger: logging.Logger = None
        self.model = model

    def update_task(self, task: NmkTask):
        self.task = task
        self.logger = logging.getLogger(self.task.name)

    @abstractmethod
    def build(self):  # pragma: no cover
        pass
