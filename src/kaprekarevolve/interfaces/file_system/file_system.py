from pathlib import Path
from typing import Protocol


class FileSystem(Protocol):
    """Reads and writes real files. An edge."""

    def read_text(self, path: Path) -> str:
        """Return the whole contents of ``path`` as text."""
        ...

    def write_text(self, path: Path, content: str) -> None:
        """Write ``content`` to ``path``, creating parent directories."""
        ...

    def exists(self, path: Path) -> bool:
        """Return whether ``path`` exists."""
        ...
