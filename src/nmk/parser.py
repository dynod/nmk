import logging
from argparse import ZERO_OR_MORE, ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path
from typing import List

import argcomplete
import coloredlogs

from nmk import __version__

# Displayed logs format
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


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

        # Setup logging (if not disabled)
        if not args.no_logs:
            if len(args.log_file):
                # Handle output log file (generate it from pattern, and create parent folder if needed)
                log_file = Path(args.log_file.format(out=args.output, time=args.start_time.strftime("%Y-%m-%d-%H-%M-%S")))
                log_file.parent.mkdir(parents=True, exist_ok=True)
                logging.basicConfig(
                    force=True, level=logging.DEBUG, format=LOG_FORMAT, datefmt=coloredlogs.DEFAULT_DATE_FORMAT, filename=log_file, filemode="w"
                )

            # Colored logs install
            coloredlogs.install(level=args.log_level, fmt=LOG_FORMAT)

        return args
