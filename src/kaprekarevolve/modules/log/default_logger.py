from kaprekarevolve.interfaces.clock import Clock
from kaprekarevolve.interfaces.console import Console
from kaprekarevolve.interfaces.log import LogFormatter, LogLevel, LogRecord


class DefaultLogger:
    """Builds records from the clock and hands formatted lines to the console."""

    def __init__(self, clock: Clock, formatter: LogFormatter, console: Console) -> None:
        self._clock = clock
        self._formatter = formatter
        self._console = console

    def debug(self, message: str) -> None:
        self._emit(LogLevel.DEBUG, message)

    def info(self, message: str) -> None:
        self._emit(LogLevel.INFO, message)

    def warning(self, message: str) -> None:
        self._emit(LogLevel.WARNING, message)

    def error(self, message: str) -> None:
        self._emit(LogLevel.ERROR, message)

    def critical(self, message: str) -> None:
        self._emit(LogLevel.CRITICAL, message)

    def _emit(self, level: LogLevel, message: str) -> None:
        record = LogRecord(level=level, message=message, timestamp=self._clock.now())
        self._console.write_error(self._formatter.format(record))
