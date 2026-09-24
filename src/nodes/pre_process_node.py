"""AgentCore Platform v1.0 — TEL-C2-013 outer pre_process node (ValidateInput).

S-1 trust gate is declared explicitly (outer node, matches agent.yaml
required_trust_level). S-2 PII/credential scanning of standard fields is the
framework @final _security_gate_input(); the _extra_security_gate_input()
hook below adds a domain check on input_context, which is tenant-supplied
metadata not covered by the standard-field scan.
"""

import json
import re
from typing import Any, ClassVar

from framework.nodes.function_node import FunctionNode
from framework.schemas.agent_status import AgentStatus
from framework.schemas.trust_level import TrustLevel
from shared.utils.audit_logger import emit_trace_event

# S-2 domain check: input_context (incident_context) is tenant-supplied
# free-form metadata outside the framework's standard-field PII scan; reject
# credential-shaped values before they are echoed into enriched_context.
_CREDENTIAL_PATTERN = re.compile(
    r"(sk-[A-Za-z0-9]{16,}|eyJ[A-Za-z0-9_-]{10,}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._-]{10,})"
)


class ValidateInputNode(FunctionNode):
    """Outer pre_process: S-1 trust (framework), reject empty/invalid input, normalize the
    incident-resolution query, and serialize a JSON payload into ``validated_input`` for the
    inner KB-Q&A subgraph.
    """

    # S-1: outer node receiving caller input first — matches agent.yaml required_trust_level.
    required_trust_level: ClassVar[TrustLevel] = TrustLevel.INTERNAL

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        user_input = state.get("user_input", "")
        input_context = state.get("input_context", {})  # read-only

        if not user_input or not user_input.strip():
            emit_trace_event(
                "incident_query_rejected",
                {"correlation_id": state.get("correlation_id"), "reason": "empty_query"},
                state,
            )
            return {
                "status": AgentStatus.ERROR.value,
                "error_log": ["ValidateInputNode: incident query (user_input) is empty or missing"],
            }

        query = " ".join(user_input.split())
        payload = {"query": query}

        emit_trace_event(
            "incident_query_validated",
            {"correlation_id": state.get("correlation_id"), "query_length": len(query)},
            state,
        )
        return {
            "validated_query": query,
            "validated_input": json.dumps(payload, ensure_ascii=False),
            "enriched_context": {
                "source": "tel-c2-013",
                "incident_context": input_context.get("incident_context", ""),
            },
            "status": AgentStatus.SUCCESS.value,
        }

    def _extra_security_gate_input(self, state: dict[str, Any]) -> dict[str, Any]:
        """S-2 domain check: reject if input_context embeds a credential-shaped
        string. Runs automatically BEFORE execute(); must always return a dict
        and must never raise or be called manually.
        """
        input_context = state.get("input_context")
        if isinstance(input_context, dict):
            flattened = json.dumps(input_context, ensure_ascii=False)
            if _CREDENTIAL_PATTERN.search(flattened):
                return {
                    "status": AgentStatus.ERROR.value,
                    "error_log": ["S-2: credential-shaped value detected in input_context"],
                }
        return state
