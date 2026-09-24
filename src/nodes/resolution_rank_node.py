"""AgentCore Platform v1.0 — TEL-C2-013 inner step 2: ResolutionRank."""

from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.resolution_ranker import merge_escalation_path, rank_resolutions


class ResolutionRankNode(FunctionNode):
    """Inner step 2: rank candidate resolutions and map the escalation path.

    Per the architect note (docs/02_design.md), ranking is a **deterministic score-sort
    implemented as a Tool** (`src.services.resolution_ranker`, no LLM) called from here.
    """

    # S-1: inner subgraph node — trust is verified at the outer backbone
    # (GraphNode main slot); inner nodes must never escalate above ANONYMOUS.
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.ANONYMOUS

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        passages = state.get("retrieved_passages", [])
        if not passages:
            emit_trace_event(
                "resolution_rank_rejected",
                {"correlation_id": state.get("correlation_id"), "reason": "no_passages"},
                state,
            )
            return {
                "status": AgentStatus.ERROR.value,
                "error_log": ["ResolutionRankNode: no candidate passages to rank"],
            }

        ranked = rank_resolutions(passages)
        escalation = merge_escalation_path(ranked)
        emit_trace_event(
            "resolutions_ranked",
            {"correlation_id": state.get("correlation_id"), "ranked_count": len(ranked)},
            state,
        )
        return {
            "ranked_resolutions": ranked,
            "escalation_path": escalation,
            "status": AgentStatus.SUCCESS.value,
        }
