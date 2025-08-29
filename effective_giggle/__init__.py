"""Effective Giggle package root.

Provides helper utilities to discover and instantiate agents.
"""

from importlib import metadata as _metadata

__version__: str = _metadata.version("effective-giggle")
