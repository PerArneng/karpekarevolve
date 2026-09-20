#!/usr/bin/env python3
"""Summarise an OpenEvolve run in the terminal. Standard library only.

Reads the program records OpenEvolve writes into checkpoints and answers the
questions you usually have first: did the score move, when did it move, and what
is sitting at the top of the population right now.

    python summarize_run.py [RUN_DIR] [--metric NAME] [--top N] [--csv FILE]

RUN_DIR defaults to ./openevolve_output. Point it at the run directory or at a
single checkpoint; both work.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

BAR_WIDTH = 40


def find_checkpoints(root: Path) -> list[Path]:
    """Return every checkpoint under ``root``, oldest first."""
    if (root / "programs").is_dir():
        return [root]
    found = [path for path in root.rglob("checkpoint_*") if (path / "programs").is_dir()]
    return sorted(found, key=lambda path: _checkpoint_number(path))


def _checkpoint_number(path: Path) -> int:
    tail = path.name.rsplit("_", 1)[-1]
    return int(tail) if tail.isdigit() else 0


def load_programs(checkpoint: Path) -> list[dict]:
    """Load every program record in a checkpoint, skipping anything unreadable."""
    programs = []
    for path in sorted((checkpoint / "programs").glob("*.json")):
        try:
            programs.append(json.loads(path.read_text()))
        except (OSError, json.JSONDecodeError) as error:
            print(f"  ! skipped {path.name}: {error}", file=sys.stderr)
    return programs


def metric(program: dict, name: str) -> float | None:
    value = (program.get("metrics") or {}).get(name)
    return float(value) if isinstance(value, (int, float)) else None


def bar(value: float, low: float, high: float) -> str:
    span = high - low
    filled = BAR_WIDTH if span <= 0 else round(BAR_WIDTH * (value - low) / span)
    return "#" * max(0, filled) + "." * (BAR_WIDTH - max(0, filled))


def report_progress(programs: list[dict], name: str) -> None:
    """Show the running best of ``name`` against the iteration it was found at."""
    scored = [
        (program.get("iteration_found") or 0, metric(program, name))
        for program in programs
        if metric(program, name) is not None
    ]
    if not scored:
        print(f"No program carries a '{name}' metric.")
        return
    scored.sort()
    values = [value for _, value in scored]
    low, high = min(values), max(values)

    print(f"\nbest {name} by iteration")
    running = None
    for iteration, value in scored:
        running = value if running is None else max(running, value)
        marker = " <- new best" if running == value and value == high else ""
        print(f"  {iteration:>5}  {bar(running, low, high)}  {running:.6f}{marker}")
    print(f"\n  first {values[0]:.6f}   best {high:.6f}   lift {high - values[0]:+.6f}")


def report_spread(programs: list[dict], name: str) -> None:
    """Show how the population spreads over a feature - the MAP-Elites question."""
    counts = Counter(
        round(value, 3) for value in (metric(program, name) for program in programs)
        if value is not None
    )
    if not counts:
        return
    print(f"\npopulation spread over {name}")
    widest = max(counts.values())
    for value, count in sorted(counts.items()):
        print(f"  {value:>10}  {'#' * round(BAR_WIDTH * count / widest):<{BAR_WIDTH}} {count}")


def report_top(programs: list[dict], name: str, top: int) -> None:
    ranked = sorted(
        (program for program in programs if metric(program, name) is not None),
        key=lambda program: metric(program, name) or 0.0,
        reverse=True,
    )[:top]
    if not ranked:
        return
    print(f"\ntop {len(ranked)} by {name}")
    print(f"  {'id':<10} {'iter':>5} {'gen':>4} {name:>12}  other metrics")
    for program in ranked:
        others = ", ".join(
            f"{key}={value:g}"
            for key, value in sorted((program.get("metrics") or {}).items())
            if key != name and isinstance(value, (int, float))
        )
        print(
            f"  {str(program.get('id', '?'))[:8]:<10} "
            f"{program.get('iteration_found', 0):>5} "
            f"{program.get('generation', 0):>4} "
            f"{metric(program, name):>12.6f}  {others}"
        )


def write_csv(programs: list[dict], destination: Path) -> None:
    names = sorted({key for program in programs for key in (program.get("metrics") or {})})
    with destination.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["id", "parent_id", "generation", "iteration_found", *names])
        for program in programs:
            metrics = program.get("metrics") or {}
            writer.writerow(
                [
                    program.get("id", ""),
                    program.get("parent_id", "") or "",
                    program.get("generation", 0),
                    program.get("iteration_found", 0),
                    *[metrics.get(name, "") for name in names],
                ]
            )
    print(f"\nwrote {destination} ({len(programs)} rows)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", nargs="?", default="openevolve_output", type=Path)
    parser.add_argument("--metric", default="combined_score", help="metric to rank by")
    parser.add_argument("--spread", action="append", default=[], help="feature to bucket by")
    parser.add_argument("--top", type=int, default=5)
    parser.add_argument("--csv", type=Path, help="dump every program's metrics here")
    args = parser.parse_args()

    if not args.run_dir.exists():
        print(f"{args.run_dir} does not exist.", file=sys.stderr)
        return 1

    checkpoints = find_checkpoints(args.run_dir)
    if not checkpoints:
        print(
            f"No checkpoints under {args.run_dir}.\n"
            "OpenEvolve only writes them every `checkpoint_interval` iterations "
            "(default 100), so a short run leaves nothing behind. Lower the interval "
            "in your config and run again.",
            file=sys.stderr,
        )
        return 1

    latest = checkpoints[-1]
    programs = load_programs(latest)
    print(f"run       {args.run_dir}")
    print(f"checkpoints {len(checkpoints)}: {', '.join(path.name for path in checkpoints)}")
    print(f"reading   {latest.name}  ({len(programs)} programs)")

    report_progress(programs, args.metric)
    for feature in args.spread:
        report_spread(programs, feature)
    report_top(programs, args.metric, args.top)
    if args.csv:
        write_csv(programs, args.csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
