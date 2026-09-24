# TEL-C2-013 - criterion #15 regression: every node must assign status as the
# .value STRING, never the bare AgentStatus Enum object. Equality asserts
# (`== AgentStatus.X`) pass for both forms because AgentStatus(str, Enum) - so
# this test asserts the runtime TYPE instead, which is the only check that
# actually catches a bare-Enum regression.

from framework.schemas.agent_status import AgentStatus

from src.nodes.guidance_assemble_node import GuidanceAssembleNode
from src.nodes.kb_retrieve_node import KBRetrieveNode
from src.nodes.post_process_node import GuidanceRenderNode
from src.nodes.pre_process_node import ValidateInputNode
from src.nodes.resolution_rank_node import ResolutionRankNode


def _assert_str_status(result: dict) -> None:
    status = result["status"]
    assert isinstance(status, str)
    assert not isinstance(status, AgentStatus)


class TestStatusIsStringNotBareEnum:
    def test_validate_input_success_and_error(self):
        _assert_str_status(ValidateInputNode().execute({"user_input": "BGP flap"}))
        _assert_str_status(ValidateInputNode().execute({"user_input": ""}))

    def test_kb_retrieve_success_and_error(self):
        _assert_str_status(KBRetrieveNode().execute({"user_input": '{"query": "BGP flap"}'}))
        _assert_str_status(KBRetrieveNode().execute({"user_input": ""}))

    def test_resolution_rank_success_and_error(self):
        _assert_str_status(
            ResolutionRankNode().execute(
                {"retrieved_passages": [{"doc_id": "R-1", "source": "runbook", "score": 0.8, "escalation": []}]}
            )
        )
        _assert_str_status(ResolutionRankNode().execute({"retrieved_passages": []}))

    def test_guidance_assemble_success(self):
        _assert_str_status(
            GuidanceAssembleNode().execute(
                {"ranked_resolutions": [{"doc_id": "R-1", "source": "runbook", "steps_text": "..."}], "escalation_path": []}
            )
        )

    def test_post_process_success(self):
        _assert_str_status(GuidanceRenderNode().execute({"guidance": "text"}))
