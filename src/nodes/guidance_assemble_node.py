"""AgentCore Platform v1.0 — TEL-C2-013 inner step 3: GuidanceAssemble (S-3 output gate)."""

from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.guidance_service import assemble_guidance


class GuidanceAssembleNode(FunctionNode):
    """Inner step 3 (S-3 output gate): assemble ranked resolution guidance + escalation path
    with a source runbook/ITSM citation. Guidance + citations are always produced — never
    silently suppressed.
    """

    # S-1: inner subgraph node — trust is verified at the outer backbone
    # (GraphNode main slot); inner nodes must never escalate above ANONYMOUS.
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.ANONYMOUS

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        ranked = state.get("ranked_resolutions", [])
        escalation = state.get("escalation_path", [])
        result = assemble_guidance(ranked, escalation)

        emit_trace_event(
            "incident_guidance_assembled",
            {"resolution_count": len(ranked), "escalation_tiers": len(escalation)},
            state,
        )

        return {
            "guidance": result["guidance"],
            "citations": result["citations"],
            "status": AgentStatus.SUCCESS.value,
        }
