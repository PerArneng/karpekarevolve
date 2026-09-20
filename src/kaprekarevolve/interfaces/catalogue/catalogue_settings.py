from pathlib import Path

from pydantic import BaseModel, ConfigDict


class CatalogueSettings(BaseModel):
    """Where the catalogue lives and how wide a net it casts."""

    model_config = ConfigDict(frozen=True)

    registry_path: Path = Path("found-solutions/registry.json")
    report_path: Path = Path("found-solutions/CATALOGUE.md")
    #: Only maps this close to total convergence are worth recording as prior art.
    min_basin_fraction: float = 0.95
    max_cycle_length: int = 3
