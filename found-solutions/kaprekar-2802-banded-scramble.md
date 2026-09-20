# Banded scramble → 2802

A total map on `0..9999` that funnels **every one of the 10000 four-digit numbers
into the single fixed point 2802**, taking 7.60 steps on average. It is a classic
Kaprekar step followed by a scramble whose form depends on which band the
difference lands in.

Its interest is that it reaches a *different* constant than Kaprekar's 6174 while
keeping the same 55-value image, and that it closes the one structural gap in the
real routine: the repdigit basin.

| | |
|---|---|
| Found | 2026-09-20, iteration 129, generation 4 |
| Program id | `8a8af2b5-e55b-4d8e-ba21-9b509326e8b3` |
| Parent | `13500a84-4550-49aa-a854-d8a3ff0aa95a` |
| Backend | `cerebras` (`gpt-oss-120b`), 200 iterations, 0 errors |
| Code | [`kaprekar-2802-banded-scramble.py`](kaprekar-2802-banded-scramble.py) |

## Scores

> **Scoring units changed after this was written.** The map was found under
> `ScoreWeights.depth_span = 5.0`, where `depth_score` saturated at mean depth 6 and
> this map scored a flat **1.000000**. `depth_span` is now **10.0**, under which it
> scores **0.659610** and the baseline scores **0.292728**. The table below gives both.
> Nothing about the map changed - only the yardstick.

| Factor | Kaprekar baseline (span 10) | This map (span 10) | This map (span 5, as found) |
|---|---|---|---|
| `combined_score` | 0.292728 | **0.659610** | 1.000000 |
| `dominance` | 0.998500 | 1.000000 | 1.000000 |
| `parsimony` | 0.800000 | 1.000000 | 1.000000 |
| `cycle_quality` | 1.000000 | 1.000000 | 1.000000 |
| `depth_score` | 0.366460 | 0.659610 | 1.000000 |
| attractors | 2 (`[6174]`, `[0000]`) | 1 (`[2802]`) | 1 (`[2802]`) |
| dominant basin | 99.90% | 100.00% | 100.00% |
| mean / max depth | 4.66 / 7 | 7.60 / 14 | 7.60 / 14 |
| distinct outputs | 55 (0.55%) | 55 (0.55%) | 55 (0.55%) |

## The code

```python
def transform(value: int) -> int:
    d = f"{value:04d}"
    # classic Kaprekar step
    diff = int("".join(sorted(d, reverse=True))) - int("".join(sorted(d)))

    if diff == 0:                      # repdigits: kill the second basin
        return 1

    s = f"{diff:04d}"

    if diff < 4000 and s != s[::-1]:   # reverse, +1
        rev = int(s[::-1])
        cand = (rev + 1) % 10000
        return cand if cand != diff else rev

    if 4000 <= diff < 7000:            # left-rotate, +2
        rot = int(s[1:] + s[0])
        cand = (rot + 2) % 10000
        return cand if cand != diff else rot

    if 7000 <= diff < 9000:            # right-rotate, +3
        rot = int(s[-1] + s[:-1])
        cand = (rot + 3) % 10000
        return cand if cand != diff else rot

    if diff >= 9000:                   # swap first and last, +4
        swapped = int(s[3] + s[1:3] + s[0])
        cand = (swapped + 4) % 10000
        return cand if cand != diff else swapped

    return diff
```

## How it works

**Step 1 — the Kaprekar difference.** Zero-pad to four digits, sort descending,
sort ascending, subtract. Unchanged from the seed program.

**Step 2 — redirect the repdigits.** In the real routine, `1111`, `2222`, … all
subtract to `0`, and `0` maps to itself. That is a **second attractor** holding 10
of the 10000 values, and it is exactly what costs Kaprekar's routine its parsimony
(0.8) and caps the baseline at 0.585. Sending that case to `1` instead folds those
ten values back into the main basin, taking `attractors` from 2 to 1.

**Step 3 — scramble by band.** The difference is re-read as a four-digit string and
perturbed differently depending on its magnitude:

| Band | Operation |
|---|---|
| `diff < 4000`, non-palindrome | reverse the digits, `+1` |
| `4000 ≤ diff < 7000` | left-rotate, `+2` |
| `7000 ≤ diff < 9000` | right-rotate, `+3` |
| `diff ≥ 9000` | swap first and last digit, `+4` |

All arithmetic is `% 10000`, which keeps the map total on the domain.

These operations are **digit permutations**, so they do not change which digits are
present — only their order. Since the next iteration immediately re-sorts those
digits, the scramble cannot change *where* a value eventually lands. What it
changes is how long the journey takes. That is its entire purpose: mean depth rises
from 4.66 to 7.60, clearing the threshold where `depth_score` saturates.

**The `cand != diff` guards.** Every branch checks that the perturbed value differs
from the input before returning it. Without that check a perturbation could map
some value onto itself, creating a stray fixed point — a new attractor, which would
immediately cost parsimony. The fallback (`return rot` / `return rev`) sidesteps it.

## Behaviour

```
9831 -> 2847 -> 2648 -> 1748 -> 3729 -> 3738 -> 3557 -> 6994 -> 2657 -> 0857 -> 2820 -> 2802
1111 -> 0001 -> 9991 -> 2802                     (the repdigit redirect in action)
3524 -> 7804 -> 2829 -> 3756 -> 0866 -> 2802
```

Steps required, over all 10000 seeds:

```
 0:    1     4:  750     8:  984    12:  654
 1:  183     5:  600     9:  936    13:  192
 2:  792     6:  426    10: 1304    14:  104
 3:  748     7:  832    11: 1494
```

Verified independently of the evaluator: `transform(2802) == 2802`, and all 10000
inputs return an `int` within `0..9999`.

## Honest assessment

The repdigit redirect is a genuine improvement on Kaprekar's routine — it removes a
real structural wart, and it would be worth keeping in any successor map.

The four-band scramble is opportunistic. The boundaries (4000 / 7000 / 9000) and the
`+1 / +2 / +3 / +4` constants show no sign of being principled; they look like values
that happened to work. Their function is to satisfy the scoring policy's depth term
rather than to express anything about four-digit arithmetic. Read this as a map
engineered for the metric, not a mathematical discovery.

It also scored a flat `1.000000`, which is the **ceiling** of the current
`ScoreWeights`. At the end of the run 38 of 200 programs were tied at 1.0 with mean
depths spanning 6.27–8.10, so the score could not rank this map above the others —
only confirm it is maximal. Raising `depth_span` would re-separate that group.

## Reproduce

```bash
uv run kaprekarevolve score found-solutions/kaprekar-2802-banded-scramble.py
```
