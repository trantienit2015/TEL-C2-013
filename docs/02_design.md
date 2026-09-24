# Template Design Specification — TEL-C2-013

## Position in AgentCore Architecture

- **L1 Base**: `AgentBaseGraph` (Level 1 direct inheritance). `RAGAgent` (the vector-RAG pattern) is the
  pattern reference, NOT an inheritance target — L2 inheritance is retired.
- **Agent Class**: `IncidentKBQAAgent` (alias `Graph`) in `src/graph/graph.py`.
- **Category**: Cat 2 — outer `AgentBaseGraph` backbone + a `GraphNode` in the `main` slot
  wrapping an inner `BaseGraph` Q&A workflow.

## Architecture (Cat 2 — outer + inner subgraph)

```
OUTER (AgentBaseGraph — src/graph/graph.py):
  initialize → pre_process(ValidateInputNode) → main(IncidentQAGraphNode)
            → post_process(GuidanceRenderNode) → finalize

INNER (BaseGraph — src/graph/domain_workflow_graph.py), via IncidentQAGraphNode:
  START → kb_retrieve → resolution_rank → guidance_assemble → END
```

Data flow: outer `pre_process` validates + serializes `{query}` into `validated_input` (JSON
string). `IncidentQAGraphNode.extract_input()` returns that string; the inner first node
(`KBRetrieveNode`) `json.loads` it. Config (retriever, top_k, hybrid_search) reaches the
inner graph via `_parent_config()`. `merge_output()` maps inner result fields back to outer.

## Node Set

| Slot / Step | Node | Role |
|---|---|---|
| outer pre_process | `ValidateInputNode` | S-2 input scan, reject empty, serialize `validated_input` |
| inner step 1 | `KBRetrieveNode` | hybrid retrieval (e5 + BM25 for device/error codes) over runbook KB + ServiceNow ITSM export |
| inner step 2 | `ResolutionRankNode` | **deterministic score-sort via the `resolution_ranker` Tool (no LLM)** + escalation-path mapping |
| inner step 3 (S-3 gate) | `GuidanceAssembleNode` | assemble ranked guidance + escalation path with source citation; `emit_trace_event` (S-4) |
| outer post_process | `GuidanceRenderNode` | assemble guidance payload + disclaimer |

### ResolutionRankNode — node-level Agent-vs-Tool decision

Per the architect note on the scaffold issue, the implementer must declare whether
`ResolutionRankNode` is a deterministic Tool or an in-graph LLM node. **Decision: deterministic
Tool.** Ranking is a pure score-sort (retrieval score × source weight) with no LLM, implemented
in `src/services/resolution_ranker.py` (`rank_resolutions`, `merge_escalation_path`) and called
from the node. No State, no side effects — a Tool, not an Agent.

## State Schema (`src/schemas/state.py`)

`class State(AgentState)` — flat TypedDict. Agent-specific fields: `validated_query`,
`retrieved_passages`, `ranked_resolutions`, `guidance`, `escalation_path`, `citations`. No
Pydantic / dataclass / credentials in state.

## Security (5-layer)

- **S-1** Trust Gate: `required_trust_level: INTERNAL` per-agent in `config/agent.yaml`
  (internal carrier NOC KB — INTERNAL callers only).
- **S-2** domain input check: input scan / empty-reject in `ValidateInputNode`.
- **S-3** Secret Isolation: `bound_secrets()` + `secrets_factory()` + `provision_secrets()`
  at the entry point (`src/api/server.py`); never `os.environ`. The output assembly gate
  (`GuidanceAssembleNode`) is node logic, not a framework S-* gate.
- **S-4** Audit Logging: `emit_trace_event()` in `GuidanceAssembleNode`.
- **S-5** Credential Scan: framework `__init_subclass__` at import time.

## Dependencies

`pyproject [project].dependencies = []` — framework resolves via the scaffold CI include.
The embedding model + retriever are injected via `config`; a deterministic keyword/code
overlap baseline runs when none is injected (no hard dependency). Ranking has no LLM dependency.
