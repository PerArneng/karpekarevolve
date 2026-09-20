"""Seed program for evolution: the classic Kaprekar routine.

The contract, which the evaluator enforces:

* ``transform(value)`` takes an int in ``0..9999`` and returns an int in ``0..9999``.
* Think of the number as its zero-padded four-digit form: 49 is "0049".
* It must be pure and deterministic - no randomness, no globals, no IO.

The score rewards the *shape* of the convergence, not merely that it converges:
a single shallow-but-not-instant basin ending in a fixed point. Constant maps and
the identity score exactly zero.
"""

# EVOLVE-BLOCK-START


def transform(value: int) -> int:
    """Kaprekar variant with a reversible‑digit detour.
    * Classic Kaprekar step (desc‑asc).
    * Zero fixed point is sent to 1 to avoid an isolated basin.
    * For most intermediate results (diff < 5000) the digits are reversed,
      unless the number is already a palindrome (which would create a new fixed point).
    """
    d = f"{value:04d}"
    # classic Kaprekar step
    diff = int("".join(sorted(d, reverse=True))) - int("".join(sorted(d)))
    # redirect the isolated zero‑attractor
    if diff == 0:
        return 1
    s = f"{diff:04d}"
    # Add reversible perturbations to lengthen transient paths.
    # 1️⃣ Small differences: reverse digits and add 1 (mod 10000).
    if diff < 4000 and s != s[::-1]:
        rev = int(s[::-1])
        cand = (rev + 1) % 10000
        # avoid mapping back to the original diff
        return cand if cand != diff else rev
    # 2️⃣ Mid‑range: left‑rotate the digits, then add 2.
    if 4000 <= diff < 7000:
        rot = int(s[1:] + s[0])            # left‑rotate
        cand = (rot + 2) % 10000
        return cand if cand != diff else rot
    # 3️⃣ Upper‑mid range: right‑rotate the digits, then add 3.
    if 7000 <= diff < 9000:
        rot = int(s[-1] + s[:-1])          # right‑rotate
        cand = (rot + 3) % 10000
        return cand if cand != diff else rot
    # 4️⃣ Large values: swap first and last digits, then add 4.
    if diff >= 9000:
        swapped = int(s[3] + s[1:3] + s[0])
        cand = (swapped + 4) % 10000
        return cand if cand != diff else swapped
    # otherwise fall back to the plain Kaprekar difference
    return diff


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    current = 3524
    for _ in range(8):
        print(f"{current:04d}")
        current = transform(current)
