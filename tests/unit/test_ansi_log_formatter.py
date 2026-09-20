from datetime import datetime

from kaprekarevolve.interfaces.log import LogLevel, LogRecord
from kaprekarevolve.modules.log import AnsiLogFormatter

RECORD = LogRecord(
    level=LogLevel.WARNING, message="slow map", timestamp=datetime(2026, 9, 20, 8, 5, 3)
)


def test_only_the_level_token_is_coloured() -> None:
    line = AnsiLogFormatter(use_color=True).format(RECORD)

    assert line == "2026-09-20 08:05:03 \x1b[33mWARNING\x1b[0m slow map"


def test_colour_can_be_switched_off() -> None:
    line = AnsiLogFormatter(use_color=False).format(RECORD)

    assert line == "2026-09-20 08:05:03 WARNING slow map"
