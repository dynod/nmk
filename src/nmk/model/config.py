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

        # Map dicts and lists
        if isinstance(candidate, list):
            return [self._format(cache, c, resolved_from, path) for c in candidate]
        if isinstance(candidate, dict):
            return {k: self._format(cache, v, resolved_from, path) for k, v in candidate.items()}
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

                # Relative path reference
                relative_path = ref_name.startswith("r!")
                if relative_path:
                    ref_name = ref_name[2:]

                if ref_name == NmkRootConfig.BASE_DIR:
                    # Resolve current path
                    ref_value = str(path if path is not None else self.path)
                else:
                    # Handle doted references (for dicts)
                    if "." in ref_name:
                        segments = ref_name.split(".")
                        ref_name = segments[0]
                    else:
                        segments = None

                    # Resolve from config
                    assert (
                        ref_name not in resolved_from
                    ), f"Cyclic string substitution: resolving (again!) '{ref_name}' config from '{self.name}' config"  # NOQA:B028
                    assert ref_name in self.model.config, f"Unknown '{ref_name}' config referenced from '{self.name}' config"  # NOQA:B028

                    # Resolve reference
                    ref_value = self.model.config[ref_name].resolve(cache, resolved_from)

                    # Doted reference?
                    if segments is not None:
                        # Iterate on segments as long as we get dicts
                        v = ref_value
                        for segment in segments[1:]:
                            assert isinstance(v, dict), f"Doted reference from {self.name} used for {ref_name} value, which is not a dict"
                            assert len(segment), f"Empty doted reference segment from {self.name} for {ref_name} value"
                            assert segment in v, f"Unknown dict key {segment} in doted reference from {self.name} for {ref_name} value"
                            v = v[segment]
                        ref_value = v

                # Relative path required?
                if relative_path:
                    try:
                        # Update path(s) relatively to project root
                        p_dir = self.model.config[NmkRootConfig.PROJECT_DIR].value
                        if isinstance(ref_value, list):
                            ref_value = [Path(v).relative_to(p_dir).as_posix() for v in ref_value]
                        elif isinstance(ref_value, dict):
                            ref_value = {k: Path(v).relative_to(p_dir).as_posix() for k, v in ref_value.items()}
                        else:
                            ref_value = Path(ref_value).relative_to(p_dir).as_posix()
                    except ValueError:
                        # Invalid relative reference
                        raise AssertionError(f"Invalid relative path reference: {m.group(0)}")

                # Replace with resolved value
                begin, end = m.span(0)
                if m.group(0) == to_format and not isinstance(ref_value, str):
                    # Stop here, with raw non-string value
                    return ref_value
                to_format = to_format[0:begin] + str(ref_value) + to_format[end:]
        return to_format

    @abstractmethod
    def _get_value(self, cache: bool, resolved_from: Set[str] = None) -> Union[str, int, bool, list, dict]:  # pragma: no cover
        pass

    @property
    @abstractmethod
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

    # Recursive list resolution
    def traverse_list(self, items: list, out_list: list, cache: bool, resolved_from: Set[str], holder):
        for item in items:
            formatted_item = self._format(cache, item, resolved_from, path=holder.path)
            if isinstance(formatted_item, list):
                # Go deeper in this sub-list
                self.traverse_list(formatted_item, out_list, cache, resolved_from, holder)
            else:
                # Simple list append
                out_list.append(formatted_item)

    # Recursive dict resolution
    def traverse_dict(self, items: dict, out_dict: dict, cache: bool, resolved_from: Set[str], holder):
        for k, v in items.items():
            formatted_item = self._format(cache, v, resolved_from, path=holder.path)
            if isinstance(formatted_item, dict):
                # Recursively merge this dict
                if k not in out_dict:
                    out_dict[k] = {}
                self.traverse_dict(formatted_item, out_dict[k], cache, resolved_from, holder)
            elif isinstance(formatted_item, list):
                # Recursively merge this list
                if k not in out_dict:
                    out_dict[k] = []
                self.traverse_list(formatted_item, out_dict[k], cache, resolved_from, holder)
            else:
                # Simple item: override
                out_dict[k] = formatted_item


@dataclass
class NmkListConfig(NmkMergedConfig):
    def _get_value(self, cache: bool, resolved_from: Set[str] = None) -> list:
        # Merge lists (recursively)
        out = []
        for holder in self.static_list:
            self.traverse_list(holder._get_value(cache), out, cache, resolved_from, holder)
        return out

    @property
    def value_type(self) -> object:
        return list


@dataclass
class NmkDictConfig(NmkMergedConfig):
    def _get_value(self, cache: bool, resolved_from: Set[str] = None) -> dict:
        # Merge dicts and lists (recursively)
        out = {}
        for holder in self.static_list:
            self.traverse_dict(holder._get_value(cache), out, cache, resolved_from, holder)
        return out

    @property
    def value_type(self) -> object:
        return dict
