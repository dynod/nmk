"""
buildenv 2 environment backend abstraction (+ compatibility layer for buildenv 1)
"""

# We want to be compatible with both buildenv 1/2
# --> Abstract the environment backend
try:
    from buildenv.backends import EnvBackend, EnvBackendFactory
except ImportError:  # pragma: no cover
    from ._internal.envbackend_legacy import EnvBackend, EnvBackendFactory

__all__ = ["EnvBackend", "EnvBackendFactory"]
