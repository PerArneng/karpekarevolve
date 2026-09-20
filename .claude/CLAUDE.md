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
uv run kaprekarevolve best                # re-score the last run's winner

uv run pytest
uv run mypy src tests evolution           # strict; must stay clean
uv run ruff check src tests evolution
```

`evolve` uses the **Claude Code CLI** as its LLM backend (`provider: claude_code` in
`evolution/config.yaml`), so it needs no API key — just an authenticated `claude`
session. It costs real money; don't launch one without the user asking.

## The scoring contract

Every total map on a finite domain converges, so "does it converge?" measures nothing.
The evaluator grades the *shape* of the convergence instead — a product of four
factors, each in 0..1, in `modules/scoring/weighted_scoring_policy.py`:

```
combined_score = dominance^1.5 · parsimony · cycle_quality · depth_score
```

`depth_score` (mean steps to settle, saturating at mean depth 6) is the anti-triviality
term. Without it the search collapses onto `return 6174` and `return value`, which both
score exactly 0.0 today. If you ever find the search producing degenerate winners, that
term is the first place to look.

Output diversity is deliberately **not** scored: the real Kaprekar map emits only 55
distinct values out of 10000, so rewarding a wide image would punish the thing being
imitated. `image_ratio` is exported as a MAP-Elites feature instead.

**The baseline scores `0.292728`, and that number is pinned in four files** —
`tests/unit/test_weighted_scoring_policy.py`, `tests/integration/test_engine.py`,
`tests/integration/test_cli.py`, and the README's comparison table. Tuning
Note `tests/unit/test_weighted_scoring_policy.py` also pins a `depth_score` value
(currently `0.4499`) that moves with `depth_span` but is not the baseline. Tuning
`ScoreWeights` (e.g. raising `depth_span` so a 200-iteration run keeps discriminating
past the current 1.0 ceiling) is a reasonable thing to want, but update all four or the
suite goes red for the wrong reason.

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
