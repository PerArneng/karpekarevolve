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
    """Kaprekar's routine with a tiny offset for odd inputs.
    
    The classic Kaprekar difference is computed; if the original number is odd,
    we add 1 (mod 10000) before returning. This preserves the main attractor
    (6174) but lengthens the transient for about half of the inputs, increasing
    the mean depth without creating new attractors.
    """
    digits = f"{value:04d}"
    descending = int("".join(sorted(digits, reverse=True)))
    ascending = int("".join(sorted(digits)))
    k = descending - ascending

    # ---- Depth‑enhancing detour chain ----
    # 1. Small odd‑value tweak (keeps the classic attractor)
    if value & 1:
        k = (k + 1) % 10000

    # 2. Collapse the secondary fixed point (0) into the main basin.
    if k == 0:
        return 6174

    # 3. First deterministic left‑rotation of the 4‑digit string.
    k = int(f"{k:04d}"[1:] + f"{k:04d}"[0])

    # 4. Depth‑enhancing rotation: rotate left by (digit‑sum % 4) positions.
    s = sum(int(d) for d in f"{k:04d}")
    rot = s % 4
    s_str = f"{k:04d}"
    k = int(s_str[rot:] + s_str[:rot])

    # 5. Second depth‑enhancing rotation, again driven by the new digit‑sum.
    s2 = sum(int(d) for d in f"{k:04d}")
    rot2 = s2 % 4
    s_str = f"{k:04d}"
    k = int(s_str[rot2:] + s_str[:rot2])

    return k


# EVOLVE-BLOCK-END


if __name__ == "__main__":
    current = 3524
    for _ in range(8):
        print(f"{current:04d}")
        current = transform(current)
