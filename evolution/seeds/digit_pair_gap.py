"""Seed: the gap between the high and low digit pairs.

Sorts the digits like Kaprekar's routine but combines them differently: the two
largest digits form one number, the two smallest another, and the map returns
their difference scaled back across the domain. A near neighbour of Kaprekar in
spirit, deliberately different in arithmetic.
"""

# EVOLVE-BLOCK-START


def transform(value: int) -> int:
    """Difference between the high digit pair and the low digit pair, spread out."""
    digits = sorted(f"{value:04d}")
    low = int(digits[0] + digits[1])
    high = int(digits[3] + digits[2])
    return (high - low) * 101 % 10000


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    current = 3524
    for _ in range(8):
        print(f"{current:04d}")
        current = transform(current)
