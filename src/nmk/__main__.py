import sys
import traceback
from typing import List

from nmk.errors import NmkNoLogsError, NmkStopHereError
from nmk.logs import NmkLogger
from nmk.model.loader import NmkLoader
from nmk.parser import NmkParser


# CLI entry point
def nmk(argv: List[str]) -> int:
    try:
        # Build parser and parse input args
        args = NmkParser().parse(argv)
        out = 0
    except NmkNoLogsError as e:
        # Just print error (log system isn't ready yet)
        print(str(e))
        out = 1

    if out == 0:
        try:
            # Load build model
            NmkLoader(args)

            # TODO Trigger build
            NmkLogger.info("checkered_flag", "Nothing to do")
        except Exception as e:
            if not isinstance(e, NmkStopHereError):
                list(map(NmkLogger.error, str(e).split("\n")))
                list(map(NmkLogger.debug, "".join(traceback.format_tb(e.__traceback__)).split("\n")))
                out = 1
    return out


def main() -> int:  # pragma: no cover
    return nmk(sys.argv)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
