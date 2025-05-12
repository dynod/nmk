"""
nmk configuration objects
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Union

from nmk.model.keys import NmkRootConfig

CONFIG_REF_PATTERN = re.compile(r"(^|[^$])(\$\{([^ \}]+)\})")
"""Pattern to locate config reference in string"""

# Group indexes for config refs
_CONFIG_REF_FULL = 0
_CONFIG_REF_PREFIX = 1
_CONFIG_REF_TO_REPLACE = 2
_CONFIG_REF_NAME = 3

# Escaped reference prefix
_ESCAPED_REF_PREFIX = "$${"

FINAL_ITEM_PATTERN = re.compile("^[A-Z0-9_]+$")
"""Pattern to recognize final config items"""


# Compute reference name (+doted segments) from config reference
def _get_ref_name(m: re.Match, name: str, model) -> tuple[str, bool, list[str]]:
    # Look for referenced config item name
    ref_name: str = m.group(_CONFIG_REF_NAME)

    # Relative path reference
    relative_path = ref_name.startswith("r!")
    if relative_path:
        ref_name = ref_name[2:]

    # Handle doted references (for dicts)
    if "." in ref_name:
        segments = ref_name.split(".")
        ref_name = segments[0]
    else:
        segments = None

    # Resolve from config
    assert ref_name in model.config, f"Unknown '{ref_name}' config referenced from '{name}' config"

    return ref_name, relative_path, segments


@dataclass
class NmkConfig(ABC):
    """
    nmk configuration item base class
    """

    name: str
    """Item name"""

    model: object
    """Model instance"""

    path: Path
    """Defining project file path"""

    @property
    def is_final(self) -> bool:
        """
        Returns true if current item is a final one
        """
        return FINAL_ITEM_PATTERN.match(self.name) is not None

    @property
    def value(self) -> Union[str, int, bool, list, dict]:
        """
        Returns current item value
        """
        return self.resolve()

    def resolve(self, cache: bool = True, resolved_from: set[str] = None) -> Union[str, int, bool, list, dict]:
        """
        Resolves item value

        :param cache: use cached value, if already resolved
        :param resolved_from: set of item names referencing this item
        :return: resolved item value
        """

        # Check for volatile item
        is_volatile = self.volatile if hasattr(self, "volatile") else False

        # Check for cached value
        cached_value = self.cached_value if hasattr(self, "cached_value") else None

        # Check for cached value
        if not cache or cached_value is None or is_volatile:
            # Get value from implementation
            out = self._get_value(cache, resolved_from)

            # Cache resolved value? (unless volatile)
            if cache and not is_volatile:
                self.cached_value = out
        else:
            # Use cached value
            out = self.cached_value

        return out

    # Process item references
    def _format(
        self, cache: bool, candidate: Union[str, int, bool, list, dict], resolved_from: set[str] = None, path: Path = None
    ) -> Union[str, int, bool, list, dict]:
        resolved_from = set(resolved_from) if resolved_from is not None else set()
        resolved_from.add(self.name)

        # Map dicts and lists
        if isinstance(candidate, list):
            return [self._format(cache, c, resolved_from, path) for c in candidate]
        if isinstance(candidate, dict):
            return {self._format(cache, k, resolved_from, path): self._format(cache, v, resolved_from, path) for k, v in candidate.items()}
        if not isinstance(candidate, str):
            # Nothing to format
            return candidate

        # Iterate on <xxx> references
        m = True
        to_format = candidate
        while m is not None:
            m = CONFIG_REF_PATTERN.search(to_format)
            if m is not None:
                # Look for referenced config item name, and potential doted segments + relative path option
                ref_name, relative_path, segments = _get_ref_name(m, self.name, self.model)

                if ref_name == NmkRootConfig.BASE_DIR:
                    # Resolve current path
                    ref_value = str(path if path is not None else self.path)
                else:
                    # Check for cyclic reference
                    assert ref_name not in resolved_from, f"Cyclic string substitution: resolving (again!) '{ref_name}' config from '{self.name}' config"  # NOQA:B028

                    # Resolve reference from config
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
                    except ValueError as e:
                        # Invalid relative reference
                        raise AssertionError(f"Invalid relative path reference: {m.group(0)}") from e

                # Replace with resolved value
                begin, end = m.span(_CONFIG_REF_TO_REPLACE)
                if m.group(_CONFIG_REF_FULL) == to_format and not isinstance(ref_value, str):
                    # Stop here, with raw non-string value
                    return ref_value
                to_format = to_format[0:begin] + str(ref_value) + to_format[end:]

        # Return formatted value (handling escaped prefix only if resolving at top level)
        return to_format.replace(_ESCAPED_REF_PREFIX, "${") if (len(resolved_from) == 1) else to_format

    @abstractmethod
    def _get_value(self, cache: bool, resolved_from: set[str] = None) -> Union[str, int, bool, list, dict]:  # pragma: no cover
        """
        Internal value access
        """
        pass

    @property
    @abstractmethod
    def value_type(self) -> object:  # pragma: no cover
        """
        Value type for this item; to be overridden by sub-classes

        :return: value type
        """
        pass


@dataclass
class NmkStaticConfig(NmkConfig):
    """
    Static config item (defined in project file)
    """

    static_value: Union[str, int, bool, list, dict]
    """Project defined value"""

    volatile: bool = False
    """Disable cache for this item"""

    def __post_init__(self):
        # Detect value type once for all
        self._type = type(self.static_value)

        # Specific handling for string items
        if isinstance(self.static_value, str):
            # Consider string items containing escaped references ($${xxx}) as volatile
            if _ESCAPED_REF_PREFIX in self.static_value:
                self.volatile = True
            else:
                # Check for reference
                m = CONFIG_REF_PATTERN.match(self.static_value)
                if m is not None and m.group(_CONFIG_REF_FULL) == self.static_value:
                    # Value is actually a simple reference: use referenced item type
                    ref_name, _, _ = _get_ref_name(m, self.name, self.model)
                    self._type = self.model.config[ref_name].value_type

    def _get_value(self, cache: bool, resolved_from: set[str] = None) -> Union[str, int, bool, list, dict]:
        # Simple static value
        return self._format(cache, self.static_value, resolved_from)

    @property
    def value_type(self) -> object:
        """
        Value type for this static item

        :return: value type
        """

        return self._type


@dataclass
class NmkMergedConfig(NmkConfig):
    """
    Merged config item base class
    """

    static_list: list[NmkStaticConfig] = field(default_factory=list)
    """List of merged static items"""

    def traverse_list(self, items: list, out_list: list, cache: bool, resolved_from: set[str], holder):
        """
        Recursive list resolution

        :param items: list of items to be traversed
        :param out_list: resolved output list
        :param cache: use cache or not
        :param resolved_from: set of item names referencing this item
        """
        for value in items:
            if isinstance(value, list):
                # Go deeper in this sub-list
                self.traverse_list(value, out_list, cache, resolved_from, holder)
            else:
                # Simple list append
                out_list.append(value)

    def traverse_dict(self, items: dict, out_dict: dict, cache: bool, resolved_from: set[str], holder):
        """
        Recursive dict resolution

        :param items: dict of items to be traversed
        :param out_dict: resolved output dict
        :param cache: use cache or not
        :param resolved_from: set of item names referencing this item
        """

        for k, value in items.items():
            if isinstance(value, dict):
                # Recursively merge this dict
                if k not in out_dict:
                    out_dict[k] = {}
                self.traverse_dict(value, out_dict[k], cache, resolved_from, holder)
            elif isinstance(value, list):
                # Recursively merge this list
                if k not in out_dict:
                    out_dict[k] = []
                self.traverse_list(value, out_dict[k], cache, resolved_from, holder)
            else:
                # Simple item: override
                out_dict[k] = value


@dataclass
class NmkListConfig(NmkMergedConfig):
    """
    Merged list config item
    """

    def _get_value(self, cache: bool, resolved_from: set[str] = None) -> list:
        # Merge lists (recursively)
        out = []
        for holder in self.static_list:
            self.traverse_list(holder._get_value(cache), out, cache, resolved_from, holder)
        return out

    @property
    def value_type(self) -> object:
        """
        Value type for this item

        :return: list type
        """
        return list


@dataclass
class NmkDictConfig(NmkMergedConfig):
    """
    Merged list config item
    """

    def _get_value(self, cache: bool, resolved_from: set[str] = None) -> dict:
        # Merge dicts and lists (recursively)
        out = {}
        for holder in self.static_list:
            self.traverse_dict(holder._get_value(cache), out, cache, resolved_from, holder)
        return out

    @property
    def value_type(self) -> object:
        """
        Value type for this item

        :return: dict type
        """
        return dict


@dataclass
class NmkResolvedConfig(NmkConfig):
    """
    Resolved config item class
    """

    resolver: Callable
    """Config resolver instance for this item"""

    params: NmkDictConfig
    """Resolver parameters"""

    def resolve(self, cache: bool = True, resolved_from: set[str] = None) -> Union[str, int, bool, list, dict]:
        """
        Resolves item value (with disabled cache if resolver is volatile)

        :param cache: use cached value, if already resolved
        :param resolved_from: set of item names referencing this item
        :return: resolved item value
        """
        return super().resolve(cache and not self.resolver.is_volatile(self.name), resolved_from)

    def _get_value(self, cache: bool, resolved_from: set[str] = None) -> Union[str, int, bool, list, dict]:
        try:
            # Cache value from resolver if not done yet, or redo if value is declared to be volatile
            params = self.params.value if self.params is not None else {}
            out = self.resolver.get_value(self.name, **params)

            # Make sure the resolver has returned expected type
            got_type = type(out)
            declared_type = self.value_type
            assert isinstance(out, declared_type), f"Invalid type returned by resolver: got {got_type.__name__}, expecting {declared_type.__name__}"
            return self._format(cache, out, resolved_from)
        except Exception as e:
            raise Exception(f"Error occurred while resolving config {self.name}: {e}") from e

    @property
    def value_type(self) -> object:
        """
        Value type for this item

        :return: value type
        """
        try:
            # Ask resolver for value type
            return self.resolver.get_type(self.name)
        except Exception as e:
            raise Exception(f"Error occurred while getting type for config {self.name}: {e}") from e
