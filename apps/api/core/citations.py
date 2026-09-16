"""
========================================================================================
ORCA: Marine EcOsystem Reasoning with Collaborative Agents (SIH 2026 - PS 26176)
Core: Verifiable Citation Tracking
========================================================================================
Every claim any domain agent makes (SST readings, IMD warnings, IMBL distances, etc.)
is registered here so the final synthesized answer can present a chip row of
verifiable, source-attributed citations to the user (IMD / INCOIS / ISRO Oceansat-3 /
Marine Regions / ORCA internal engines).
========================================================================================
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import itertools

_counter = itertools.count(1)


class CitationTracker:
    """Collects and de-duplicates verifiable citations across a single ORCA query lifecycle."""

    def __init__(self):
        self._citations: List[Dict[str, Any]] = []

    def add(
        self,
        claim: str,
        source: str,
        dataset_name: Optional[str] = None,
        reference_id: Optional[str] = None,
        is_live: bool = False,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        citation = {
            "id": next(_counter),
            "claim": claim,
            "source": source,
            "dataset_name": dataset_name,
            "reference_id": reference_id,
            "is_live_feed": is_live,
            "url": url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._citations.append(citation)
        return citation

    def all(self) -> List[Dict[str, Any]]:
        return list(self._citations)

    def sources_summary(self) -> List[str]:
        """Unique, ordered list of source names for a compact citation chip row."""
        seen = []
        for c in self._citations:
            if c["source"] not in seen:
                seen.append(c["source"])
        return seen

    def clear(self):
        self._citations.clear()

    def __len__(self):
        return len(self._citations)

    def __bool__(self) -> bool:
        # IMPORTANT: without this, an empty-but-present tracker (0 citations so far)
        # would be falsy due to __len__, causing every `if citation_tracker:` guard
        # across the domain agents to silently skip citation registration.
        return True
