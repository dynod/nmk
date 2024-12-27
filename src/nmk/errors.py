"""
nmk custom error classes
"""


class NmkFileLoadingError(Exception):
    """
    Error occurring when loading the project file model

    :param project: project file
    :param message: error message
    """

    def __init__(self, project: str, message: str):
        super().__init__(f"While loading {project}: {message}")


class NmkNoLogsError(Exception):
    """
    Error used to raise issues before the logging system is initialized
    """

    pass


class NmkStopHereError(Exception):
    """
    Error usable to stop nmk execution without causing an user error (return code 0)
    """

    pass
