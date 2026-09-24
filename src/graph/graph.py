"""AgentCore Platform v1.0 — TEL-C2-013 outer graph (Cat 2).

Telecom Network Incident Knowledge Base Q&A Agent.
L1 Base: AgentBaseGraph (Level 1 direct inheritance).

Outer backbone (fixed):
    initialize → pre_process(ValidateInput) → main(GraphNode)
              → post_process(GuidanceRender) → finalize
"""

from typing import Any, ClassVar, cast

from framework.graph.agent_base_graph import AgentBaseGraph
from framework.nodes.graph_node import GraphNode
from framework.schemas.agent_state import AgentState
from framework.schemas.trust_level import TrustLevel

from src.nodes.post_process_node import GuidanceRenderNode
from src.nodes.pre_process_node import ValidateInputNode
from src.schemas.state import State


class IncidentQAGraphNode(GraphNode):
    """Wraps the inner incident-resolution KB Q&A subgraph (`main` slot)."""

    # S-1: outer main-slot wrapper — first node in the outer backbone to receive
    # caller input after pre_process. Matches agent.yaml required_trust_level.
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.INTERNAL
    error_strategy: ClassVar[str] = "propagate"
    propagate_hitl: ClassVar[bool] = False

    def __init__(self, retriever: Any = None, top_k: int = 8, hybrid_search: bool = True):
        super().__init__()
        self._retriever = retriever
        self._top_k = top_k
        self._hybrid_search = hybrid_search

    def get_subgraph(self) -> Any:
        from src.graph.domain_workflow_graph import IncidentQAWorkflowGraph

        sg = IncidentQAWorkflowGraph(config=self._parent_config())
        sg.compile()
        return sg

    def extract_input(self, state: AgentState) -> str:
        return cast(str, state.get("validated_input", state.get("user_input", "")))

    def merge_output(self, state: AgentState, sub_result: dict[str, Any]) -> dict[str, Any]:
        return {
            "retrieved_passages": sub_result.get("retrieved_passages", []),
            "ranked_resolutions": sub_result.get("ranked_resolutions", []),
            "escalation_path": sub_result.get("escalation_path", []),
            "guidance": sub_result.get("guidance", ""),
            "citations": sub_result.get("citations", []),
            "status": sub_result.get("status"),
        }

    def _parent_config(self) -> dict[str, Any]:
        return {
            "retriever": self._retriever,
            "top_k": self._top_k,
            "hybrid_search": self._hybrid_search,
        }


class IncidentKBQAAgent(AgentBaseGraph):
    """Cat 2 outer graph — Telecom Network Incident Knowledge Base Q&A."""

    @property
    def name(self) -> str:
        return "tel-c2-013"

    @property
    def state_schema(self) -> type:
        return State

    def register_nodes(self) -> None:
        super().register_nodes()  # injects initialize + finalize
        cfg = self.config if hasattr(self, "config") and self.config else {}
        self._nodes["pre_process"] = ValidateInputNode()
        self._nodes["main"] = IncidentQAGraphNode(
            retriever=cfg.get("retriever"),
            top_k=cfg.get("top_k", 8),
            hybrid_search=cfg.get("hybrid_search", True),
        )
        self._nodes["post_process"] = GuidanceRenderNode()

    # add_edges() is NOT overridden — backbone wiring belongs to the framework.


# Alias for agent.yaml module:"src.graph" discovery.
Graph = IncidentKBQAAgent
