__all__ = ["main", "__version__"]

from ._version import get_versions
from .gitgerrit import main

__version__ = get_versions()["version"]
del get_versions


__all__ = ["main", "__version__"]
