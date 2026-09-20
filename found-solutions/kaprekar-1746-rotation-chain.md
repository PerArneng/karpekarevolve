# Rotation chain → 1746

A total map on `0..9999` that sends **all 10000 four-digit numbers to the fixed point
1746**, averaging 8.72 steps. A Kaprekar difference feeds a chain of digit rotations
whose amounts are driven by the running digit sum.

Two things set it apart from the earlier finds. It reaches a **third distinct
constant** (after 6174 and 2802), and it is the first winner to break out of
Kaprekar's image: **110 distinct outputs rather than the usual 55**.

| | |
|---|---|
| Found | 2026-09-20, iteration 130, generation 4 |
| Program id | `8b611246-7ece-4216-a383-8ffa848a79c0` |
| Parent | `9b190a32-27dc-4535-950c-a5bdf0d95185` |
| Backend | `cerebras` (`gpt-oss-120b`), 200 iterations, 2 malformed diffs |
| Weights | `ScoreWeights.depth_span = 10.0` |
| Code | [`kaprekar-1746-rotation-chain.py`](kaprekar-1746-rotation-chain.py) |

## Scores

| Factor | Kaprekar baseline | This map |
|---|---|---|
| `combined_score` | 0.292728 | **0.772280** |
| `dominance` | 0.998500 | 1.000000 |
| `parsimony` | 0.800000 | 1.000000 |
| `cycle_quality` | 1.000000 | 1.000000 |
| `depth_score` | 0.366460 | 0.772280 |
| attractors | 2 (`[6174]`, `[0000]`) | 1 (`[1746]`) |
| dominant basin | 99.90% | 100.00% |
| mean / max depth | 4.66 / 7 | 8.72 / 16 |
| distinct outputs | 55 (0.55%) | **110 (1.10%)** |

Unlike the earlier `found-solutions` entry, this score is **not** at a ceiling:
`depth_score` still has 0.23 of headroom, so the map is recorded as good rather than
maximal.

## The code

```python
def transform(value: int) -> int:
    digits = f"{value:04d}"
    descending = int("".join(sorted(digits, reverse=True)))
    ascending = int("".join(sorted(digits)))
    k = descending - ascending

    # 1. Small odd-value tweak (keeps the classic attractor)
    if value & 1:
        k = (k + 1) % 10000

    # 2. Collapse the secondary fixed point (0) into the main basin.
    if k == 0:
        return 6174

    # 3. First deterministic left-rotation of the 4-digit string.
    k = int(f"{k:04d}"[1:] + f"{k:04d}"[0])

    # 4. Rotate left by (digit-sum % 4) positions.
    s = sum(int(d) for d in f"{k:04d}")
    rot = s % 4
    s_str = f"{k:04d}"
    k = int(s_str[rot:] + s_str[:rot])

    # 5. Second rotation, driven by the new digit-sum.
    s2 = sum(int(d) for d in f"{k:04d}")
    rot2 = s2 % 4
    s_str = f"{k:04d}"
    k = int(s_str[rot2:] + s_str[:rot2])

    return k
```

## How it works

**Step 1 - the Kaprekar difference,** unchanged from the seed.

**Step 2 - the parity tweak.** If the *original* input was odd, add 1 to the
difference. This is the one step that breaks the map out of Kaprekar's orbit: the
classical routine only ever emits the 55 values reachable as a sorted-digit
difference, and the `+1` on odd inputs doubles that image to 110. It is also why the
attractor moves off 6174.

**Step 3 - the repdigit fix.** When all four digits are equal the difference is 0,
which in the classical routine is a second fixed point holding 10 of the 10000
values. Sending it into the basin takes `attractors` from 2 to 1 and `parsimony` from
0.8 to 1.0 - the same insight every successful run here has rediscovered.

**Steps 4-6 - the rotation chain.** Three left-rotations of the four-digit string:
one fixed, then two by `digit_sum % 4`. Rotations are digit permutations, so they
cannot change which digits are present - only their order, which the next iteration's
sort discards. Their sole effect is to lengthen the transient, taking mean depth from
4.66 to 8.72.

## Behaviour

```
9831 -> 3844 -> 5499 -> 6535 -> 9982 -> 0837 -> 3835 -> 6517 -> 5608 -> 0828 -> 5328 -> 1746
1111 -> 1000 -> 9099 -> 9928 -> 0837 -> 3835 -> 6517 -> 5608 -> 0828 -> 5328 -> 1746
3524 -> 0873 -> 3835 -> 6517 -> 5608 -> 0828 -> 5328 -> 1746
```

Steps required, over all 10000 seeds:

```
 0:    1     5:  372    10: 1277    15:   27
 1:  191     6:  368    11: 1056    16:   15
 2:  293     7: 1136    12: 1318
 3:  480     8:  784    13:  576
 4:  708     9:  804    14:  594
```

Verified independently of the evaluator: `transform(1746) == 1746`, and all 10000
inputs return an `int` within `0..9999`.

## Honest assessment

The parity tweak is the interesting part. It is one token of code, and it is what
moves the map off Kaprekar's 55-value image and onto a new constant - the first time
any run here has escaped that orbit.

The rotation chain is not interesting. Three rotations keyed on digit sums, stacked
because each one adds transient length; nothing about the choice of `% 4` or the
number of stages reflects anything about four-digit arithmetic. It exists to satisfy
`depth_score`.

One wart: step 2 returns the literal `6174` when the difference is zero, hardcoding
the *classical* constant into a map whose own attractor is 1746. It is harmless -
6174 flows into the 1746 basin like everything else - but it is a leftover from the
lineage rather than a considered choice.

This map was found under `depth_span = 10.0`. Scores recorded here are not comparable
with the earlier entry in this directory, which was found under `depth_span = 5.0`.

## Reproduce

```bash
uv run kaprekarevolve score found-solutions/kaprekar-1746-rotation-chain.py
```

## Re-measured under the rebuilt score (six factors)

`combined_score` **0.000253**, down from the number above. The earlier rows are kept
deliberately: scores measured under different weights are not comparable, and this one
was found under an objective that has since been rebuilt.

It falls because its structure is Kaprekar's own (a 2-fold cover, via the parity tweak) and its AST cost is 245. Both are penalties the earlier objective had no way to express —
it measured only the shape of the convergence, so a map that reached a known place by a
longer road looked like a discovery. See **The catalogue** in README.md.
