# Block product → 0

```python
def transform(value: int) -> int:
    return (value // 100) * (value % 100)
```

Split the four digits into two two-digit blocks and multiply them.

| | this map | Kaprekar |
|---|---|---|
| `combined_score` | **0.616036** | 0.019311 |
| dominant basin | **100.0000%** | 99.90% |
| attractors | **1** | 2 |
| mean / max depth | 4.67 / 12 | 4.66 / 7 |
| AST cost | **29** | 48 |
| novelty | 1.000 | 0.049 (catalogued) |
| distinct outputs | 2870 (28.70%) | 55 (0.55%) |

`3524 → 0840 → 0320 → 0060 → 0000`, four steps.

Found by evolution at iteration 104 of a 200-iteration cerebras run (`gpt-oss-120b`),
seeded from `composed_permutation`, `depth_peak 5.0 / depth_width 3.0 /
elegance_reference 48.0`.

## Why it is short

It needs no modulus and no clamping. The largest possible product is 99 × 99 = 9801, so
the map is total on 0..9999 *by construction*. That is most of the 29 against Kaprekar's
48, and it is the kind of thing the elegance factor was added to notice.

Its transient structure is also strikingly close to Kaprekar's — mean depth 4.67 against
4.66 — while reaching its attractor from **every** starting value rather than 9990 of
them, and spreading over 2870 distinct outputs rather than 55.

## The honest caveat

**The constant is 0, which is the trivial fixed point.** Kaprekar's 6174 is interesting
precisely because it is not an obvious number; "everything collapses to zero" is a much
less striking destination, and a multiplicative map reaching it is not a surprise once
stated — any block containing a 0 digit sends the product to 0 immediately.

So this is a real structural find with Kaprekar-like *dynamics* and a genuinely tidy
formula, but it is not a new Kaprekar *constant*. Treat the score as measuring what it
measures: basin, depth shape, brevity and structural novelty. It does not measure
"is this destination interesting", and this map is the clearest illustration so far that
those are different questions.

127 of the 159 distinct valid programs in the final population converged on the zero
attractor, 8 kept the seed's 4950, and the rest found small cycles. The run collapsed
onto one family, which is the same anchoring behaviour every previous run showed — this
time on a different family.

## The scoring exploit this run exposed

30 of 201 programs (15%) scored themselves as high as 0.9882 by writing

```python
transform = lambda v: ...
```

instead of `def transform(...)`. `AstShapeAnalyzer` looked only for a `FunctionDef`,
raised when it found none, and the raise was caught upstream as "this map has no source"
— the neutral meant for the built-in baseline, which really has none. That handed the
candidate `elegance = 1.0`: a perfect score on the one factor it was dodging.

Fixed: every binding form is measured, and anything unrecognised falls back to measuring
the whole module. `tests/unit/test_ast_shape_analyzer.py` pins it. The map above is
unaffected — re-scored honestly it still leads, at 0.616036 rather than 0.9882.
