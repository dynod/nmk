"""
nmk internal config item keys
"""


class NmkRootConfig:
    """
    Built-in config items keys
    """

    BASE_DIR = "BASEDIR"
    """Path to directory holding current project file"""

    ROOT_DIR = "ROOTDIR"
    """Path to the **nmk** root directory (parent of the venv folder)"""

    ROOT_NMK_DIR = "ROOTDIR_NMK"
    """Path to the **.nmk** directory relative to root folder"""

    CACHE_DIR = "CACHEDIR"
    """Path to the **nmk** cache directory"""

    PROJECT_DIR = "PROJECTDIR"
    """Path to the parent directory of the main project file"""

    PROJECT_NMK_DIR = "PROJECTDIR_NMK"
    """Path to the **.nmk** directory relative to project folder"""

    PROJECT_FILES = "PROJECTFILES"
    """List of all resolved project files (by following references from main project file)"""

    ENV = "ENV"
    """Current **nmk** process environment variables"""

    PACKAGES_REFS = "PACKAGESREFS"
    """List of python packages referenced by the current project"""
