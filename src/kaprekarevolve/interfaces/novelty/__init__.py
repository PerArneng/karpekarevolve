"""Novelty: telling a discovery from a map we already knew."""

from kaprekarevolve.interfaces.novelty.fingerprinter import Fingerprinter
from kaprekarevolve.interfaces.novelty.map_fingerprint import MapFingerprint
from kaprekarevolve.interfaces.novelty.novelty_registry import NoveltyRegistry
from kaprekarevolve.interfaces.novelty.registry_loader import RegistryLoader

__all__ = ["Fingerprinter", "MapFingerprint", "NoveltyRegistry", "RegistryLoader"]
