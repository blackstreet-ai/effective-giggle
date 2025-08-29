"""Agents package.

Utility for dynamic discovery of available agent factories.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import ModuleType
from typing import Callable, Dict

__all__: list[str] = [
    "list_agents",
    "get_agent_factory",
]

_FACTORY_CACHE: Dict[str, Callable] = {}


def _discover() -> None:
    """Populate global factory cache by importing submodules that define `create()`."""

    global _FACTORY_CACHE

    for mod_info in pkgutil.walk_packages(__path__, prefix=f"{__name__}."):
        if not mod_info.ispkg:
            continue
        try:
            module: ModuleType = importlib.import_module(mod_info.name + ".agent")
        except ModuleNotFoundError:
            continue
        if hasattr(module, "create"):
            _FACTORY_CACHE[mod_info.name.split(".")[-1]] = module.create  # type: ignore


_discover()


def list_agents() -> list[str]:
    """Return names of all discoverable agents."""

    return sorted(_FACTORY_CACHE.keys())


def get_agent_factory(name: str) -> Callable:
    """Return factory function for *name* agent."""

    return _FACTORY_CACHE[name]
