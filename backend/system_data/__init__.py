"""System-aware reference data extracted from each system's open licence.

Each module exposes a single dict `REFERENCE` with the same shape so the
frontend Reference page can render any of them through a uniform contract.

Compliance posture per LEGAL_COMPLIANCE.md:
- D&D 5E content is restricted to CC-BY SRD 5.1 / 5.2 mechanics — no flavour
  prose, lore, or trademark-protected names. Page references cite the SRD only.
- Anime 5E content uses the OGL-released Anime 5E Tri-Stat Emporium SRD
  variant. Mechanic names + page references only.
- Cypher System content is published under the Cypher System Creator
  programme — mechanics, tier numbers, type/focus/descriptor names, and
  page-references only. No reproduced flavour prose.
"""
from .dnd5e_data import REFERENCE as DND5E_REFERENCE
from .anime5e_data import REFERENCE as ANIME5E_REFERENCE
from .cypher_data import REFERENCE as CYPHER_REFERENCE
from .decks import DECKS

__all__ = [
    "DND5E_REFERENCE", "ANIME5E_REFERENCE", "CYPHER_REFERENCE",
    "DECKS", "REFERENCE_BY_SYSTEM",
]


REFERENCE_BY_SYSTEM = {
    "dnd-5e": DND5E_REFERENCE,
    "anime-5e": ANIME5E_REFERENCE,
    "cypher": CYPHER_REFERENCE,
}
