import sys
import traceback

from nmk._internal.build import NmkBuild
from nmk._internal.loader import NmkLoader
from nmk._internal.parser import NmkParser
from nmk.errors import NmkStopHereError
from nmk.logs import NmkLogger


# CLI entry point
def nmk(argv: list[str]) -> int:
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
