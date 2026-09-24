# TEL-C2-013 - Framework compliance tests TC-01..TC-08.
# Based on the standard framework-compliance test,
# adapted to this template's real architecture (Cat 2: outer pre/post + GraphNode-wrapped inner nodes).

import os
import re

import pytest
from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_state import AgentState
from framework.schemas.agent_status import AgentStatus
from framework.schemas.invocation_context import InvocationContext
from framework.schemas.trust_level import TrustLevel

from src.nodes import guidance_assemble_node, kb_retrieve_node, post_process_node, pre_process_node, resolution_rank_node
from src.schemas.state import State

_SRC = os.path.join(os.path.dirname(__file__), "..", "..", "src")
TRUST = TrustLevel.INTERNAL.value


def _src_files():
    for root, _d, files in os.walk(_SRC):
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(root, f)


# TC-01 - State is a flat TypedDict extending AgentState, added fields are primitives/JSON-str.
class TestTC01StateContract:
    def test_state_is_typeddict_extending_agent_state(self):
        assert hasattr(State, "__annotations__")
        assert "user_input" in State.__annotations__
        assert set(AgentState.__annotations__).issubset(set(State.__annotations__))

    def test_added_fields_are_declared(self):
        added = [k for k in State.__annotations__ if k not in AgentState.__annotations__]
        assert added, "State must declare agent-specific fields"


# TC-02 - Empty/missing input yields a fail-closed ERROR outcome, no raise.
class TestTC02Validation:
    def test_empty_input_no_raise(self):
        node = pre_process_node.ValidateInputNode()
        out = node.execute({"user_input": ""})
        assert out["status"] == AgentStatus.ERROR.value
        assert out["error_log"]

    def test_missing_query_envelope_no_raise(self):
        node = kb_retrieve_node.KBRetrieveNode()
        out = node.execute({"user_input": ""})
        assert out["status"] == AgentStatus.ERROR.value
        assert out["error_log"]

    def test_no_candidate_passages_no_raise(self):
        node = resolution_rank_node.ResolutionRankNode()
        out = node.execute({"retrieved_passages": []})
        assert out["status"] == AgentStatus.ERROR.value
        assert out["error_log"]


# TC-03 - No JWT / API keys / secrets in src/; no direct os.environ reads.
class TestTC03NoCredentials:
    def test_no_credential_literals(self):
        pat = re.compile(r"(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)")
        offenders = []
        for fp in _src_files():
            with open(fp, encoding="utf-8") as f:
                if pat.search(f.read()):
                    offenders.append(fp)
        assert offenders == []

    def test_no_os_environ_secret_reads(self):
        offenders = []
        for fp in _src_files():
            if fp.endswith(os.path.join("api", "server.py")):
                continue  # entry-point INVOKE_AUTH_TOKEN exception (CLAUDE_AGENT.md §3)
            with open(fp, encoding="utf-8") as f:
                if "os.environ" in f.read():
                    offenders.append(fp)
        assert offenders == []


# TC-04 - InvocationContext is never stored in State after invoke.
class TestTC04ContextIsolation:
    def test_no_invocationcontext_in_state_after_invoke(self):
        from src.graph.graph import Graph

        agent = Graph(config={"top_k": 5, "hybrid_search": True})
        agent.compile()
        ctx = InvocationContext(session_id="tc04", caller_trust_level=TrustLevel.INTERNAL, caller_id="noc-tc04")
        result = agent.invoke("BGP flap on core router, how do I resolve it?", ctx=ctx)
        for v in result.values():
            assert not isinstance(v, InvocationContext)

    def test_from_state_available(self):
        assert hasattr(InvocationContext, "from_state")


# TC-05 - Domain events: every node under src/nodes/ emits >=1 domain event on
# its execute() path, and no node re-emits a framework backbone lifecycle event.
class TestTC05Audit:
    def test_pre_process_emits_domain_event(self, monkeypatch):
        events = []
        monkeypatch.setattr(pre_process_node, "emit_trace_event", lambda e, p, s: events.append(e))
        out = pre_process_node.ValidateInputNode().execute({"user_input": "BGP flap"})
        assert out["status"] == AgentStatus.SUCCESS.value
        assert "incident_query_validated" in events

    def test_guidance_assemble_emits_domain_event(self, monkeypatch):
        events = []
        monkeypatch.setattr(guidance_assemble_node, "emit_trace_event", lambda e, p, s: events.append(e))
        out = guidance_assemble_node.GuidanceAssembleNode().execute(
            {"ranked_resolutions": [{"doc_id": "R-1", "source": "runbook", "steps_text": "..."}], "escalation_path": []}
        )
        assert out["status"] == AgentStatus.SUCCESS.value
        assert "incident_guidance_assembled" in events

    def test_source_has_no_backbone_events(self):
        pat = re.compile(r'emit_trace_event\(\s*["\'](node_start|node_complete|node_error|node_skip)["\']')
        offenders = []
        for fp in _src_files():
            with open(fp, encoding="utf-8") as f:
                if pat.search(f.read()):
                    offenders.append(fp)
        assert offenders == []


# TC-06 / TC-07 - see tests/unit/test_framework_compliance_tc06_tc07.py (scaffold exact-name
# file; @final S-2/S-3 gate enforcement is generic, not template-specific).
class TestTC0607ExtraHooksOverridable:
    def test_extra_input_hook_is_overridable(self):
        assert pre_process_node.ValidateInputNode._extra_security_gate_input is not FunctionNode._extra_security_gate_input

    def test_output_gate_blocks_credentials(self):
        # The @final S-3 credential scan actually fires (not vacuous): a
        # credential in the result is blocked, never returned as-is.
        node = post_process_node.GuidanceRenderNode()
        with pytest.raises(Exception):
            node._security_gate_output({"formatted_output": "token AKIAIOSFODNN7EXAMPLE leaked"})


# TC-08 - required_trust_level enforced: insufficient trust -> ERROR state, no raise.
class TestTC08TrustGate:
    def test_declared_trust_levels_valid(self):
        for cls in (
            pre_process_node.ValidateInputNode,
            kb_retrieve_node.KBRetrieveNode,
            resolution_rank_node.ResolutionRankNode,
            guidance_assemble_node.GuidanceAssembleNode,
            post_process_node.GuidanceRenderNode,
        ):
            assert cls.required_trust_level in (TrustLevel.ANONYMOUS, TrustLevel.VERIFIED_EXTERNAL, TrustLevel.INTERNAL)

    def test_insufficient_trust_returns_error(self):
        node = pre_process_node.ValidateInputNode()
        out = node({"caller_trust_level": TrustLevel.ANONYMOUS.value, "user_input": "BGP flap on core router"})
        assert str(out.get("status")).lower().endswith("error")

    def test_sufficient_trust_succeeds(self):
        node = pre_process_node.ValidateInputNode()
        out = node({"caller_trust_level": TRUST, "user_input": "BGP flap on core router"})
        assert out["status"] == AgentStatus.SUCCESS.value
        assert out["validated_query"] == "BGP flap on core router"
