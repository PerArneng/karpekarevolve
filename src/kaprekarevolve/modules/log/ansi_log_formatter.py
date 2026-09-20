from kaprekarevolve.interfaces.log import LogLevel, LogRecord

_RESET = "\x1b[0m"
_COLORS: dict[LogLevel, str] = {
    LogLevel.DEBUG: "\x1b[36m",
    LogLevel.INFO: "\x1b[32m",
    LogLevel.WARNING: "\x1b[33m",
    LogLevel.ERROR: "\x1b[31m",
    LogLevel.CRITICAL: "\x1b[1;31m",
}


class AnsiLogFormatter:
    """Renders ``<timestamp> <level> <message>``, colouring only the level token."""

    def __init__(self, use_color: bool) -> None:
        self._use_color = use_color

    def format(self, record: LogRecord) -> str:
        timestamp = record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        level = record.level.value
        if self._use_color:
            level = f"{_COLORS[record.level]}{level}{_RESET}"
        return f"{timestamp} {level} {record.message}"
