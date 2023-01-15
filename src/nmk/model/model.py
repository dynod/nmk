import importlib
import sys
from argparse import Namespace
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Union

from nmk.logs import NmkLogger
from nmk.model.config import NmkConfig, NmkDictConfig, NmkListConfig, NmkResolvedConfig, NmkStaticConfig
from nmk.model.keys import NmkRootConfig
from nmk.model.task import NmkTask

# Class separator
CLASS_SEP = "."


def contribute_python_path(paths: List[str]):
    # Extra paths?
    added_paths = [p for p in paths if p not in sys.path]
    if len(added_paths):
        NmkLogger.debug(f"Contributed python paths: {added_paths}")
        for added_path in added_paths:
            # Path must be a directory
            assert Path(added_path).is_dir(), f"Contributed python path is not found: {added_path}"
            sys.path.append(added_path)


@dataclass
class NmkModel:
    args: Namespace
    files: Dict[Path, object] = field(default_factory=dict)
    config: Dict[str, NmkConfig] = field(default_factory=dict)
    tasks: Dict[str, NmkTask] = field(default_factory=dict)
    default_task: NmkTask = None
    tasks_config: Dict[str, NmkConfig] = field(default_factory=dict)

    def add_config(
        self, name: str, path: Path, init_value: Union[str, int, bool, list, dict] = None, resolver: object = None, task_config: bool = False
    ) -> NmkConfig:
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
            cfg = NmkResolvedConfig(name, self, path, resolver)
            new_type = cfg.value_type

        # Config object to work with
        config_dict = self.tasks_config if task_config else self.config

        # Overriding?
        old_config = config_dict[name] if name in config_dict else None
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
        assert CLASS_SEP in qualified_class, f"Invalid class qualified name: {qualified_class} (missing separator: {CLASS_SEP})"
        class_parts = qualified_class.split(CLASS_SEP)

        # Contribute to python path
        contribute_python_path(self.config[NmkRootConfig.PYTHON_PATH].resolve(False))

        try:
            # Load specified class
            mod_name = CLASS_SEP.join(class_parts[:-1])
            cls_name = class_parts[-1]
            mod = importlib.import_module(mod_name)
            assert hasattr(mod, cls_name), f"Can't find class {cls_name} in module {mod_name}"
            out = getattr(mod, cls_name)(self)
        except Exception as e:
            raise Exception(f"Can't instantiate class {qualified_class}: {e}")

        # Verify type is as expected
        assert isinstance(
            out, expected_type
        ), f"Unexpected type for loaded class {qualified_class}: got {type(out).__name__}, expecting {expected_type.__name__} subclass"
        return out

    def add_task(self, task: NmkTask):
        NmkLogger.debug(f"{'Override' if task.name in self.tasks else 'New'} task {task.name}")

        # Shortcut to task model in builder
        if task.builder is not None:
            task.builder.update_task(task)

        # Store in model
        self.tasks[task.name] = task

    def set_default_task(self, name: str):
        # Just point to default task
        NmkLogger.debug(f"New default task: {name}")
        self.default_task = self.tasks[name]
