import logging
import traceback
from abc import ABC, abstractmethod
from argparse import Action, ArgumentParser, Namespace
from typing import List

from nmk.model.loader import NmkLoader
from nmk.model.model import NmkModel


class ModelCompleter(ABC):
    @abstractmethod
    def complete(self, model: NmkModel) -> List[str]:  # pragma: no cover
        pass

    def __call__(self, prefix: str, action: Action, parser: ArgumentParser, parsed_args: Namespace) -> List[str]:
        try:
            # Load model
            loader = NmkLoader(parsed_args, False)
            return self.complete(loader.model)
        except Exception as e:  # pragma: no cover
            logging.debug(f"Exception in completion: {e}\n" + "".join(traceback.format_tb(e.__traceback__)))
        return []  # pragma: no cover


class TasksCompleter(ModelCompleter):
    def complete(self, model: NmkModel) -> List[str]:
        # Complete with known model tasks
        return model.tasks.keys()
