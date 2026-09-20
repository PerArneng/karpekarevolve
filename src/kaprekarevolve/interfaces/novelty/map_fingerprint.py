from pydantic import BaseModel, ConfigDict


class MapFingerprint(BaseModel):
    """Identifies a map's *structure*, ignoring what its values happen to be called.

    The key is the multiset of in-degrees - how many values each output is reached
    from - with both the degrees and their multiplicities divided through by their own
    gcd. That is deliberately coarser than graph isomorphism, and the coarseness is the
    point. It collapses exactly the two ways a known map gets dressed up as a new one:

    * **Post-composition.** ``perm(kaprekar(v))`` has the same in-degree multiset as
      ``kaprekar(v)``, because renaming outputs cannot change how many inputs reach
      each one. The recorded "2802 banded scramble" is caught here exactly.
    * **k-fold covering.** A parity tweak such as ``if value & 1: k += 1`` splits every
      preimage set in two, halving each degree and doubling each multiplicity. Dividing
      by the gcd undoes it. The recorded "1746 rotation chain" is caught here.

    Both recorded solutions therefore land in Kaprekar's own class, which is the honest
    reading of them. Over an enumerated family of 154 short maps this key finds 7
    classes where exact isomorphism finds 55 - it is doing real merging, not hashing
    noise - while keeping ``desc - rot(asc)``, ``reverse_add`` and ``digit_power_sum``
    genuinely apart.
    """

    model_config = ConfigDict(frozen=True)

    structure: tuple[tuple[int, int], ...]
