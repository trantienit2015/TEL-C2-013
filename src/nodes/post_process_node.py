"""AgentCore Platform v1.0 — TEL-C2-013 outer post_process node (GuidanceRender)."""

from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.guidance_service import GUIDANCE_DISCLAIMER


class GuidanceRenderNode(FunctionNode):
    """Outer post_process: assemble the final resolution-guidance payload (JSON-shaped) from
    the inner-subgraph fields merged into outer state, with a disclaimer.
    """

    # S-1: outer node — matches agent.yaml required_trust_level.
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.INTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        report = {
            "guidance": state.get("guidance", ""),
            "ranked_resolutions": state.get("ranked_resolutions", []),
            "escalation_path": state.get("escalation_path", []),
            "citations": state.get("citations", []),
            "disclaimer": GUIDANCE_DISCLAIMER,
        }
        emit_trace_event(
            "guidance_rendered",
            {
                "correlation_id": state.get("correlation_id"),
                "citation_count": len(report["citations"]),
            },
            state,
        )
        return {
            "formatted_output": report,
            "result": report["guidance"],
            "status": AgentStatus.SUCCESS.value,
        }
