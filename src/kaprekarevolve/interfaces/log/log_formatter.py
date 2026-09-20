from typing import Protocol

from kaprekarevolve.interfaces.log.log_record import LogRecord


class LogFormatter(Protocol):
    """Renders a record as a line of text. Pure."""

    def format(self, record: LogRecord) -> str:
        """Return the rendered line for ``record``."""
        ...
