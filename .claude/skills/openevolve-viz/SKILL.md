---
name: openevolve-viz
description: Visualize and inspect the progress of an OpenEvolve evolution run in this project - the evolution tree, the MAP-Elites grid, best-score-over-iteration, and diffs between parent and child programs. Use this skill whenever the user asks how a run is going, what the evolution found, whether the score is still improving, which programs are in the population, or wants to see, plot, chart, graph, or open a visualizer / dashboard / UI for an `evolve` run or its `openevolve_output` directory - and also when they are simply staring at a finished run asking "did that actually work?". Reach for it before hand-rolling any ad-hoc plotting of checkpoint data.
---

# Visualizing an OpenEvolve run

The point of a run is to watch a population get better. Two questions come up
constantly — *is the score still climbing?* and *what does the winner actually do
differently?* — and there are two tools here, one for each.

Start with the **terminal summary** (instant, no dependencies). Reach for the
**Flask visualizer** when the user wants to click around the evolution tree, see the
MAP-Elites grid, or read diffs.

## First: make sure there is something to visualize

Both tools read **checkpoints**, not the live run. OpenEvolve writes a checkpoint
every `checkpoint_interval` iterations, and **that setting defaults to 100** — so a
short exploratory run finishes having written nothing but `best/` and `logs/`, and
every visualization comes up empty. This is the single most common reason "the
visualizer shows nothing".

If `openevolve_output/checkpoints/` is missing or empty, that is the diagnosis. Fix it
in `evolution/config.<backend>.yaml` before the next run:

```yaml
max_iterations: 200
checkpoint_interval: 10   # ~20 snapshots over a 200-iteration run
```

Pick an interval that yields roughly 10-30 checkpoints across the run. Each one
serializes the whole population, so `1` is wasteful on a long run and `100` is useless
on a short one. Checkpoints are also resume points (`--checkpoint_path`), which is a
second reason to keep them frequent enough to be worth having.

A checkpoint looks like this, and both tools depend on the `programs/` directory:

```
openevolve_output/
  checkpoints/checkpoint_10/
    metadata.json          islands, archive, best_program_id, feature_stats
    programs/<id>.json      one record per program: code, parent_id, generation,
                            iteration_found, metrics{...}, complexity, diversity
    best_program.py
    best_program_info.json
  best/                     the winner of the whole run
  logs/                     openevolve_<timestamp>.log
```

## The fast path: terminal summary

`scripts/summarize_run.py` ships with this skill. Standard library only, so it runs
against any Python — no install, no server, no browser:

```bash
python .claude/skills/openevolve-viz/scripts/summarize_run.py
```

It defaults to `openevolve_output` and prints the running best by iteration, the top
programs with their metrics, and where the lift came from:

```
best combined_score by iteration
      0  ........................................  0.585457
      3  ########################################  1.000000 <- new best

  first 0.585457   best 1.000000   lift +0.414543
```

Useful flags:

| Flag | Why |
|---|---|
| `--metric mean_depth` | rank by something other than `combined_score` |
| `--spread elegance` | bucket the population over a feature — the poor man's MAP-Elites grid |
| `--top 10` | show more of the leaderboard |
| `--csv /tmp/run.csv` | dump every program's metrics for your own plotting |

In this project the metrics worth passing are the ones
`DefaultEvaluationProjector` emits: `combined_score`, `validity`, `dominance`,
`attractor_focus`, `cycle_quality`, `depth_score`, `elegance`, `novelty`,
`attractor_count`, `dominant_basin_fraction`, `dominant_cycle_length`, `mean_depth`,
`max_depth`, `image_ratio`, `depth_ratio`, `elegance_cost`,
`fixed_point_count`, `validity`. The three the MAP-Elites grid is configured on live
under `database.feature_dimensions` in `evolution/config.<backend>.yaml`.

When a summary shows the score flat across every checkpoint, say so plainly and look
at `validity` in the spread — a population of rejected candidates (validity 0) means
the LLM is fighting the contract, not the problem, and the fix is in the evaluator's
artifact messages or the system message, not in the visualization.

## The rich path: the Flask visualizer

This is the interactive UI from the OpenEvolve README: evolution tree with
parent-child links, MAP-Elites grid, per-metric coloring, and a code diff viewer.

**It is not in the PyPI package.** `pip install openevolve` gives you the library
only; `scripts/visualizer.py` lives in the GitHub repo and imports its own `manual.py`,
`templates/` and `static/` siblings — so copying the single file out will fail with
`ModuleNotFoundError: No module named 'manual'`. Get the directory, not the file:

```bash
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/algorithmicsuperintelligence/openevolve.git /tmp/openevolve-viz
git -C /tmp/openevolve-viz sparse-checkout set scripts
```

Then run it against this project's output. Use `--no-project` so uv builds a throwaway
environment with Flask instead of trying to install the clone as a package:

```bash
uv run --no-project --with flask \
  python /tmp/openevolve-viz/scripts/visualizer.py --path openevolve_output
```

It serves on <http://127.0.0.1:8080>. Flags: `--path` (run directory *or* a single
`checkpoints/checkpoint_N`), `--host`, `--port`, `--log-level`, and `--static-output
DIR` to write a standalone HTML export.

Two behaviours worth knowing, both of which look like bugs otherwise:

- It searches recursively for `checkpoint_*` and shows **the most recently modified
  one**. It does not follow a run live — restart or re-point it after new checkpoints
  land.
- `--static-output` writes `index.html` plus its assets, but the process may keep
  running rather than exiting. Once the files are on disk you can stop it; the export
  is complete and self-contained, which makes it the right choice for sharing a result
  or dropping a snapshot into a report.

Run the server in the background and tell the user the URL rather than blocking on it.

## Watching a run as it happens

The visualizer is a post-hoc tool. While a run is going, the log is the live view:

```bash
tail -f openevolve_output/logs/openevolve_*.log
```

New checkpoint directories appearing under `openevolve_output/checkpoints/` are the
other progress signal — re-running the terminal summary after each one is the cheapest
way to answer "is it still improving?" without restarting anything.

## When you need something the tools do not show

`evolution_trace` writes one JSONL record per evolution step and ships *with* the
package, so it needs no clone. It is off by default; enable it in `evolution/config.<backend>.yaml`:

```yaml
evolution_trace:
  enabled: true
  format: jsonl
  include_code: false    # true makes the file much larger
  output_path: null      # defaults inside the output directory
```

That file, or `summarize_run.py --csv`, is the right input for a custom chart. Prefer
either of those over parsing `programs/*.json` by hand each time — the schema is stable
but re-deriving it per question is wasted work.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Visualizer loads but is empty | No checkpoints. `checkpoint_interval` (default 100) exceeded the run length. |
| `ModuleNotFoundError: No module named 'manual'` | Copied `visualizer.py` alone. Sparse-clone the whole `scripts/` directory. |
| uv tries to build `openevolve` and fails | Ran `uv run` from inside the clone. Add `--no-project`. |
| Shows an old run's data | It picks the most recently modified `checkpoint_*` found recursively. Point `--path` at one specific checkpoint. |
| `Address already in use` | An earlier visualizer is still running. `--port 8081`, or kill it. |
| Every program scores 0 | Not a visualization problem — candidates are failing the evaluator's contract. Check `validity` and the artifact messages. |
