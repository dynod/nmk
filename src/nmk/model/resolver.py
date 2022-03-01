from abc import ABC, abstractmethod
from typing import Union

from nmk.model.model import NmkModel


class NmkConfigResolver(ABC):
    def __init__(self, model: NmkModel):
        self.model = model

    @abstractmethod
    def get_value(self, name: str) -> Union[str, int, bool, list, dict]:  # pragma: no cover
        pass

    @abstractmethod
    def get_type(self, name: str) -> object:  # pragma: no cover
        pass

    def is_volatile(self, name: str) -> bool:
        return False


class NmkStrConfigResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return str


class NmkIntConfigResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return int


class NmkDictConfigResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return dict


class NmkListConfigResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return list
