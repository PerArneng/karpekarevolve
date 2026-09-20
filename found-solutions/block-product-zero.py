"""Block product -> 0. Found by evolution, 200 iterations on cerebras, iteration 104.

Split the four digits into two two-digit blocks and multiply them. The largest
possible product is 99 x 99 = 9801, so the map is total on 0..9999 by construction -
it needs no modulus and no clamping, which is most of why it is so short.
"""

# EVOLVE-BLOCK-START


def transform(value: int) -> int:
    """Product of the high-order and low-order two-digit blocks."""
    return (value // 100) * (value % 100)


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    current = 3524
    for _ in range(8):
        print(f"{current:04d}")
        current = transform(current)
