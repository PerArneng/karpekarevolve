from typing import Protocol


class Logger(Protocol):
    """Emits log lines."""

    def debug(self, message: str) -> None:
        """Log at DEBUG."""
        ...

    def info(self, message: str) -> None:
        """Log at INFO."""
        ...

    def warning(self, message: str) -> None:
        """Log at WARNING."""
        ...

    def error(self, message: str) -> None:
        """Log at ERROR."""
        ...

    def critical(self, message: str) -> None:
        """Log at CRITICAL."""
        ...
