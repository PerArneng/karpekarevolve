import json
from pathlib import Path

from kaprekarevolve.interfaces.file_system import FileSystem
from kaprekarevolve.interfaces.novelty import MapFingerprint, NoveltyRegistry


class JsonRegistryLoader:
    """Loads the known-structure registry from a JSON file.

    Reads through the injected ``FileSystem`` rather than ``open``, so the edge stays
    the only place that touches a disk and a fake serves this class in tests.
    """

    def __init__(self, file_system: FileSystem) -> None:
        self._file_system = file_system

    def load(self, path: Path) -> NoveltyRegistry:
        if not self._file_system.exists(path):
            # No catalogue yet: nothing is known, so everything is novel.
            return NoveltyRegistry()
        entries = json.loads(self._file_system.read_text(path))
        return NoveltyRegistry(
            known_costs={
                MapFingerprint(
                    structure=tuple(tuple(pair) for pair in entry["structure"])
                ): int(entry["cost"])
                for entry in entries
            }
        )
