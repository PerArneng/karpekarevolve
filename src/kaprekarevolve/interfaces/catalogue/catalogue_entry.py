from pydantic import BaseModel, ConfigDict

from kaprekarevolve.interfaces.novelty.map_fingerprint import MapFingerprint


class CatalogueEntry(BaseModel):
    """One structure, with the cheapest formula found to reach it."""

    model_config = ConfigDict(frozen=True)

    formula: str
    fingerprint: MapFingerprint
    cost: int
    attractor: tuple[int, ...]
    basin_fraction: float
    attractor_count: int
    mean_depth: float
    max_depth: int
