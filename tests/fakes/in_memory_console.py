class InMemoryConsole:
    """Collects what would have been printed."""

    def __init__(self) -> None:
        self.output: list[str] = []
        self.errors: list[str] = []

    def write(self, text: str) -> None:
        self.output.append(text)

    def write_error(self, text: str) -> None:
        self.errors.append(text)

    @property
    def text(self) -> str:
        return "\n".join(self.output)
