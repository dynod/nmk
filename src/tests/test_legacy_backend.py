import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest
from pytest_multilog import TestHelper

from nmk._internal.envbackend_legacy import EnvBackend, EnvBackendFactory


class TestLegacyBackend(TestHelper):
    @pytest.fixture
    def backend(self, logs: None) -> EnvBackend:
        return EnvBackendFactory().create("foo", self.test_folder)

    def test_version(self, backend: EnvBackend):
        assert backend.version == 1

    def test_backend_name(self, backend: EnvBackend):
        assert backend.name == "legacy"

    def test_is_mutable(self, backend: EnvBackend):
        assert backend.is_mutable() is True

    def test_venv_name(self, backend: EnvBackend):
        assert backend.venv_name == "venv"

    def test_project_path(self, backend: EnvBackend):
        assert backend.project_path == self.test_folder

    def test_venv_root(self, backend: EnvBackend):
        assert backend.venv_root == Path(sys.executable).parent.parent

    def test_use_requirements(self, backend: EnvBackend):
        assert backend.use_requirements is True

    def test_print_updates(self, backend: EnvBackend):
        # Simple run for coverage
        backend.print_updates({})

    def test_dump(self, backend: EnvBackend):
        # Simple run for coverage
        dump_file = self.test_folder / "backend_dump.txt"
        backend.dump(dump_file)
        assert dump_file.is_file()

    def test_upgrade(self, backend: EnvBackend, monkeypatch: pytest.MonkeyPatch):
        called_args: list[str] = []

        def fake_subprocess(args: list[str], *extra_args: list[Any], **kwargs: dict[str, Any]):
            called_args.extend(args)
            return subprocess.CompletedProcess[str](args, 0, "", "")

        monkeypatch.setattr(subprocess, "run", fake_subprocess)

        ret_code = backend.upgrade(full=True)
        assert ret_code == 0
        assert called_args[-4:] == ["-r", "requirements.txt", "--upgrade", "--require-virtualenv"]
