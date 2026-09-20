class BuiltinKaprekarMap:
    """The classic Kaprekar routine: ``desc(n) - asc(n)`` on the zero-padded form.

    Every four-digit number reaches 6174 or 0 within seven steps.
    """

    def __call__(self, value: int) -> int:
        digits = f"{value:04d}"
        descending = int("".join(sorted(digits, reverse=True)))
        ascending = int("".join(sorted(digits)))
        return descending - ascending
