import sys


class StdioConsole:
    """Writes to stdout and stderr."""

    def write(self, text: str) -> None:
        print(text, file=sys.stdout)

    def write_error(self, text: str) -> None:
        print(text, file=sys.stderr)
