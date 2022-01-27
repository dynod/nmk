import sys
import traceback
from typing import List

from nmk.logs import NmkLogger
from nmk.model.loader import NmkModel
from nmk.parser import NmkParser


# CLI entry point
def nmk(argv: List[str]) -> int:
    # Build parser and parse input args
    args = NmkParser().parse(argv)

    try:
        # Load build model
        NmkModel(args)

        # TODO Trigger build
        NmkLogger.info("checkered_flag", "Nothing to do")
        out = 0
    except Exception as e:
        list(map(NmkLogger.error, str(e).split("\n")))
        list(map(NmkLogger.debug, "".join(traceback.format_tb(e.__traceback__)).split("\n")))
        out = 1
    return out


def main() -> int:  # pragma: no cover
    return nmk(sys.argv)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
