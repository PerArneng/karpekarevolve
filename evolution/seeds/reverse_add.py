"""Seed: reverse-and-add, the Lychrel operation, kept inside the domain.

Adds a number to its digit reversal. Unlike Kaprekar's routine this preserves
no ordering information and grows rather than shrinks, so the modulus is what
keeps it total on 0..9999 - and is also what gives it its structure.
"""

# EVOLVE-BLOCK-START


def transform(value: int) -> int:
    """Add the number to its four-digit reversal, wrapped into the domain."""
    digits = f"{value:04d}"
    return (value + int(digits[::-1])) % 10000


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    current = 3524
    for _ in range(8):
        print(f"{current:04d}")
        current = transform(current)
