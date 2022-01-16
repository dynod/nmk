from configparser import ConfigParser
from pathlib import Path

from pkg_resources import DistributionNotFound, get_distribution

__title__ = "nmk"
try:
    __version__ = get_distribution(__title__).version
except DistributionNotFound:  # pragma: no cover
    # For debug
    with (Path(__file__).parent.parent.parent / "setup.cfg").open("r") as f:
        c = ConfigParser()
        c.read_file(f.readlines())
        __version__ = c.get("metadata", "version")
