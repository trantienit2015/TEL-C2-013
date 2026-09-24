"""Deterministic resolution ranking — a Tool (no LLM).

Per the architect note on the scaffold issue, ResolutionRankNode's ranking is a
deterministic score-sort, so it is implemented here as a pure Tool function (no State, no
side effects) called from the node — not an in-graph LLM node. Declared in docs/02_design.md.
"""

from __future__ import annotations

from typing import Any

# Runbook passages outrank historical ITSM examples for actionable steps.
_SOURCE_WEIGHT = {"runbook": 1.0, "itsm": 0.6}


def rank_resolutions(passages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank candidate resolution passages by retrieval score × source weight.

    Returns a new list of dicts: {doc_id, source, device, incident_type, steps_text,
    score, escalation}.
    """
    ranked = []
    for p in passages:
        weight = _SOURCE_WEIGHT.get(p.get("source", ""), 0.5)
        rank_score = round(p.get("score", 0.5) * weight, 4)
        ranked.append(
            {
                "doc_id": p.get("doc_id"),
                "source": p.get("source"),
                "device": p.get("device"),
                "incident_type": p.get("incident_type"),
                "steps_text": p.get("text", ""),
                "rank_score": rank_score,
                "escalation": p.get("escalation", []),
            }
        )
    ranked.sort(key=lambda r: r["rank_score"], reverse=True)
    return ranked


def merge_escalation_path(ranked: list[dict[str, Any]]) -> list[str]:
    """Merge a de-duplicated escalation path from the ranked resolutions (order-preserving)."""
    path: list[str] = []
    for r in ranked:
        for tier in r.get("escalation", []):
            if tier not in path:
                path.append(tier)
    return path
