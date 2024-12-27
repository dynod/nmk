"""
Python module for **nmk** tool
"""

from importlib.metadata import version

__title__ = "nmk"
try:
    __version__ = version(__title__)
except Exception:  # pragma: no cover
    # For debug
    __version__ = "unknown"
