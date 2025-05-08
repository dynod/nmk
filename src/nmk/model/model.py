"""
nmk main model
"""

import importlib
import importlib.abc
import importlib.util
import sys
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

from nmk.logs import NmkLogger
from nmk.model.config import NmkConfig, NmkDictConfig, NmkListConfig, NmkResolvedConfig, NmkStaticConfig
from nmk.model.task import NmkTask

# Class separator
_CLASS_SEP = "."


@dataclass
class _NmkPathFinder(importlib.abc.MetaPathFinder):
    # Dict of contributed files from nmk files
    _path_contribs: dict[str, Path] = field(default_factory=dict)

    # Remember if a file has already been contributed through this finder
    _path_found: dict[str, Path] = field(default_factory=dict)

    # Remember if this finder has been added to the import system
    _registered: bool = False

    def custom_import(self, fullname: str):
        # Check if path:
        # * is a contributed one
        # * is already loaded as system module
        # * has not be found yet by this finder
        if (fullname in self._path_found) and (fullname in sys.modules) and not self._path_found[fullname]:
            # Custom loading of this module
            spec = self.find_spec(fullname, None)
            mod = importlib.util.module_from_spec(spec)

            # Override cache for this module
            sys.modules[fullname] = mod
            spec.loader.exec_module(mod)
            return mod

        # Default import
        return importlib.import_module(fullname)

    def contribute_path(self, paths: list[Path]):
        # Contribute to internal paths list
        added_paths = [x.resolve() for x in paths]
        NmkLogger.debug(f"Contributed python paths: {added_paths}")
        for added_path in added_paths:
            # Path must be a directory
            assert added_path.is_dir(), f"Contributed python path is not found: {added_path}"

            # Remember all found python files
            for f in added_path.rglob("*.py"):
                # Build module name (remove py extension; also remove __init__ for packages)
                name = _CLASS_SEP.join(list(f.relative_to(added_path).parts)).removesuffix(".py").removesuffix(".__init__")
                self._path_contribs[name] = f
                self._path_found[name] = False

            # A new path has been contributed, register in import system
            if not self._registered:  # pragma: no branch
                self._registered = True
                sys.meta_path.append(self)

    def find_spec(self, fullname: str, path: str, target=None):
        # Find in contributes files
        found_path = self._path_contribs.get(fullname, None)
        if found_path:  # pragma: no branch
            self._path_found[fullname] = True
            return importlib.util.spec_from_file_location(fullname, found_path)


@dataclass
class NmkModel:
    """
    nmk model definition
    """

    args: Namespace
    """Command line parsed args"""

    file_paths: list[Path] = field(default_factory=list)
    """List of parsed project file paths"""

    file_models: dict[Path, object] = field(default_factory=dict)
    """Dict of file models indexed by path"""

    config: dict[str, NmkConfig] = field(default_factory=dict)
    """Dict of config item instances"""

    tasks: dict[str, NmkTask] = field(default_factory=dict)
    """Dict of task instances"""

    default_task: NmkTask = None
    """Default task instance"""

    tasks_config: dict[str, NmkConfig] = field(default_factory=dict)
    """Inner tasks config dict"""

    pip_args: str = ""
    """pip command extra args"""

    overridden_refs: dict[str, Path] = field(default_factory=dict)
    """Dict of overridden references"""

    path_finder: _NmkPathFinder = field(default_factory=_NmkPathFinder)
    """Path finder instance"""

    def add_config(
        self,
        name: str,
        path: Path,
        init_value: Union[str, int, bool, list, dict] = None,
        resolver: object = None,
        task_config: bool = False,
        resolver_params: NmkDictConfig = None,
    ) -> NmkConfig:
        """
        Add a config item to model

        :param name: config item name
        :param path: project file defining this item
        :param init_value: initial value for config item
        :param resolver: resolver instance for this item
        :param task_config: use inner task config dict
        :param resolver_params: resolver parameters
        :return: created config item instance
        """

        # Real value?
        is_list = is_dict = False
        if init_value is not None:
            # Yes: with real value read from file
            NmkLogger.debug(f"New static config {name} with value: {init_value}")
            cfg = NmkStaticConfig(name, self, path, init_value)
            is_list = isinstance(init_value, list)
            is_dict = isinstance(init_value, dict)
            new_type = type(init_value)
        else:
            # No: with resolver
            assert resolver is not None, f"Internal error: resolver is not set for config {name}"
            NmkLogger.debug(f"New dynamic config {name} with resolver class {type(resolver).__name__}")
            cfg = NmkResolvedConfig(name, self, path, resolver, resolver_params)
            new_type = cfg.value_type

        # Config object to work with
        config_dict = self.tasks_config if task_config else self.config

        # Overriding?
        old_config = config_dict.get(name, None)
        if old_config is not None:
            NmkLogger.debug(f"Overriding config {name}")
            old_config = config_dict[name]

            # Check for final
            assert not old_config.is_final, f"Can't override final config {name}"

            # Check for type change
            old_type = config_dict[name].value_type
            assert new_type == old_type, f"Unexpected type change for config {name} ({old_type.__name__} --> {new_type.__name__})"

        # Add config to model
        if is_list or is_dict:
            if old_config is None or isinstance(old_config, NmkResolvedConfig):
                # Add multiple config holder (or replace previously installed resolver)
                config_dict[name] = NmkListConfig(name, self, path) if is_list else NmkDictConfig(name, self, path)

            # Add new value to be merged in fine
            config_dict[name].static_list.append(cfg)
        else:
            # Update value
            config_dict[name] = cfg

        return config_dict[name]

    def load_class(self, qualified_class: str, expected_type: object) -> object:
        """
        Create referenced class instance

        :param qualified_class: fully qualified class name
        :param expected_type: expected instance type
        :return: created class instance
        """
        assert _CLASS_SEP in qualified_class, f"Invalid class qualified name: {qualified_class} (missing separator: {_CLASS_SEP})"
        class_parts = qualified_class.split(_CLASS_SEP)

        try:
            # Split module/class names
            mod_name = _CLASS_SEP.join(class_parts[:-1])
            cls_name = class_parts[-1]

            # Import module using custom contributions
            mod = self.path_finder.custom_import(mod_name)

            # Load specified class
            assert hasattr(mod, cls_name), f"Can't find class {cls_name} in module {mod_name}"
            out = getattr(mod, cls_name)(self)
        except Exception as e:
            raise Exception(f"Can't instantiate class {qualified_class}: {e}") from e

        # Verify type is as expected
        assert isinstance(out, expected_type), (
            f"Unexpected type for loaded class {qualified_class}: got {type(out).__name__}, expecting {expected_type.__name__} subclass"
        )
        return out

    def add_task(self, task: NmkTask):
        """
        Add task instance to model

        :param task: task instance to be added
        """

        NmkLogger.debug(f"{'Override' if task.name in self.tasks else 'New'} task {task.name}")

        # Shortcut to task model in builder
        if task.builder is not None:
            task.builder.update_task(task)

        # Store in model
        self.tasks[task.name] = task

    def set_default_task(self, name: str):
        """
        Default task setter

        :param name: name of the new default task
        """

        # Just point to default task
        NmkLogger.debug(f"New default task: {name}")
        self.default_task = self.tasks[name]

    def replace_remote(self, remote: str, local: Path):
        """
        Replace remote reference by local remote reference

        :param remote: remote name
        :param local: local remote path
        """

        # Remember remote ref to be replaced by a local one
        NmkLogger.debug(f"Override all remote refs to {remote} by {local}")
        self.overridden_refs[remote] = local

    def check_remote_ref(self, remote: str) -> Path:
        """
        Check remote reference to potentially replace it by its local equivalent

        :param remote: remote name
        :return: resolved remote path
        """

        # Replace potentially overridden remote ref by its local equivalent
        for prefix in self.overridden_refs:
            if remote.startswith(prefix):
                prefix_len = len(prefix)
                local = self.overridden_refs[prefix] / remote[prefix_len + (1 if remote[prefix_len] == "/" else 0) :]
                NmkLogger.debug(f'Replacing remote ref "{remote}" by overridden local equivalent: "{local}"')
                return local
        return remote
