import logging
from argparse import Namespace
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
                log_file = Path(args.log_file.format(out=args.output, time=args.start_time.strftime("%Y-%m-%d-%H-%M-%S")))
                log_file.parent.mkdir(parents=True, exist_ok=True)
                logging.basicConfig(
                    force=True, level=logging.DEBUG, format=LOG_FORMAT_DEBUG, datefmt=coloredlogs.DEFAULT_DATE_FORMAT, filename=log_file, filemode="w"
                )

            # Colored logs install
            coloredlogs.install(level=args.log_level, fmt=LOG_FORMAT if args.log_level > logging.DEBUG else LOG_FORMAT_DEBUG)

        # First log line
        cls.debug(f"nmk version {__version__}")

    @classmethod
    def log(cls, level: int, emoji: str, line: str):
        cls.LOG.log(level, f"{Emoji(emoji)} - {line}")

    @classmethod
    def info(cls, emoji: str, line: str):
        cls.log(logging.INFO, emoji, line)

    @classmethod
    def debug(cls, line: str):
        cls.log(logging.DEBUG, "bug", line)

    @classmethod
    def error(cls, line: str):
        cls.log(logging.ERROR, "skull", line)

    @classmethod
    def warning(cls, line: str):
        cls.log(logging.WARNING, "exclamation", line)
