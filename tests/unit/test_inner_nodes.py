# TEL-C2-013 — Unit Tests: inner KB-Q&A nodes

import json

from framework.schemas.agent_status import AgentStatus
from src.nodes.guidance_assemble_node import GuidanceAssembleNode
from src.nodes.kb_retrieve_node import KBRetrieveNode
from src.nodes.resolution_rank_node import ResolutionRankNode


class TestKBRetrieveNode:
    def test_success_retrieves(self):
        node = KBRetrieveNode()
        payload = {"query": "core router BGP flap 発生"}
        result = node.execute({"user_input": json.dumps(payload), "node_history": [], "error_log": []})
        assert result["status"] == AgentStatus.SUCCESS
        assert len(result["retrieved_passages"]) >= 1

    def test_invalid_payload_errors(self):
        node = KBRetrieveNode()
        result = node.execute({"user_input": "not-json", "node_history": [], "error_log": []})
        assert result["status"] == AgentStatus.ERROR


class TestResolutionRankNode:
    def setup_method(self):
        self.node = ResolutionRankNode()

    def test_runbook_outranks_itsm(self):
        state = {
            "retrieved_passages": [
                {"doc_id": "ITSM-1", "source": "itsm", "device": "d", "incident_type": "t", "text": "past", "score": 0.9, "escalation": ["Tier2"]},
                {"doc_id": "RUNBOOK-1", "source": "runbook", "device": "d", "incident_type": "t", "text": "steps", "score": 0.7, "escalation": ["Tier1", "Tier2"]},
            ],
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS
        # runbook 0.7*1.0=0.7 > itsm 0.9*0.6=0.54 -> runbook ranks first
        assert result["ranked_resolutions"][0]["doc_id"] == "RUNBOOK-1"
        assert result["escalation_path"] == ["Tier1", "Tier2"]

    def test_no_passages_errors(self):
        result = self.node.execute({"retrieved_passages": [], "node_history": [], "error_log": []})
        assert result["status"] == AgentStatus.ERROR


class TestGuidanceAssembleNode:
    def setup_method(self):
        self.node = GuidanceAssembleNode()

    def test_assembles_guidance_with_citation(self):
        state = {
            "ranked_resolutions": [
                {"doc_id": "RUNBOOK-1", "source": "runbook", "steps_text": "do X", "rank_score": 0.7, "escalation": ["Tier2"]}
            ],
            "escalation_path": ["Tier2"],
            "node_history": [],
            "error_log": [],
            "trace_id": "t",
            "correlation_id": "c",
            "session_id": "s",
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS
        assert "RUNBOOK-1" in result["guidance"]
        assert result["citations"] == ["RUNBOOK-1"]

    def test_empty_ranked_still_produces_guidance(self):
        state = {"ranked_resolutions": [], "escalation_path": [], "node_history": [], "error_log": [], "trace_id": "t", "correlation_id": "c", "session_id": "s"}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS
        assert result["guidance"]
        assert result["citations"] == []
