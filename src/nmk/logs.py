import logging
import logging.handlers
from argparse import Namespace
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union

import coloredlogs
from rich.emoji import Emoji
from rich.text import Text

from nmk import __version__

"""
Logs handling for nmk
"""


LOG_FORMAT = "%(asctime)s (%(levelname).1s) %(prefix)s%(name)s %(message)s"
"""Displayed logs format"""

LOG_FORMAT_DEBUG = "%(asctime)s.%(msecs)03d (%(levelname).1s) %(prefix)s%(name)s %(message)s - %(filename)s:%(funcName)s:%(lineno)d"
"""File logs format"""

# One megabyte
_ONE_MB = 1024 * 1024


class NmkLogWrapper:
    """
    Wrapped logger, handling logs with emojis!

    :param logger: logger instance to be wrapped
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def __log(self, level: int, emoji: Union[str, Emoji, Text], line: str):
        self._logger.log(level, f"{Emoji(emoji) if isinstance(emoji, str) else emoji} - {line}", stacklevel=3)

    def log(self, level: int, emoji: str, line: str):
        """
        Log provided message string + emoji, on required level

        :param level: log level
        :param emoji: emoji code or format string
        :param line: message string to be logged
        """
        self.__log(level, emoji, line)

    def info(self, emoji: str, line: str):
        """
        Log provided message string + emoji, on INFO level

        :param emoji: emoji code or format string
        :param line: message string to be logged
        """
        self.__log(logging.INFO, emoji, line)

    def debug(self, line: str):
        """
        Log provided message string (with default emoji), on DEBUG level

        :param line: message string to be logged
        """
        self.__log(logging.DEBUG, "bug", line)

    def error(self, line: str):
        """
        Log provided message string (with default emoji), on ERROR level

        :param line: message string to be logged
        """
        self.__log(logging.ERROR, "skull", line)

    def warning(self, line: str):
        """
        Log provided message string (with default emoji), on WARNING level

        :param line: message string to be logged
        """
        self.__log(logging.WARNING, "exclamation", line)


NmkLogger = NmkLogWrapper(logging.getLogger("nmk"))
"""Root logger instance"""


def logging_initial_setup(args: Namespace) -> Union[logging.handlers.MemoryHandler, None]:
    """
    Logging setup for nmk

    :param args: parsed args from the command line
    :return: memory handler used for logging, or None if no logs are enabled
    """

    # Setup logging (if not disabled)
    mem_handler = None
    if not args.no_logs:
        # Basic init, with memory handler (to be flushed later)
        logging.basicConfig(force=True, level=logging.DEBUG)
        mem_handler = logging.handlers.MemoryHandler(capacity=_ONE_MB, target=None, flushLevel=logging.FATAL)
        logging.getLogger().addHandler(mem_handler)

        # Colored logs install
        coloredlogs.install(level=args.log_level, fmt=LOG_FORMAT if args.log_level > logging.DEBUG else LOG_FORMAT_DEBUG)

        # Add prefix keyword if configured
        used_logs_prefix = (args.log_prefix + " ") if args.log_prefix else ""
        _old_record_factory = logging.getLogRecordFactory()

        def _prefixed_log_record_factory(*p_args, **kw_args):
            """
            Custom log record factory to add prefix
            """
            record = _old_record_factory(*p_args, **kw_args)
            record.prefix = used_logs_prefix
            return record

        logging.setLogRecordFactory(_prefixed_log_record_factory)

    # First log line
    NmkLogger.debug(f"----- nmk version {__version__} -----")
    NmkLogger.debug(f"called with args: {args}")
    if args.no_cache:
        NmkLogger.debug("Cache cleared!")
    return mem_handler


def logging_finalize_setup(log_file_str: str, model_paths_keywords: dict[str, str], memory_handler: Union[logging.handlers.MemoryHandler, None]):
    """
    Finalize logs setup, once nmk project folder has been setup

    :param log_file_str: log file path pattern (from command line args)
    :param model_paths_keywords: keywords to be used in the log file path pattern (computed from nmk model)
    :param memory_handler: memory handler used for logging, or None if no logs are enabled
    """

    if not memory_handler:
        # No logs to write, just return
        return

    if log_file_str:
        # Handle output log file (generate it from pattern, and create parent folder if needed)
        log_file = Path(log_file_str.format(**model_paths_keywords))
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(log_file, maxBytes=_ONE_MB, backupCount=5, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT_DEBUG, datefmt=coloredlogs.DEFAULT_DATE_FORMAT))
        logging.getLogger().addHandler(file_handler)

        # Provide log file handler to pending memory handler
        memory_handler.setTarget(file_handler)

    # Just close the memory handler to flush pending logs
    memory_handler.close()
