import logging
from argparse import Namespace
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union

import coloredlogs
from rich.emoji import Emoji
from rich.text import Text

from nmk import __version__

# Displayed logs format
LOG_FORMAT = "%(asctime)s (%(levelname).1s) %(name)s %(message)s"
LOG_FORMAT_DEBUG = "%(asctime)s.%(msecs)03d (%(levelname).1s) %(name)s %(message)s - %(filename)s:%(funcName)s:%(lineno)d"


# Main logger instance
class NmkLogWrapper:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def __log(self, level: int, emoji: Union[str, Emoji, Text], line: str):
        self.logger.log(level, f"{Emoji(emoji) if isinstance(emoji, str) else emoji} - {line}", stacklevel=3)

    def log(self, level: int, emoji: str, line: str):
        self.__log(level, emoji, line)

    def info(self, emoji: str, line: str):
        self.__log(logging.INFO, emoji, line)

    def debug(self, line: str):
        self.__log(logging.DEBUG, "bug", line)

    def error(self, line: str):
        self.__log(logging.ERROR, "skull", line)

    def warning(self, line: str):
        self.__log(logging.WARNING, "exclamation", line)


# Root logger
NmkLogger = NmkLogWrapper(logging.getLogger("nmk"))


def logging_setup(args: Namespace):
    # Setup logging (if not disabled)
    if not args.no_logs:
        if len(args.log_file):
            # Handle output log file (generate it from pattern, and create parent folder if needed)
            logging.basicConfig(force=True, level=logging.DEBUG)
            log_file = Path(args.log_file.format(ROOTDIR=args.root))
            log_file.parent.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(log_file, maxBytes=1024 * 1024, backupCount=5, encoding="utf-8")
            handler.setFormatter(logging.Formatter(LOG_FORMAT_DEBUG, datefmt=coloredlogs.DEFAULT_DATE_FORMAT))
            logging.getLogger().addHandler(handler)

        # Colored logs install
        coloredlogs.install(level=args.log_level, fmt=LOG_FORMAT if args.log_level > logging.DEBUG else LOG_FORMAT_DEBUG)

    # First log line
    NmkLogger.debug(f"----- nmk version {__version__} -----")
    NmkLogger.debug(f"called with args: {args}")
    if args.no_cache:
        NmkLogger.debug("Cache cleared!")
