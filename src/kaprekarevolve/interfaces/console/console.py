from typing import Protocol


class Console(Protocol):
    """Writes text to the terminal. An edge."""

    def write(self, text: str) -> None:
        """Write a line to standard output."""
        ...

    def write_error(self, text: str) -> None:
        """Write a line to standard error."""
        ...
