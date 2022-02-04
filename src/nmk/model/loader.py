import json
import logging
from argparse import Namespace
from pathlib import Path

from nmk.errors import NmkStopHereError
from nmk.logs import NmkLogger
from nmk.model.files import NmkModelFile
from nmk.model.keys import NmkRootConfig
from nmk.model.model import NmkModel


class NmkLoader:
    def __init__(self, args: Namespace):
        # Prepare repo cache and empty model
        self.repo_cache: Path = args.cache / "cache"
        self.model = NmkModel()

        # Add "root" config items
        self.model.add_config(NmkRootConfig.PYTHON_PATH, None, [])
        self.model.add_config(NmkRootConfig.BASE_DIR, None, "")

        # Load json fragment from config arg, if any
        try:
            override_config = json.loads(args.config) if args.config is not None else {}
        except Exception as e:
            raise Exception(f"Invalid Json fragment for --config option: {e}")
        assert isinstance(override_config, dict), "Json fragment for --config option must be an object"

        # Init recursive files loading loop
        NmkModelFile(args.project, self.repo_cache, self.model, [])

        # Override model config with command-line values
        if len(override_config):
            NmkLogger.debug("Overriding config from --config option")
            for k, v in override_config.items():
                self.model.add_config(k, None, v)

        # Print config is required
        if args.print is not None and len(args.print):
            for k in args.print:
                assert k in self.model.config, f"Unknown config item key: {k}"
            dump_dict = json.dumps({k: c.value for k, c in filter(lambda t: t[0] in args.print, self.model.config.items())}, indent=-1).replace("\n", " ")
            if args.log_level >= logging.WARNING:
                # Quiet mode
                print(dump_dict)
            else:
                # Normal mode
                NmkLogger.info("newspaper", f"Config dump: {dump_dict}")

            # Stop here
            raise NmkStopHereError()
