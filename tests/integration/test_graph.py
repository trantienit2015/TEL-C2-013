# TEL-C2-013 — Integration Tests: full graph compile + invoke (Cat 2)

from framework.schemas.agent_status import AgentStatus
from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel
from src.graph.graph import Graph


def _ctx():
    return InvocationContext(
        session_id="it-1",
        caller_trust_level=TrustLevel.INTERNAL,
        caller_id="noc-engineer",
    )


class TestGraphIntegration:
    def test_full_pipeline_success(self):
        agent = Graph()
        agent.compile()
        result = agent.invoke("core router BGP セッションが flap している。対応手順は？", ctx=_ctx())
        assert result["status"] in (AgentStatus.SUCCESS, AgentStatus.SUCCESS.value)
        assert len(result.get("node_history", [])) >= 5
        out = result.get("formatted_output") or result.get("output")
        assert isinstance(out, dict)
        assert out["guidance"]
        assert out["citations"]
        assert "disclaimer" in out

    def test_empty_input_terminates(self):
        agent = Graph()
        agent.compile()
        result = agent.invoke("", ctx=_ctx())
        assert "status" in result
        assert len(result.get("node_history", [])) >= 3

    def test_escalation_path_surfaces(self):
        agent = Graph()
        agent.compile()
        result = agent.invoke("enodeb セル停止 cell outage の対応", ctx=_ctx())
        out = result.get("formatted_output") or result.get("output")
        assert out["escalation_path"]
