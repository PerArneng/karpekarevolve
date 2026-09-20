from pathlib import Path

from pydantic import BaseModel, ConfigDict


class EvolutionSettings(BaseModel):
    """Where the evolution run finds its inputs and puts its output."""

    model_config = ConfigDict(frozen=True)

    initial_program_path: Path = Path("evolution/seeds/kaprekar.py")
    evaluator_path: Path = Path("evolution/evaluator.py")
    config_path: Path = Path("evolution/config.brain-tailscale.yaml")
    output_dir: Path = Path("openevolve_output")
    iterations: int = 200
