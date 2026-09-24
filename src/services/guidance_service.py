"""Assemble ranked resolution guidance + escalation path with source citations."""

from __future__ import annotations

from typing import Any

GUIDANCE_DISCLAIMER = (
    "This resolution guidance is retrieved from internal runbooks and historical ITSM "
    "incidents to assist NOC engineers. Verify against current network state and follow "
    "your change-management procedure before applying any remediation."
)


def assemble_guidance(ranked: list[dict[str, Any]], escalation_path: list[str]) -> dict[str, Any]:
    """Return {guidance, citations}. The top-ranked resolution leads; others are alternatives."""
    if not ranked:
        return {"guidance": "No matching resolution found in the internal KB for this query.", "citations": []}

    lines = []
    top = ranked[0]
    lines.append(f"Recommended ({top['doc_id']}, source={top['source']}): {top['steps_text']}")
    for alt in ranked[1:3]:
        lines.append(f"Alternative ({alt['doc_id']}, source={alt['source']}): {alt['steps_text']}")
    if escalation_path:
        lines.append("Escalation path: " + " -> ".join(escalation_path))

    citations = [r["doc_id"] for r in ranked if r.get("doc_id")]
    return {"guidance": "\n".join(lines), "citations": citations}
