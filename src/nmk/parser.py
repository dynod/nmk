import logging
import shutil
import sys
from argparse import ZERO_OR_MORE, ArgumentParser, Namespace
from pathlib import Path
from typing import List

import argcomplete

from nmk import __version__
from nmk.errors import NmkNoLogsError
from nmk.logs import logging_setup


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
            "--log-file", metavar="L", default="{ROOTDIR}/.nmk/nmk.log", help="write logs to L (default: {ROOTDIR}/.nmk/nmk.log)"
        ).completer = argcomplete.completers.FilesCompleter(directories=True)
        lg.add_argument("--no-logs", action="store_true", default=False, help="disable logging")

        # Root folder
        rg = self.parser.add_argument_group("root folder options")
        rg.add_argument(
            "-r", "--root", metavar="R", type=Path, default=None, help="root folder (default: virtual env parent)"
        ).completer = argcomplete.completers.DirectoriesCompleter()
        rg.add_argument("--no-cache", action="store_true", default=False, help="clear cache before resolving references")

        # Project
        pg = self.parser.add_argument_group("project options")
        pg.add_argument(
            "-p", "--project", metavar="P", default="nmk.yml", help="project file (default: nmk.yml)"
        ).completer = argcomplete.completers.FilesCompleter(allowednames=["*.yml", "*.yaml"], directories=True)

        # Config
        cg = self.parser.add_argument_group("config options")
        cg.add_argument("--config", metavar="JSON", help="contribute to config from json fragment")
        cg.add_argument("--print", metavar="K", action="append", help="print required config item(s) and exit")

        # Build
        bg = self.parser.add_argument_group("build options")
        bg.add_argument("--dry-run", action="store_true", default=False, help="list tasks to be executed and exit")

        # Handle completion
        argcomplete.autocomplete(self.parser)

    def parse(self, argv: List[str]) -> Namespace:
        # Parse arguments
        args = self.parser.parse_args(argv)

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
        logging_setup(args)

        return args
