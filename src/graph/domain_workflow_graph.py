"""AgentCore Platform v1.0 — TEL-C2-013 inner domain workflow graph (Cat 2).

Linear: START → kb_retrieve → resolution_rank → guidance_assemble → END
"""

from typing import Any
from langgraph.graph import END, START

from framework.graph.base_graph import BaseGraph
from framework.schemas.agent_state import AgentState
from framework.schemas.agent_status import AgentStatus

from src.nodes.guidance_assemble_node import GuidanceAssembleNode
from src.nodes.kb_retrieve_node import KBRetrieveNode
from src.nodes.resolution_rank_node import ResolutionRankNode
from src.schemas.state import State


class IncidentQAWorkflowGraph(BaseGraph):
    """Inner graph for the telecom incident-resolution KB Q&A workflow."""

    @property
    def name(self) -> str:
        return "incident_kb_qa_workflow"

    @property
    def state_schema(self) -> type:
        return State

    def _validate_config(self) -> None:
        pass

    def register_nodes(self) -> None:
        cfg = self.config if hasattr(self, "config") and self.config else {}
        retriever = cfg.get("retriever")
        top_k = cfg.get("top_k", 8)
        hybrid_search = cfg.get("hybrid_search", True)

        self._nodes["kb_retrieve"] = KBRetrieveNode(retriever=retriever, top_k=top_k, hybrid_search=hybrid_search)
        self._nodes["resolution_rank"] = ResolutionRankNode()
        self._nodes["guidance_assemble"] = GuidanceAssembleNode()

    def add_edges(self) -> None:
        self._sg.add_edge(START, "kb_retrieve")
        self._sg.add_edge("kb_retrieve", "resolution_rank")
        self._sg.add_edge("resolution_rank", "guidance_assemble")
        self._sg.add_edge("guidance_assemble", END)

    def route(self, state: AgentState) -> str:
        return END if state.get("status") == AgentStatus.ERROR.value else "guidance_assemble"

    def get_output(self, state: AgentState) -> dict[str, Any]:
        return {
            "validated_query": state.get("validated_query", ""),
            "retrieved_passages": state.get("retrieved_passages", []),
            "ranked_resolutions": state.get("ranked_resolutions", []),
            "escalation_path": state.get("escalation_path", []),
            "guidance": state.get("guidance", ""),
            "citations": state.get("citations", []),
            "status": state.get("status"),
            "trace_id": state.get("trace_id"),
            "correlation_id": state.get("correlation_id"),
            "node_history": state.get("node_history", []),
        }
