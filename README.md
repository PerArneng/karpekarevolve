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
combined_score          0.585457

  dominance             0.998500
  parsimony             0.800000
  cycle_quality         1.000000
  depth_score           0.732920

attractors              2
dominant basin          99.9000% of 10000
dominant cycle          [6174]
mean / max depth        4.66 / 7
distinct outputs        55 (0.55%)
fixed points            2
```

## The scoring problem

"Does it converge?" is not a question worth asking: on a finite domain *every* total
map converges. What matters is the **shape** of the convergence, so the score is a
product of four factors, each in `0..1`:

| factor | rewards |
|---|---|
| `dominance` | the share of the 10000 numbers falling into the largest attractor, raised to 1.5 |
| `parsimony` | few distinct attractors |
| `cycle_quality` | a fixed point over a long terminal cycle |
| `depth_score` | **mean** steps needed to settle, saturating around 6 |

`depth_score` is what keeps the evaluator honest. Without it the search collapses
immediately onto degenerate winners:

| candidate | attractors | mean depth | score |
|---|---|---|---|
| `return 6174` | 1 | 1.0 | **0.000** |
| `return value` | 10000 | 0.0 | **0.000** |
| Kaprekar's routine | 2 | 4.66 | **0.585** |

Output diversity is deliberately *not* scored: the real Kaprekar map only ever emits 55
distinct values, so rewarding a wide image would punish the thing being imitated. It is
exported as a MAP-Elites feature instead.

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
  initial_program.py   seed program, inside EVOLVE-BLOCK markers
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
