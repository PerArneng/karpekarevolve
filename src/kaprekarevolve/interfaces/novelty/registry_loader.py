from pathlib import Path
from typing import Protocol

from kaprekarevolve.interfaces.novelty.novelty_registry import NoveltyRegistry


class RegistryLoader(Protocol):
    """Reads the registry of already-known maps."""

    def load(self, path: Path) -> NoveltyRegistry:
        """Return the registry stored at ``path``, or an empty one if absent."""
        ...
