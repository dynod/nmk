import importlib.resources
import json
import os
import re
import shutil
import sys
from argparse import Namespace
from pathlib import Path

from nmk._internal.cache import get_referenced_wheels
from nmk._internal.files import NmkModelFile
from nmk.errors import NmkNoLogsError
from nmk.logs import NmkLogger, logging_setup
from nmk.model.config import NmkStaticConfig
from nmk.model.keys import NmkRootConfig
from nmk.model.model import NmkModel

# Config pattern
CONFIG_STRING_PATTERN = re.compile("^([^ =]+)=(.*)$")


class NmkLoader:
    def __init__(self, args: Namespace, with_logs: bool = True):
        # Finish args parsing
        self.finish_parsing(args, with_logs)

        # Prepare repo cache and empty model
        self.root_nmk_dir = args.nmk_dir
        self.repo_cache: Path = self.root_nmk_dir / "cache"
        self.model = NmkModel(args)

        # Load model
        self.load_model_from_files()

        # Override config from args, if any
        config_list = self.model.args.config
        if config_list is not None and len(config_list):
            self.override_config(config_list)

        # Validate tasks after full loading process
        self.validate_tasks()

    def load_model_from_files(self):
        # Add built-in config items
        root = self.model.args.root.resolve()
        for name, value in {
            NmkRootConfig.BASE_DIR: "",  # Useless while directly referenced (must identify current project file parent dir)
            NmkRootConfig.ROOT_DIR: root,
            NmkRootConfig.ROOT_NMK_DIR: self.root_nmk_dir,
            NmkRootConfig.CACHE_DIR: self.repo_cache,
            NmkRootConfig.PROJECT_DIR: "",  # Will be updated as soon as initial project is loaded
            NmkRootConfig.PROJECT_NMK_DIR: "",  # Will be updated as soon as initial project is loaded
            NmkRootConfig.PROJECT_FILES: [],  # Will be updated as soon as files are loaded
            NmkRootConfig.ENV: dict(os.environ),
            NmkRootConfig.PACKAGES_REFS: [],  # Will be updated as soon as files are loaded
        }.items():
            self.model.add_config(name, None, value)

        # Init inner model loading
        NmkModelFile(Path(importlib.resources.files("nmk.model")) / "internal.yml", self.repo_cache, self.model, [], is_internal=True)

        # Init recursive files loading
        NmkModelFile(self.model.args.project, self.repo_cache, self.model, [])

        # Loop 1: load python paths
        for m in self.model.file_models.values():
            file_model: NmkModelFile = m
            file_model.load_paths()

        # Loop 2: load config items + tasks
        for m in self.model.file_models.values():
            file_model: NmkModelFile = m
            file_model.load_config()
            file_model.load_tasks()

        # Refresh items once the whole model is loaded
        NmkLogger.debug("Updating settings now that all files are loaded")
        self.model.config[NmkRootConfig.PROJECT_FILES] = NmkStaticConfig(NmkRootConfig.PROJECT_FILES, self.model, None, list(self.model.file_paths))
        self.model.config[NmkRootConfig.PACKAGES_REFS] = NmkStaticConfig(NmkRootConfig.PACKAGES_REFS, self.model, None, get_referenced_wheels())

    def override_config(self, config_list: list[str]):
        # Iterate on config
        for config_str in config_list:
            override_config = {}

            # Json fragment?
            if config_str[0] == "{":
                # Load json fragment from config arg, if any
                try:
                    override_config = json.loads(config_str)
                except Exception as e:
                    raise Exception(f"Invalid Json fragment for --config option: {e}") from e

            # Single config string?
            else:
                m = CONFIG_STRING_PATTERN.match(config_str)
                assert m is not None, f"Config option is neither a json object nor a K=V string: {config_str}"
                override_config = {m.group(1): m.group(2)}

            # Override model config with command-line values
            if len(override_config):
                NmkLogger.debug(f"Overriding config from --config option ({config_str})")
                for k, v in override_config.items():
                    self.model.add_config(k, None, v)

    def finish_parsing(self, args: Namespace, with_logs: bool):
        # Handle root folder
        if args.root is None:  # pragma: no cover
            # By default, root dir is the parent folder of currently running venv
            if sys.prefix == sys.base_prefix:
                raise NmkNoLogsError("nmk must run from a virtual env; can't find root dir")
            args.root = Path(sys.prefix).parent
        else:
            # Verify custom root
            if not args.root.is_dir():
                raise NmkNoLogsError(f"specified root directory not found: {args.root}")

        # Handle cache clear
        args.nmk_dir = args.root / ".nmk"
        if args.no_cache and args.nmk_dir.is_dir():
            shutil.rmtree(args.nmk_dir)

        # Setup logging
        if with_logs:
            logging_setup(args)

    def validate_tasks(self):
        # Iterate on tasks: pass 1 --> resolve references
        for task in self.model.tasks.values():
            # Resolve references
            task._resolve_subtasks()
            task._resolve_contribs()

        # Iterate on tasks: pass 2 --> skip tasks (and their sub-tasks)
        filtered = set()
        for filtered_name, task in filter(lambda t: t[0] in self.model.args.skipped_tasks, self.model.tasks.items()):
            task._skip()
            filtered.add(filtered_name)

        # Unknown skipped task?
        unknown_tasks = set(self.model.args.skipped_tasks) - filtered
        assert len(unknown_tasks) == 0, f"unknown skipped task(s): {', '.join(list(unknown_tasks))}"
