from pydantic import BaseModel, ConfigDict

from kaprekarevolve.interfaces.novelty.map_fingerprint import MapFingerprint


class NoveltyRegistry(BaseModel):
    """The structures already known, each with the cheapest code known to reach it.

    Storing the cost, rather than only the fingerprint, is what lets the score discount
    prior art instead of banning it: a shorter route to a known structure is a real
    result, and a longer one is a rediscovery dressed up as a find.

    Frozen and injected, so a test supplies one directly and never touches a file.
    """

    model_config = ConfigDict(frozen=True)

    known_costs: dict[MapFingerprint, int] = {}

    def best_known_cost(self, fingerprint: MapFingerprint) -> int | None:
        """Return the cheapest known cost for this structure, or None if it is new."""
        return self.known_costs.get(fingerprint)
