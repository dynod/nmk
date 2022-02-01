from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Union


@dataclass
class NmkConfig(ABC):
    name: str
    model: object
    path: Path

    @property
    def value(self) -> Union[str, int, bool, list, dict]:  # pragma: no cover
        pass

    @property
    def value_type(self) -> object:  # pragma: no cover
        pass


@dataclass
class NmkScalarConfig(NmkConfig):
    real_value: Union[str, int, bool, list, dict]

    @property
    def value(self) -> Union[str, int, bool, list, dict]:
        # Simple scalar value
        return self.real_value

    @property
    def value_type(self) -> object:
        return type(self.real_value)


@dataclass
class NmkResolvedConfig(NmkConfig):
    resolver: Callable
    _value: Union[str, int, bool, list, dict] = None

    @property
    def value(self) -> Union[str, int, bool, list, dict]:
        try:
            if self._value is None or self.resolver.is_volatile(self.name):
                # Cache value from resolver if not done yet, or redo if value is declared to be volatile
                self._value = self.resolver.get_value(self.name)

                # Make sure the resolver has returned expected type
                got_type = type(self._value)
                declared_type = self.value_type
                assert isinstance(self._value, declared_type), f"Invalid type returned by resolver: got {got_type.__name__}, expecting {declared_type.__name__}"
            return self._value
        except Exception as e:
            raise Exception(f"Error occurred while resolving config {self.name}: {e}").with_traceback(e.__traceback__)

    @property
    def value_type(self) -> object:
        try:
            # Ask resolver for value type
            return self.resolver.get_type(self.name)
        except Exception as e:
            raise Exception(f"Error occurred while getting type for config {self.name}: {e}").with_traceback(e.__traceback__)


@dataclass
class NmkMergedConfig(NmkConfig):
    scalar_list: List[NmkScalarConfig] = field(default_factory=list)
    _value: list = None


@dataclass
class NmkListConfig(NmkMergedConfig):
    @property
    def value(self) -> list:
        if self._value is None:
            # Merge lists
            self._value = [v for holder in self.scalar_list for v in holder.value]
        return self._value

    @property
    def value_type(self) -> object:
        return list


@dataclass
class NmkDictConfig(NmkMergedConfig):
    @property
    def value(self) -> dict:
        if self._value is None:
            # Merge dicts
            self._value = {}
            for holder in self.scalar_list:
                self._value.update(holder.value)
        return self._value

    @property
    def value_type(self) -> object:
        return dict
