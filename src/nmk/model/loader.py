import json
import logging
import os
from argparse import Namespace
from pathlib import Path

from nmk.errors import NmkStopHereError
from nmk.logs import NmkLogger
from nmk.model.config import NmkStaticConfig
from nmk.model.files import NmkModelFile
from nmk.model.keys import NmkRootConfig
from nmk.model.model import NmkModel


class NmkLoader:
    def __init__(self, args: Namespace):
        # Prepare repo cache and empty model
        self.repo_cache: Path = args.nmk_dir / "cache"
        self.model = NmkModel(args)

        # Add built-in config items
        root = args.root.resolve()
        for name, value in {
            NmkRootConfig.PYTHON_PATH: [],
            NmkRootConfig.BASE_DIR: "",  # Useless while directly referenced (must identify current project file parent dir)
            NmkRootConfig.ROOT_DIR: root,
            NmkRootConfig.CACHE_DIR: root / ".nmk",
            NmkRootConfig.PROJECT_DIR: "",  # Will be updated as soon as initial project is loaded
            NmkRootConfig.PROJECT_FILES: [],  # Will be updated as soon as files are loaded
            NmkRootConfig.ENV: {k: v for k, v in os.environ.items()},
        }.items():
            self.model.add_config(name, None, value)

        # Load json fragment from config arg, if any
        try:
            override_config = json.loads(args.config) if args.config is not None else {}
        except Exception as e:
            raise Exception(f"Invalid Json fragment for --config option: {e}")
        assert isinstance(override_config, dict), "Json fragment for --config option must be an object"

        # Init recursive files loading loop
        NmkModelFile(args.project, self.repo_cache, self.model, [])

        # Refresh project files list
        NmkLogger.debug(f"Updating {NmkRootConfig.PROJECT_FILES} now that all files are loaded")
        self.model.config[NmkRootConfig.PROJECT_FILES] = NmkStaticConfig(NmkRootConfig.PROJECT_FILES, self.model, None, list(self.model.files.keys()))

        # Override model config with command-line values
        if len(override_config):
            NmkLogger.debug("Overriding config from --config option")
            for k, v in override_config.items():
                self.model.add_config(k, None, v)

        # Validate tasks after full loading process
        self.validate_tasks()

        # Print config is required
        if args.print is not None and len(args.print):
            for k in args.print:
                assert k in self.model.config, f"Unknown config item key: {k}"

            def prepare_for_json(v):
                if isinstance(v, list):
                    return list(map(prepare_for_json, v))
                if isinstance(v, dict):
                    return {k: prepare_for_json(v) for k, v in v.items()}
                return v if type(v) in [int, str, bool] else str(v)

            dump_dict = json.dumps(
                {k: prepare_for_json(c.value) for k, c in filter(lambda t: t[0] in args.print, self.model.config.items())}, indent=-1
            ).replace("\n", " ")
            if args.log_level >= logging.WARNING:
                # Quiet mode
                print(dump_dict)
            else:
                # Normal mode
                NmkLogger.info("newspaper", f"Config dump: {dump_dict}")

            # Stop here
            raise NmkStopHereError()

    def validate_tasks(self):
        # Iterate on tasks
        for task in self.model.tasks.values():
            # Resolve references
            task._resolve_subtasks()
            task._resolve_contribs()
