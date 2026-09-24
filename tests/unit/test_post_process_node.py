# TEL-C2-013 — Unit Tests: GuidanceRenderNode (post_process)

from framework.schemas.agent_status import AgentStatus
from src.nodes.post_process_node import GuidanceRenderNode


class TestGuidanceRenderNode:
    def setup_method(self):
        self.node = GuidanceRenderNode()

    def test_assembles_payload_with_disclaimer(self):
        state = {
            "guidance": "Recommended (RUNBOOK-1): do X",
            "ranked_resolutions": [{"doc_id": "RUNBOOK-1"}],
            "escalation_path": ["Tier2"],
            "citations": ["RUNBOOK-1"],
            "node_history": [],
            "error_log": [],
        }
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS
        out = result["formatted_output"]
        assert out["guidance"]
        assert out["escalation_path"] == ["Tier2"]
        assert out["citations"] == ["RUNBOOK-1"]
        assert "disclaimer" in out

    def test_defaults_when_empty(self):
        result = self.node.execute({"node_history": [], "error_log": []})
        out = result["formatted_output"]
        assert out["guidance"] == ""
        assert "disclaimer" in out
