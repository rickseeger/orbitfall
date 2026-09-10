"""High-score save/load: JSON in the XDG data directory (DESIGN.md sec 5.7).

Round-trip save/load plus corrupt-file handling are unit-tested in node 3's
test plan. Node 3 owns this.

Intended public API (node 3):
    load_high_score() -> int
    save_high_score(score: int) -> None
"""

from __future__ import annotations

__all__: list[str] = []
