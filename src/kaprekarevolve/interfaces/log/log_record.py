from datetime import datetime

from pydantic import BaseModel, ConfigDict

from kaprekarevolve.interfaces.log.log_level import LogLevel


class LogRecord(BaseModel):
    """One line of log, before formatting."""

    model_config = ConfigDict(frozen=True)

    level: LogLevel
    message: str
    timestamp: datetime
