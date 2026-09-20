from kaprekarevolve.interfaces.catalogue import CatalogueEntry
from kaprekarevolve.interfaces.evolution import EvolutionResult
from kaprekarevolve.interfaces.kaprekar import Attractor, Trajectory
from kaprekarevolve.interfaces.scoring import ScoreCard

_MAX_LISTED_ATTRACTORS = 8
_MAX_LISTED_MEMBERS = 8


class TextReportFormatter:
    """Renders reports as plain text. Pure."""

    def format_score_card(self, title: str, card: ScoreCard) -> str:
        lines = [title, "=" * len(title)]
        analysis = card.analysis
        if not card.valid or analysis is None:
            failure = card.failure
            reason = failure.reason.value if failure is not None else "unknown"
            detail = failure.detail if failure is not None else ""
            lines.append(f"REJECTED ({reason}): {detail}")
            lines.append("combined_score  0.000000")
            return "\n".join(lines)
        lines.extend(
            [
                f"combined_score          {card.combined_score:.6f}",
                "",
                f"  dominance             {card.dominance:.6f}",
                f"  attractor_focus       {card.attractor_focus:.6f}",
                f"  cycle_quality         {card.cycle_quality:.6f}",
                f"  depth_score           {card.depth_score:.6f}",
                f"  elegance              {card.elegance:.6f}"
                f"{self._cost(card)}",
                f"  novelty               {card.novelty:.6f}"
                f"{self._novelty_note(card)}",
                "",
                f"attractors              {analysis.attractor_count}",
                f"dominant basin          {analysis.dominant_basin_fraction:.4%} of "
                f"{analysis.domain_size}",
                f"dominant cycle          {self._members(analysis.dominant_attractor)}",
                f"mean / max depth        {analysis.mean_depth:.2f} / {analysis.max_depth}",
                f"distinct outputs        {analysis.image_size} "
                f"({analysis.image_ratio:.2%})",
                f"fixed points            {analysis.fixed_point_count}",
                "",
                "basins:",
            ]
        )
        for attractor in analysis.attractors[:_MAX_LISTED_ATTRACTORS]:
            share = attractor.basin_size / analysis.domain_size
            lines.append(
                f"  {self._members(attractor):<44} {attractor.basin_size:>6}  {share:7.2%}"
            )
        hidden = analysis.attractor_count - _MAX_LISTED_ATTRACTORS
        if hidden > 0:
            lines.append(f"  ... and {hidden} more")
        return "\n".join(lines)

    def format_catalogue(self, examined: int, entries: list[CatalogueEntry]) -> str:
        title = "Short-formula catalogue"
        lines = [
            title,
            "=" * len(title),
            f"{examined} formulas examined, {len(entries)} distinct structures.",
            "",
            "Each row is the cheapest formula known to reach that structure. A candidate",
            "matching one of these is scored as prior art unless it gets there in less code.",
            "",
            f"{'formula':44s} {'cost':>4s} {'attractor':>22s} {'basin':>7s} {'mean':>5s}",
            "-" * 88,
        ]
        for entry in entries:
            lines.append(
                f"{entry.formula:44s} {entry.cost:4d} "
                f"{self._digits(entry.attractor):>22s} "
                f"{entry.basin_fraction:7.4f} {entry.mean_depth:5.2f}"
            )
        return "\n".join(lines)

    def format_trajectory(self, trajectory: Trajectory) -> str:
        walk = " -> ".join(f"{value:04d}" for value in trajectory.values)
        if trajectory.cycle:
            ending = (
                f"cycle {self._digits(trajectory.cycle)} reached after "
                f"{trajectory.steps_to_cycle} step(s)"
            )
        else:
            ending = f"no cycle within {trajectory.steps_to_cycle} steps"
        return f"{trajectory.seed:04d}: {walk}\n{ending}"

    def format_evolution_result(self, result: EvolutionResult) -> str:
        lines = [
            f"best combined_score     {result.best_score:.6f}",
            f"output directory        {result.output_dir or '(none)'}",
            "",
            "metrics:",
        ]
        lines.extend(f"  {name:<22} {value:.6f}" for name, value in sorted(result.metrics.items()))
        lines.extend(["", "best program:", result.best_code])
        return "\n".join(lines)

    @staticmethod
    def _cost(card: ScoreCard) -> str:
        return f"   (AST cost {card.shape.cost})" if card.shape is not None else ""

    @staticmethod
    def _novelty_note(card: ScoreCard) -> str:
        """Say so plainly when a map is only a known one wearing different values."""
        return "   (already known: a relabelling)" if card.novelty < 1.0 else ""

    def _members(self, attractor: Attractor) -> str:
        return self._digits(attractor.members)

    def _digits(self, values: tuple[int, ...]) -> str:
        shown = ", ".join(f"{value:04d}" for value in values[:_MAX_LISTED_MEMBERS])
        if len(values) > _MAX_LISTED_MEMBERS:
            shown = f"{shown}, ... ({len(values)} long)"
        return f"[{shown}]"
