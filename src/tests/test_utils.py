from nmk.utils import create_dir_symlink
from tests.utils import NmkTester


class TestUtils(NmkTester):
    def test_symlink(self):
        # Create sample folder
        foo = self.test_folder / "foo"
        foo.mkdir()
        foo_file = foo / "sample.txt"
        foo_file.touch()

        # Create link and verify content
        bar = self.test_folder / "bar"
        create_dir_symlink(foo, bar)
        bar_file = bar / "sample.txt"
        assert bar_file.is_file()
