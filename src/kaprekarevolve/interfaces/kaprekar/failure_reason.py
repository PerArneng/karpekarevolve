from enum import StrEnum


class FailureReason(StrEnum):
    """Why a candidate map was rejected before it could be scored."""

    RAISED = "raised"
    NOT_INTEGER = "not_integer"
    OUT_OF_RANGE = "out_of_range"
    NON_DETERMINISTIC = "non_deterministic"
    ITERATION_LIMIT = "iteration_limit"
    TIME_LIMIT = "time_limit"
    LOAD_ERROR = "load_error"
