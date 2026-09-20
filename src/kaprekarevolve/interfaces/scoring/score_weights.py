from pydantic import BaseModel, ConfigDict


class ScoreWeights(BaseModel):
    """Tunables of the combined score. Injected, never hard-coded in the policy."""

    model_config = ConfigDict(frozen=True)

    dominance_exponent: float = 1.5
    attractor_penalty: float = 0.25
    cycle_penalty: float = 0.5

    #: Kaprekar's routine settles in 4.66 steps on average and the enumerated catalogue
    #: of short maps has a median of 4.94, so this is where a Kaprekar-like map lives.
    depth_peak: float = 5.0
    depth_width: float = 3.0
    #: Kaprekar's deepest value takes 7 steps. Past this a map is padding its paths.
    max_depth_reference: float = 12.0

    #: depth_score is THE anti-triviality term, so its low end must not be generous.
    #: A bare Gaussian hands a near-constant map (mean depth 1.05) 0.18, where the ramp
    #: it replaces gave 0.005. This gate restores that guarantee continuously, rather
    #: than with a hard cutoff that only catches a mean of exactly 1.0.
    depth_onset: float = 1.0
    depth_onset_width: float = 1.0

    #: Kaprekar's own measured AST cost: "elegant" means no more elaborate than the map
    #: you are trying to beat.
    elegance_reference: float = 48.0

    #: What a map is worth once we know it is one we already have, under another name.
    known_map_penalty: float = 0.05
