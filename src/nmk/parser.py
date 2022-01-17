import logging
from argparse import ZERO_OR_MORE, ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from typing import List

import argcomplete

from nmk import __version__
from nmk.logs import NmkLogger


class NmkParser:
    def __init__(self):
        # Prepare parser
        self.parser = ArgumentParser(description="Next-gen make-like build system")

        # Version handling
        self.parser.add_argument("-V", "--version", action="version", version=f"nmk version {__version__}")

        # Tasks
        self.parser.add_argument("tasks", metavar="task", default=[], nargs=ZERO_OR_MORE, help="build task to execute")

        # Logging
        lg = self.parser.add_argument_group("logging options")
        ll = lg.add_mutually_exclusive_group()
        ll.add_argument(
            "-q",
            "--quiet",
            action="store_const",
            const=logging.WARNING,
            default=logging.INFO,
            dest="log_level",
            help="quiet mode (only warning/error messages)",
        )
        ll.add_argument("--info", action="store_const", const=logging.INFO, default=logging.INFO, dest="log_level", help="default mode")
        ll.add_argument(
            "-v",
            "--verbose",
            action="store_const",
            const=logging.DEBUG,
            default=logging.INFO,
            dest="log_level",
            help="verbose mode (all messages, including debug ones)",
        )
        lg.add_argument(
            "--log-file", metavar="L", default="{out}/{time}-nmk.log", help="write logs to LOG_FILE (default: {out}/{time}-nmk.log)"
        ).completer = argcomplete.completers.FilesCompleter(directories=True)
        lg.add_argument("--no-logs", action="store_true", default=False, help="disable logging")

        # Output
        og = self.parser.add_argument_group("output options")
        og.add_argument(
            "-o", "--output", metavar="O", type=Path, default=Path("out"), help="build output directory (default: out)"
        ).completer = argcomplete.completers.DirectoriesCompleter()

        # Project
        pg = self.parser.add_argument_group("project options")
        pg.add_argument(
            "-p", "--project", metavar="P", type=Path, default=Path("nmk.yml"), help="project file (default: nmk.yml)"
        ).completer = argcomplete.completers.FilesCompleter(allowednames=["*.yml", "*.yaml"], directories=True)

        # Handle completion
        argcomplete.autocomplete(self.parser)

    def parse(self, argv: List[str]) -> Namespace:
        # Parse arguments
        args = self.parser.parse_args(argv)

        # Store start of build timestamp
        args.start_time = datetime.now()

        # Setup logging
        NmkLogger.setup(args)

        return args
