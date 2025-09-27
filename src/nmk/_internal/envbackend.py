# We want to be compatible with both buildenv 1/2
# --> Abstract the environment backend
try:
    from buildenv2._backends.factory import EnvBackend, EnvBackendFactory
except ImportError:  # pragma: no cover
    from .envbackend_legacy import EnvBackend, EnvBackendFactory

__all__ = ["EnvBackend", "EnvBackendFactory"]
