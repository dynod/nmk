import logging
from argparse import Namespace
from logging.handlers import RotatingFileHandler
from pathlib import Path

import coloredlogs
from rich.emoji import Emoji

from nmk import __version__

# Displayed logs format
LOG_FORMAT = "%(asctime)s [%(levelname).1s] %(message)s"
LOG_FORMAT_DEBUG = "%(asctime)s.%(msecs)03d [%(levelname).1s] %(name)s %(message)s - %(filename)s:%(funcName)s:%(lineno)d"


# Main logger instance
class NmkLogger:
    LOG = logging.getLogger("nmk")

    @classmethod
    def setup(cls, args: Namespace):
        # Setup logging (if not disabled)
        if not args.no_logs:
            if len(args.log_file):
                # Handle output log file (generate it from pattern, and create parent folder if needed)
                logging.basicConfig(force=True, level=logging.DEBUG)
                log_file = Path(args.log_file.format(ROOTDIR=args.root))
                log_file.parent.mkdir(parents=True, exist_ok=True)
                handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5)
                handler.setFormatter(logging.Formatter(LOG_FORMAT_DEBUG, datefmt=coloredlogs.DEFAULT_DATE_FORMAT))
                logging.getLogger().addHandler(handler)

            # Colored logs install
            coloredlogs.install(level=args.log_level, fmt=LOG_FORMAT if args.log_level > logging.DEBUG else LOG_FORMAT_DEBUG)

        # First log line
        cls.debug(f"----- nmk version {__version__} -----")
        cls.debug(f"called with args: {args}")
        if args.no_cache:
            cls.debug("Cache cleared!")

    @classmethod
    def __log(cls, level: int, emoji: str, line: str):
        cls.LOG.log(level, f"{Emoji(emoji)} - {line}", stacklevel=3)

    @classmethod
    def info(cls, emoji: str, line: str):
        cls.__log(logging.INFO, emoji, line)

    @classmethod
    def debug(cls, line: str):
        cls.__log(logging.DEBUG, "bug", line)

    @classmethod
    def error(cls, line: str):
        cls.__log(logging.ERROR, "skull", line)

    @classmethod
    def warning(cls, line: str):
        cls.__log(logging.WARNING, "exclamation", line)
