# kaprekarevolve

Kaprekar's routine — sort the digits of a four-digit number descending, subtract the
ascending arrangement, repeat — drives 9990 of the 10000 starting numbers to the fixed
point **6174** in at most seven steps.

This project asks whether there are *other* maps like it, and uses
[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) to look for them.
An LLM evolves candidate functions `transform: 0000..9999 -> 0000..9999`; an exact
evaluator scores each one on how cleanly the whole domain collapses onto a small,
stable attractor.

```
$ uv run kaprekarevolve baseline
Kaprekar routine (baseline)
===========================
combined_score          0.019311

  dominance             0.998500
  attractor_focus       0.800000
  cycle_quality         1.000000
  depth_score           0.987577
  elegance              0.500000   (AST cost 48)
  novelty               0.048958   (already known: a relabelling)

attractors              2
dominant basin          99.9000% of 10000
dominant cycle          [6174]
mean / max depth        4.66 / 7
distinct outputs        55 (0.55%)
fixed points            2
```

## The scoring problem

"Does it converge?" is not a question worth asking: on a finite domain *every* total
map converges. What matters is the **shape** of the convergence — and, since the point
is to find maps a person would want to read, the shape of the code as well. The score is
a product of six factors, each in `0..1`:

| factor | rewards |
|---|---|
| `dominance` | the share of the 10000 numbers falling into the largest attractor, raised to 1.5 |
| `attractor_focus` | few distinct attractors (this was called `parsimony`, which now means code) |
| `cycle_quality` | a fixed point over a long terminal cycle |
| `depth_score` | a **band** on mean steps to settle: peaks at 5, falls away on *both* sides |
| `elegance` | a small syntax tree for `transform`; branches, magic constants and table literals cost extra |
| `novelty` | a structure not already in the catalogue, discounted by how much code it took |

`depth_score` is what keeps the evaluator honest. Without it the search collapses
immediately onto degenerate winners:

| candidate | attractors | mean depth | score |
|---|---|---|---|
| `return 6174` | 1 | 1.0 | **0.000** |
| `return value` | 10000 | 0.0 | **0.000** |
| Kaprekar's routine | 2 | 4.66 | **0.019** |

Because the factors multiply, one weak factor decides the score. That is deliberate: a
map that converges beautifully in thirty lines of special cases is not the thing being
looked for.

Two of these terms exist because of what the earlier score did. `depth_score` used to be
a *ramp* that paid for depth up to a cap, and the search answered exactly as asked — it
bolted rotation chains onto the Kaprekar difference purely to lengthen paths. Making it a
band centred on Kaprekar's own mean depth of 4.66 turns that tactic from a reward into a
cost. And nothing measured novelty at all, so a known map wearing different values read
as a discovery; see **The catalogue** below.

Output diversity is deliberately *not* scored: the real Kaprekar map only ever emits 55
distinct values, so rewarding a wide image would punish the thing being imitated. It is
exported as a MAP-Elites feature instead.

## The catalogue

`(a*P(v) + b*Q(v) + c) % 10000`, where `P` and `Q` are digit permutations, is a family a
for-loop can exhaust. `uv run kaprekarevolve catalogue` enumerates all 2400 of them in
about 20 seconds and finds they reach only **7 distinct structures**, which it records in
`found-solutions/registry.json`.

"Structure" here is the map's in-degree profile — how many values reach each output —
with the degrees and their multiplicities each divided by their own gcd. That is coarser
than graph isomorphism on purpose, because it sees through the two ways a known map gets
dressed up as a new one:

- **post-composition**, `perm(kaprekar(v))`, which cannot change how many inputs reach
  each output and so leaves the profile untouched;
- **k-fold covering**, as a parity tweak like `if value & 1: k += 1` produces, which
  halves every degree and doubles every multiplicity.

Both maps recorded in `found-solutions/` land in Kaprekar's own class under this test.
That is the honest reading of them, and nothing in the pipeline could say so before.

A candidate matching a catalogued structure is scored as prior art rather than banned
outright: `novelty` is discounted by how much longer its code is than the cheapest route
already known. Finding a *shorter* way to a known map is a real result; bolting rotations
onto one is not.

A candidate is rejected outright (score 0, with the reason fed back to the LLM through
OpenEvolve's artifact side-channel) if it returns a non-int or a value outside
`0..9999`, raises, answers differently on a repeat call, or needs more than 1000
iterations to settle.

The analysis is **exact, not sampled**. The domain under a total map is a functional
graph, so labelling each value once — memoised across all 10000 seeds — is O(domain)
rather than O(domain × iterations), and the whole thing runs in milliseconds.

## Commands

```bash
uv run kaprekarevolve baseline              # analyse and score Kaprekar's routine
uv run kaprekarevolve trace 9831            # walk one number to its attractor
uv run kaprekarevolve score <program.py>    # score a candidate
uv run kaprekarevolve evolve -n 200         # search for new maps
uv run kaprekarevolve evolve -b cerebras    # ... on a different LLM backend
uv run kaprekarevolve evolve -s reverse_add # ... from a different seed program
uv run kaprekarevolve best                  # re-score the winner of the last run
```

### LLM backends

`evolve` picks its LLM from a per-backend config file, chosen with `--backend`/`-b`:

| Backend | Config | What it needs |
|---|---|---|
| `brain-tailscale` (default) | `evolution/config.brain-tailscale.yaml` | a self-hosted `qwen3.6-35b` on your own network. Its router dispatches on `Host`, which OpenEvolve cannot set, so copy `.env.example` to `.env`, fill in your endpoint, and start `python3 scripts/vllm_host_proxy.py &` first. |
| `cerebras` | `evolution/config.cerebras.yaml` | hosted Cerebras (`gpt-oss-120b`, `qwen-3.8-27b`). Needs `CEREBRAS_API_KEY` in the environment or `.env`; the key is read from there and never stored in the repo. |

Adding a backend means dropping `evolution/config.<name>.yaml` next to the others — the
name on the command line *is* the filename, so no code change is needed.

### Seed programs

`--seed`/`-s` picks the starting program from `evolution/seeds/`, the same way:

| Seed | Score | Attractors | Mean depth | Weakness it starts with |
|---|---|---|---|---|
| `kaprekar` (default) | 0.019311 | 2 | 4.66 | the repdigit basin, and its structure is catalogued |
| `digit_pair_gap` | 0.008661 | 1 | 2.97 | settles too quickly, and shares Kaprekar's structure |
| `digit_power_sum` | 0.033251 | 10 | 6.04 | scattered across many attractors, but genuinely novel |
| `reverse_add` | 0.000000 | 3 | 19.97 | far past the depth band; limited by its 3 basins |
| `composed_permutation` | 0.251928 | 2 | 3.37 | none — the only seed outside the catalogued family |

Seeding matters more than it looks. In a 200-iteration run from `kaprekar`, **all 201
programs in the final population still contained the descending-minus-ascending step** —
the search decorated the seed rather than leaving it. Starting elsewhere is how you find
out whether other families can do as well.

Note that OpenEvolve cannot take several seeds at once: passing a list to
`run_evolution` concatenates them into a single file. One family per run, then compare.

The two files share everything but their `llm:` block. That duplication is deliberate
(OpenEvolve has no config includes) but it does mean a prompt or database change must be
applied to **both**, or the backends quietly stop being comparable.

## Layout

Interface-first: `typing.Protocol`s and frozen Pydantic models in `interfaces/`,
implementations mirroring them in `modules/`, one public class per file, every
dependency constructor-injected, IO confined to the edges (clock, console, filesystem,
program loading, the evolution runner). The whole application runs in memory against
fakes, which is why the test suite needs no temporary files and no clock.

```
src/kaprekarevolve/
  interfaces/   clock console log file_system program kaprekar scoring report evolution engine
  modules/      the implementations, same domain names
  container.py  dependency-injector wiring
  cli/main.py   Typer frontend
evolution/
  seeds/<name>.py      seed programs, inside EVOLVE-BLOCK markers
  evaluator.py         OpenEvolve adapter -> the same Engine the CLI calls
  config.<backend>.yaml  one OpenEvolve config per LLM backend
scripts/
  vllm_host_proxy.py   adds the Host header a vhost-dispatching router needs
.env.example           endpoint + key template; copy to .env (gitignored)
```

`evolution/evaluator.py` is a frontend adapter exactly like the CLI: it parses a path
and calls the facade. The score the evolution loop optimises and the score
`kaprekarevolve score` prints therefore cannot drift apart.

## Development

```bash
uv sync
uv run pytest
uv run mypy src tests evolution
uv run ruff check src tests evolution
```
