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

    @abstractmethod
    def get_value(self, name: str) -> str:  # pragma: no cover
        pass


class NmkBoolConfigResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return bool

    @abstractmethod
    def get_value(self, name: str) -> bool:  # pragma: no cover
        pass


class NmkIntConfigResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return int

    @abstractmethod
    def get_value(self, name: str) -> int:  # pragma: no cover
        pass


class NmkDictConfigResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return dict

    @abstractmethod
    def get_value(self, name: str) -> dict:  # pragma: no cover
        pass


class NmkListConfigResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return list

    @abstractmethod
    def get_value(self, name: str) -> list:  # pragma: no cover
        pass
