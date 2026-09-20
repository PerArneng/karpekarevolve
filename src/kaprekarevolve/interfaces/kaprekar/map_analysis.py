from pydantic import BaseModel, ConfigDict

from kaprekarevolve.interfaces.kaprekar.attractor import Attractor


class MapAnalysis(BaseModel):
    """The shape of a map's convergence over the whole domain."""

    model_config = ConfigDict(frozen=True)

    domain_size: int
    attractors: tuple[Attractor, ...]
    attractor_count: int
    dominant_attractor: Attractor
    dominant_basin_fraction: float
    dominant_cycle_length: int
    mean_depth: float
    max_depth: int
    image_size: int
    image_ratio: float
    fixed_point_count: int
    depth_histogram: tuple[tuple[int, int], ...]
    indegree_histogram: tuple[tuple[int, int], ...]
