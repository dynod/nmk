from pathlib import Path

from nmk.tests.tester import NmkBaseTester


class NmkTester(NmkBaseTester):
    @property
    def templates_root(self) -> Path:
        return Path(__file__).parent / "templates"
