from pathlib import Path


class InMemoryFileSystem:
    """A filesystem backed by a dict."""

    def __init__(self, files: dict[Path, str] | None = None) -> None:
        self.files: dict[Path, str] = dict(files or {})

    def read_text(self, path: Path) -> str:
        if path not in self.files:
            raise FileNotFoundError(path)
        return self.files[path]

    def write_text(self, path: Path, content: str) -> None:
        self.files[path] = content

    def exists(self, path: Path) -> bool:
        return path in self.files
