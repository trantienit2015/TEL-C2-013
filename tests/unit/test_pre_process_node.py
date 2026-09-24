# TEL-C2-013 — Unit Tests: ValidateInputNode (pre_process)

import inspect
import json

from framework.schemas.agent_status import AgentStatus
from src.nodes.pre_process_node import ValidateInputNode


class TestValidateInputNode:
    def setup_method(self):
        self.node = ValidateInputNode()

    def test_success_serializes_payload(self):
        state = {"user_input": "BGP セッションが flap しています", "input_context": {}, "node_history": [], "error_log": []}
        result = self.node.execute(state)
        assert result["status"] == AgentStatus.SUCCESS
        payload = json.loads(result["validated_input"])
        assert payload["query"]
        assert result["validated_query"]

    def test_empty_input_errors(self):
        result = self.node.execute({"user_input": "  ", "node_history": [], "error_log": []})
        assert result["status"] == AgentStatus.ERROR

    def test_execute_signature(self):
        params = list(inspect.signature(ValidateInputNode.execute).parameters.keys())
        assert params[1] == "state"
        assert "_invoke_impl" not in ValidateInputNode.__dict__

    def test_extra_security_gate_input_blocks_credential_shaped_context(self):
        state = {
            "user_input": "BGP flap",
            "input_context": {"incident_context": "token: AKIAIOSFODNN7EXAMPLE"},
            "node_history": [],
            "error_log": [],
        }
        out = self.node._extra_security_gate_input(state)
        assert out["status"] == AgentStatus.ERROR
        assert out["error_log"]

    def test_extra_security_gate_input_passthrough_when_clean(self):
        state = {
            "user_input": "BGP flap",
            "input_context": {"incident_context": "cell outage in Tokyo area"},
            "node_history": [],
            "error_log": [],
        }
        out = self.node._extra_security_gate_input(state)
        assert out is state
