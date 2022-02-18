import sys
import traceback
from typing import List

from nmk.build import NmkBuild
from nmk.errors import NmkStopHereError
from nmk.logs import NmkLogger
from nmk.model.loader import NmkLoader
from nmk.parser import NmkParser


# CLI entry point
def nmk(argv: List[str]) -> int:
    # Build parser and parse input args
    args = NmkParser().parse(argv)
    out = 0

    try:
        # Load build model
        model = NmkLoader(args).model

        # Trigger build
        if NmkBuild(model).build():
            NmkLogger.info("checkered_flag", "Done")
        else:
            NmkLogger.info("checkered_flag", "Nothing to do")
    except Exception as e:
        if not isinstance(e, NmkStopHereError):
            list(map(NmkLogger.error, str(e).split("\n")))
            list(map(NmkLogger.debug, "".join(traceback.format_tb(e.__traceback__)).split("\n")))
            out = 1
    return out


def main() -> int:  # pragma: no cover
    return nmk(sys.argv[1:])


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
