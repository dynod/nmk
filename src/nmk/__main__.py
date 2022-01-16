import sys
import traceback
from typing import List

from nmk.model import NmkModel
from nmk.parser import NmkParser


# CLI entry point
def nmk(argv: List[str]) -> int:
    # Build parser and parse input args
    args = NmkParser().parse(argv)

    try:
        # Load build model
        NmkModel(args)

        # TODO Trigger build
        args.logger.info("Nothing to do")
        out = 0
    except Exception as e:
        args.logger.error(e)
        args.logger.debug("".join(traceback.format_tb(e.__traceback__)))
        out = 1
    return out


def main() -> int:  # pragma: no cover
    return nmk(sys.argv)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
