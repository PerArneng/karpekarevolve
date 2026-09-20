# kaprekarevolve

Kaprekar's routine — sort a four-digit number's digits descending, subtract the
ascending arrangement, repeat — drives 9990 of the 10000 starting numbers to the fixed
point 6174 in at most seven steps. This repo uses
[OpenEvolve](https://github.com/algorithmicsuperintelligence/openevolve) to hunt for
*other* maps that behave like it: an LLM evolves candidate `transform(value)` functions
and an exact evaluator scores how cleanly the whole domain collapses onto a small,
stable attractor.

Two things carry most of the project's weight — **the scoring policy** and **the
interface-first structure**. Both are described below, because changing either one
carelessly breaks things that are not obviously connected.

## Commands

```bash
uv sync
uv run kaprekarevolve baseline            # score the built-in Kaprekar routine
uv run kaprekarevolve trace 9831          # walk one number to its attractor
uv run kaprekarevolve score <program.py>  # score a candidate file
uv run kaprekarevolve evolve -n 200       # run OpenEvolve (spends LLM budget)
uv run kaprekarevolve evolve -b cerebras  # ... on a named LLM backend
uv run kaprekarevolve evolve -s reverse_add  # ... from a named seed program
uv run kaprekarevolve catalogue           # enumerate what brute force already reaches
uv run kaprekarevolve best                # re-score the last run's winner

uv run pytest
uv run mypy src tests evolution           # strict; must stay clean
uv run ruff check src tests evolution
```

## Backends and seeds

Two things are chosen per run, each by name, each resolving to a file — so adding
either is a new file, never a code change.

`--backend NAME` → `evolution/config.<name>.yaml`:

- **`brain-tailscale`** (the default) — a self-hosted `qwen3.6-35b`. Its router
  dispatches on `Host`, which OpenEvolve cannot set because it builds its OpenAI
  client from a bare `api_base` string, so **`python3 scripts/vllm_host_proxy.py &`
  must be running first**. Endpoints come from `.env` (see `.env.example`); no private
  hostname is committed.
- **`cerebras`** — hosted `gpt-oss-120b`, needs `CEREBRAS_API_KEY` in `.env`. Its other
  model, `qwen-3.8-27b`, is deliberately excluded: it spends its whole budget on
  reasoning tokens and returns empty content (verified to 64000 `max_tokens`), and
  Cerebras rejects `chat_template_kwargs` so thinking cannot be disabled. OpenEvolve
  reports this as `LLM returned None response`. Don't re-add it.

`--seed NAME` → `evolution/seeds/<name>.py`. `kaprekar` is the default; `reverse_add`,
`digit_power_sum` and `digit_pair_gap` start from other families. OpenEvolve cannot
take several at once — passing a list to `run_evolution` concatenates them into one
file — so it is one family per run.

A run spends real budget (money on Cerebras, hours on brain at ~35s/iteration); don't
launch one without the user asking.

Maps worth keeping go in `found-solutions/<name>.md` with the program beside it, since
`openevolve_output/` is gitignored and overwritten by the next run. Record which
`depth_peak`, `depth_width` and `elegance_reference` a score was measured under — scores
across different weights are not comparable.

## The scoring contract

Every total map on a finite domain converges, so "does it converge?" measures nothing.
The evaluator grades the *shape* of the convergence, and of the code that produced it —
a product of six factors, each in 0..1, in `modules/scoring/weighted_scoring_policy.py`:

```
combined_score = dominance^1.5 · attractor_focus · cycle_quality
                 · depth_score · elegance · novelty
```

`depth_score` is a **band**, not a ramp: it peaks at mean depth 5 (Kaprekar's own is
4.66), falls away on both sides, and is damped again by a `max_depth` over 12. It used
to be a ramp saturating at a cap, which paid for depth without limit — and the search
answered exactly as asked, bolting rotation chains onto the Kaprekar difference purely
to lengthen paths. **If you make it a ramp again you will get that behaviour back.**

It is still the anti-triviality term, and the low end is guarded by a smooth onset gate
(`depth_onset`, `depth_onset_width`) rather than a cutoff. A bare Gaussian hands a map
that settles in 1.05 steps a score of 0.18; the gate takes that to 0.0004. `return 6174`
and `return value` both score exactly 0.0.

`elegance` measures the AST of `transform` (docstring stripped): a branch costs 6 nodes,
an unexplained integer constant 8, and each element of a list/dict literal 8. It is
strictly decreasing with **no flat top** — a factor that saturates stops ranking whatever
reaches it, which is how 22% of all evaluations once tied at exactly 1.0000.

`novelty` compares the map's gcd-normalised in-degree profile against
`found-solutions/registry.json` and discounts prior art by how much longer the code is
than the cheapest known route to the same structure. See **The catalogue** in README.md.

Output diversity is deliberately **not** scored: the real Kaprekar map emits only 55
distinct values out of 10000, so rewarding a wide image would punish the thing being
imitated. `image_ratio` is exported as a MAP-Elites feature instead.

**The baseline scores `0.019311`** through the CLI, which loads the committed registry
and so scores Kaprekar as the prior art it is. Pinned in:

- `tests/integration/test_cli.py` — `0.019311`, the full CLI path with the real registry;
- `tests/integration/test_engine.py` — `0.394438`, the same map with an **empty**
  registry, which is what the in-memory harness injects;
- `tests/unit/test_weighted_scoring_policy.py` — `0.788877`, shape only, no source and
  no registry.

Three different numbers for the same map, because they differ in what is injected. That
is the point of the harnesses, but it means changing `ScoreWeights` moves all three.
`README.md` carries the CLI number in two places.

`baseline` is scored from `BaselineProgram.source`, not from `BuiltinKaprekarMap`, so
that `kaprekarevolve baseline` and `kaprekarevolve score evolution/seeds/kaprekar.py`
report the same number. Score the object instead and the two drift the moment the score
reads source, which it now does.

Analysis is exact rather than sampled: the domain under a total map is a functional
graph, so `MemoizedMapAnalyzer` labels each value once across all 10000 seeds — O(domain),
milliseconds per candidate. Don't replace it with sampling to "speed it up".

## Architecture

Interface-first, and the constraints are what make the whole application testable in
memory with no filesystem, clock, terminal or network:

- `interfaces/<domain>/` holds **only** `typing.Protocol`s and frozen Pydantic models.
  Nothing there imports from `modules/`, `cli/` or `evolution/`. Keeping that direction
  one-way is what keeps `interfaces/` cheap and side-effect free.
- `modules/<domain>/` mirrors it with implementations. One public class per file, the
  filename being the class name in snake_case.
- Interfaces are plain nouns (`Clock`, `FileSystem`); implementations carry a
  qualifying prefix (`SystemClock`, `LocalFileSystem`, `InMemoryConsole`).
- Every dependency arrives through `__init__`. No globals, no singletons, no class
  constructing its own collaborators.
- **IO lives only in edge modules**: `clock`, `console`, `file_system`, `program`
  (it `exec`s candidate code), `evolution` (it calls the LLM). No `print()`, `open()`,
  `datetime.now()`, `os.environ` or network calls anywhere else — the clock especially,
  since `datetime.now()` buried in a pure class makes its output untestable.
- `container.py` is the composition root. Only `cli/main.py` and `evolution/evaluator.py`
  may instantiate `Container()`.
- `Engine` is the facade. New capabilities become an `Engine` method first; frontends
  only learn how to invoke them.

Adding a feature means: Protocol → frozen model(s) → implementation → re-export from
both `__init__.py` files → register in `container.py` → expose on `Engine` → thin
frontend command → unit test the pure class + an engine integration test with fakes.

## Tests

`tests/fakes/` holds in-memory counterparts of the edges (`FrozenClock`,
`InMemoryConsole`, `InMemoryFileSystem`, `RecordingEvolutionRunner`). Prefer these over
mocks — a fake with real behaviour catches integration mistakes that
`assert_called_with` never will. Because the clock is injected, assertions hardcode
timestamps: no `freezegun`, no sleeping, no flakiness.

`tests/unit/` covers pure classes; `tests/integration/` exercises the whole `Engine`
through fakes plus a CLI smoke test. No test should touch the real filesystem.

## Gotchas

- **The `evolution/` directory must not be named `openevolve/`.** `evaluator.py` does
  `from openevolve.evaluation_result import ...`, and a sibling directory of that name
  shadows the installed package once the script's directory lands on `sys.path`.
- `evolution/evaluator.py` is a frontend adapter over the same `Engine` the CLI calls.
  Keep it that way: the score the evolution loop optimises and the score
  `kaprekarevolve score` prints must not be able to drift apart. `uv run python
  evolution/evaluator.py evolution/seeds/kaprekar.py` should always agree with
  `uv run kaprekarevolve score` on the same file.
- Candidate programs define `transform(value)` inside `EVOLVE-BLOCK-START/END` markers.
- `checkpoint_interval` defaults to **100**, so a short run leaves nothing to visualize.
  Set it explicitly in `evolution/config.<backend>.yaml` before a run you intend to
  inspect.
- For anything about inspecting or plotting a run, use the **`openevolve-viz` skill** in
  `.claude/skills/` rather than hand-rolling checkpoint parsing.
- **`openevolve_output/` is not cleared between runs.** Checkpoints are overwritten in
  place, so a shorter run leaves the previous run's higher-numbered checkpoints behind,
  and directory mtimes still show the *old* times. `summarize_run.py` reads the
  highest-numbered checkpoint and the visualizer reads the most recently modified, so
  both will happily report stale data mid-run. `best/` is only written when a run
  finishes. Copy the directory aside before a re-run (`openevolve_output.*/` is
  gitignored) and don't trust either tool until the run completes.
- **The stage-1 sentinel and `cascade_thresholds` are a matched pair.**
  `_SCREEN_PASS_SCORE` in `modules/engine/default_engine.py` (0.0001) must sit *above*
  `cascade_thresholds[0]` in every `evolution/config.*.yaml` (0.00005) so a candidate
  that passes the contract check reaches stage 2, and *below* any score a real map can
  earn. OpenEvolve keeps stage 1's metrics when stage 2 times out, so when this sentinel
  was 1.0 a hung candidate recorded a perfect score — above the best map ever found.
- **Every metric named in `feature_dimensions` must be emitted on every path.**
  OpenEvolve computes MAP-Elites coordinates inside `database.add()` and raises when one
  is missing; the call that stores artifacts is the next statement, so it never runs.
  That silently cost all 173 rejections their explanation across every run on record —
  21264 checkpointed programs, zero artifacts. `REJECTED_FEATURES` in
  `modules/scoring/default_evaluation_projector.py` is what keeps this true, and
  `tests/unit/test_default_evaluation_projector.py` guards it.
- **The seed is not the lever on diversity.** A 200-iteration run from `kaprekar` ended
  with all 201 programs still containing the descending-minus-ascending step, and
  seeding `reverse_add` instead did not help: within ~12 iterations it discarded
  reverse-add as the core and adopted the Kaprekar difference. The anchoring comes from
  the system message and the in-context top programs. The untried lever is
  `diff_based_evolution: false`, which swaps "do not rewrite the entire program" for
  "provide the complete new program code".
- **One run proves very little.** Across identical configs the best result arrived at
  iteration 8, 41 and 129, and a novel constant found once (2802) did not reappear in
  two further runs. Long flat stretches are normal — one run improved after 91 idle
  iterations — so don't read an early plateau as convergence, and don't conclude a
  change helped from a single run.
- If `ScoreWeights` changes, the **system message in every `evolution/config.*.yaml`
  must change with it**. It states the depth saturation point to the model; leaving it
  stale means optimising against a threshold that no longer exists.
