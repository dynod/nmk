from pathlib import Path

from nmk.model.model import NmkModel
from nmk.model.resolver import NmkConfigResolver, NmkDictConfigResolver, NmkIntConfigResolver, NmkListConfigResolver, NmkStrConfigResolver


class StrResolver(NmkStrConfigResolver):
    def get_value(self, name: str) -> str:
        return "my dynamic value"


class LyingResolver(NmkIntConfigResolver):
    def get_value(self, name: str) -> str:
        return "my dynamic value"


class ThrowingResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        assert self.model is None, "Always failed!"

    def get_value(self, name: str) -> str:
        return "my dynamic value"


class NonVolatileResolver(NmkIntConfigResolver):
    def __init__(self, model: NmkModel):
        super().__init__(model)
        self.counter = 1

    def get_value(self, name: str) -> int:
        out = self.counter
        self.counter += 1
        return out


class VolatileResolver(NonVolatileResolver):
    def is_volatile(self, name: str) -> bool:
        return True


class GrabbingResolver(NmkDictConfigResolver):
    def get_value(self, name: str) -> dict:
        return {i: {k: self.model.config[k].value for k in ["someList", "someDict", "someVolatile", "someNonVolatile"]} for i in range(2)}


class SamplePathResolver(NmkConfigResolver):
    def get_type(self, name: str) -> object:
        return Path

    def get_value(self, name: str) -> Path:
        return Path("/tmp")


class SampleListResolver(NmkListConfigResolver):
    def get_value(self, name: str) -> list:
        return [1, 2]
