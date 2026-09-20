from pydantic import BaseModel, ConfigDict


class Attractor(BaseModel):
    """A terminal cycle and the share of the domain that falls into it."""

    model_config = ConfigDict(frozen=True)

    members: tuple[int, ...]
    cycle_length: int
    basin_size: int
