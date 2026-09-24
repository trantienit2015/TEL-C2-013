"""AgentCore Platform v1.0 — TEL-C2-013 inner step 1: KBRetrieve."""

import json
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

from src.services.kb_service import hybrid_retrieve


class KBRetrieveNode(FunctionNode):
    """Inner step 1: parse the JSON payload from the outer pre_process, then run hybrid
    retrieval (dense multilingual-e5 + BM25 for device/error codes) over the internal
    runbook KB + ServiceNow ITSM export, metadata-filtered by device / incident-type.
    """

    # S-1: inner subgraph node — trust is verified at the outer backbone
    # (GraphNode main slot); inner nodes must never escalate above ANONYMOUS.
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.ANONYMOUS

    def __init__(self, retriever: Any = None, top_k: int = 8, hybrid_search: bool = True):
        self._retriever = retriever
        self._top_k = top_k
        self._hybrid_search = hybrid_search

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        raw = state.get("user_input", "")
        try:
            payload = json.loads(raw) if isinstance(raw, str) else raw
        except (ValueError, TypeError):
            payload = None

        if not isinstance(payload, dict) or not (payload.get("query") or "").strip():
            emit_trace_event(
                "kb_retrieve_rejected",
                {"correlation_id": state.get("correlation_id"), "reason": "invalid_payload"},
                state,
            )
            return {
                "status": AgentStatus.ERROR.value,
                "error_log": ["KBRetrieveNode: missing/invalid inner payload"],
            }

        passages = hybrid_retrieve(
            payload["query"],
            top_k=self._top_k,
            hybrid_search=self._hybrid_search,
            retriever=self._retriever,
        )
        emit_trace_event(
            "kb_passages_retrieved",
            {"correlation_id": state.get("correlation_id"), "passage_count": len(passages)},
            state,
        )
        return {
            "validated_query": payload["query"],
            "retrieved_passages": passages,
            "status": AgentStatus.SUCCESS.value,
        }
