from typing import Any, cast

from kaprekarevolve.interfaces.program import DigitMap, ProgramLoadError

_ENTRY_POINT = "transform"


class ExecProgramLoader:
    """Executes candidate source and hands back its ``transform`` function.

    The one place in the codebase allowed to run code it did not write.
    """

    def load(self, source: str) -> DigitMap:
        namespace: dict[str, Any] = {}
        try:
            compiled = compile(source, "<candidate>", "exec")
            exec(compiled, namespace)  # noqa: S102 - evolving arbitrary code is the point
        except Exception as error:  # noqa: BLE001 - any failure is the candidate's fault
            raise ProgramLoadError(
                f"candidate failed to import: {type(error).__name__}: {error}"
            ) from error
        candidate = namespace.get(_ENTRY_POINT)
        if candidate is None:
            raise ProgramLoadError(f"candidate defines no {_ENTRY_POINT}() function")
        if not callable(candidate):
            raise ProgramLoadError(f"{_ENTRY_POINT} is not callable")
        return cast(DigitMap, candidate)
