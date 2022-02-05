class NmkFileLoadingError(Exception):
    def __init__(self, project: str, message: str):
        super().__init__(f"While loading {project}: {message}")


class NmkNoLogsError(Exception):
    pass


class NmkStopHereError(Exception):
    pass
