from pydantic import BaseModel, ConfigDict


class Trajectory(BaseModel):
    """The walk of one seed until it re-enters a value it has already visited."""

    model_config = ConfigDict(frozen=True)

    seed: int
    values: tuple[int, ...]
    cycle: tuple[int, ...]
    steps_to_cycle: int
