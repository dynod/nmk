import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, List, Set, Union

from nmk.model.keys import NmkRootConfig

# Pattern to locate config reference in string
CONFIG_REF_PATTERN = re.compile(r"\$\{([^ \}]+)\}")

# Pattern to recognize final config items
FINAL_ITEM_PATTERN = re.compile("^[A-Z0-9_]+$")


@dataclass
class NmkConfig(ABC):
    name: str
    model: object
    path: Path

    @property
    def is_final(self) -> bool:
        return FINAL_ITEM_PATTERN.match(self.name) is not None

    @property
    def value(self) -> Union[str, int, bool, list, dict]:
        return self.resolve()

    def resolve(self, cache: bool = True, resolved_from: Set[str] = None) -> Union[str, int, bool, list, dict]:
        if not cache or not hasattr(self, "cached_value") or self.cached_value is None:
            # Get value from implementation
            out = self._get_value(cache, resolved_from)

            # Cache resolved value?
            if cache:
                self.cached_value = out
        else:
            # Use cached value
            out = self.cached_value

        return out

    def _format(
        self, cache: bool, candidate: Union[str, int, bool, list, dict], resolved_from: Set[str] = None, path: Path = None
    ) -> Union[str, int, bool, list, dict]:
        resolved_from = set(resolved_from) if resolved_from is not None else set()
        resolved_from.add(self.name)

        if not isinstance(candidate, str):
            # Nothing to format
            return candidate

        # Iterate on <xxx> references
        m = True
        to_format = candidate
        while m is not None:
            m = CONFIG_REF_PATTERN.search(to_format)
            if m is not None:
                # Look for referenced config item name
                ref_name = m.group(1)
                if ref_name == NmkRootConfig.BASE_DIR:
                    # Resolve current path
                    ref_value = str(path if path is not None else self.path)
                else:
                    # Resolve from config
                    assert ref_name not in resolved_from, f"Cyclic string substitution: resolving (again!) '{ref_name}' config from '{self.name}' config"
                    assert ref_name in self.model.config, f"Unknown '{ref_name}' config referenced from '{self.name}' config"
                    ref_value = self.model.config[ref_name].resolve(cache, resolved_from)

                # Replace with resolved value
                begin, end = m.span(0)
                to_format = to_format[0:begin] + str(ref_value) + to_format[end:]
        return to_format

    @abstractmethod
    def _get_value(self, cache: bool, resolved_from: Set[str] = None) -> Union[str, int, bool, list, dict]:  # pragma: no cover
        pass

    @property
    def value_type(self) -> object:  # pragma: no cover
        pass


@dataclass
class NmkStaticConfig(NmkConfig):
    static_value: Union[str, int, bool, list, dict]

    def _get_value(self, cache: bool, resolved_from: Set[str] = None) -> Union[str, int, bool, list, dict]:
        # Simple static value
        return self._format(cache, self.static_value, resolved_from)

    @property
    def value_type(self) -> object:
        return type(self.static_value)


@dataclass
class NmkResolvedConfig(NmkConfig):
    resolver: Callable

    def resolve(self, cache: bool = True, resolved_from: Set[str] = None) -> Union[str, int, bool, list, dict]:
        # Always disable cache if resolver is volatile
        return super().resolve(cache and not self.resolver.is_volatile(self.name), resolved_from)

    def _get_value(self, cache: bool, resolved_from: Set[str] = None) -> Union[str, int, bool, list, dict]:
        try:
            # Cache value from resolver if not done yet, or redo if value is declared to be volatile
            out = self.resolver.get_value(self.name)

            # Make sure the resolver has returned expected type
            got_type = type(out)
            declared_type = self.value_type
            assert isinstance(out, declared_type), f"Invalid type returned by resolver: got {got_type.__name__}, expecting {declared_type.__name__}"
            return self._format(cache, out, resolved_from)
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
    static_list: List[NmkStaticConfig] = field(default_factory=list)


@dataclass
class NmkListConfig(NmkMergedConfig):
    def _get_value(self, cache: bool, resolved_from: Set[str] = None) -> list:
        # Merge lists
        return [self._format(cache, v, resolved_from, path=holder.path) for holder in self.static_list for v in holder._get_value(cache)]

    @property
    def value_type(self) -> object:
        return list


@dataclass
class NmkDictConfig(NmkMergedConfig):
    def _get_value(self, cache: bool, resolved_from: Set[str] = None) -> dict:
        # Merge dicts
        out = {}
        for holder in self.static_list:
            out.update({k: self._format(cache, v, resolved_from, path=holder.path) for k, v in holder._get_value(cache).items()})
        return out

    @property
    def value_type(self) -> object:
        return dict
