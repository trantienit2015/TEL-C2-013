"""AgentCore Platform v1.0 — TEL-C2-013 state schema."""

# ADR-005: State must be a flat TypedDict — never Pydantic BaseModel.
# LangGraph checkpoints use msgpack serialization; Pydantic objects
# cause silent corruption. Extend AgentState with agent-specific
# fields only. Do NOT add credentials, secrets, or Pydantic models.

from typing import NotRequired

from framework.schemas.agent_state import AgentState


# Type-check note: the wheel ships no py.typed, so mypy resolves AgentState to Any
# and reports every NotRequired below as valid-type. The fields are correct (the state
# contract requires NotRequired) -- the report is a packaging artifact, suppressed per field.
# Drop these ignores once the wheel ships py.typed.
class State(AgentState):
    """Telecom network-incident KB Q&A state.

    Shared fields (user_input, status, session_id, node_history, error_log,
    validated_input, hitl_*, etc.) inherited from AgentState. Only
    incident-QA-specific fields below — flat, JSON-serializable primitives only.
    """

    # pre_process (ValidateInput) output
    validated_query: NotRequired[str]  # type: ignore[valid-type]
    enriched_context: NotRequired[dict]  # type: ignore[valid-type]

    # inner: KBRetrieve
    retrieved_passages: NotRequired[list[dict]]  # type: ignore[valid-type]

    # inner: ResolutionRank
    ranked_resolutions: NotRequired[list[dict]]  # type: ignore[valid-type]

    # inner: GuidanceAssemble (S-3 output gate)
    guidance: NotRequired[str]  # type: ignore[valid-type]
    escalation_path: NotRequired[list[str]]  # type: ignore[valid-type]
    citations: NotRequired[list[str]]  # type: ignore[valid-type]
