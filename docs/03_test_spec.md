# Test Specification — TEL-C2-013

## Test Strategy

- Test types: Unit (per node) + Integration (full graph compile + invoke) + Proof-of-Boundary.
- Coverage: each node has ≥1 success + ≥1 error/edge case; ≥1 full-graph integration test.
- Retriever uses the deterministic KB baseline; ranking is a deterministic Tool — no external service.

## Unit Tests

| File | Node | Cases |
|---|---|---|
| `tests/unit/test_pre_process_node.py` | `ValidateInputNode` | success serializes payload; empty → ERROR; execute() signature |
| `tests/unit/test_inner_nodes.py` | `KBRetrieveNode` | retrieves passages; invalid payload → ERROR |
| | `ResolutionRankNode` | runbook outranks ITSM; escalation path merged; no passages → ERROR |
| | `GuidanceAssembleNode` | guidance + citation; empty ranked still produces guidance |
| `tests/unit/test_post_process_node.py` | `GuidanceRenderNode` | assembles payload + disclaimer; defaults |

## Integration Tests (`tests/integration/test_graph.py`)

- `test_full_pipeline_success` — incident query → SUCCESS, `node_history ≥ 5`, guidance + citation + disclaimer.
- `test_empty_input_terminates` — empty input terminates cleanly (rejected at ValidateInput).
- `test_escalation_path_surfaces` — incident query → escalation path present.

## Proof-of-Boundary (`tests/proof_of_boundary/`)

| PB | File | Boundary |
|---|---|---|
| PB-4 | `test_import_isolation.py` | no `agenticstar` / platform-layer imports in `src/` |
| PB-2/PB-5 | `test_state_safety.py` | State has no Pydantic / InvocationContext / credential fields |

## Framework-Compliance Mapping

- TC-01 State contract → `test_state_safety.py`
- TC-02 Error path → empty / invalid / no-passages error cases per node
- TC-04 Secret access (S-3) → secrets provisioned via `bound_secrets`/`secrets_factory` (no `os.environ`)
- TC-05 Audit (S-4) → `emit_trace_event` in `GuidanceAssembleNode`
- TC-07 No `_invoke_impl` → asserted in `test_pre_process_node.py`
- TC-08 S-1 trust gate → `required_trust_level: INTERNAL` (internal NOC KB)
- PB-6 full pipeline → `test_full_pipeline_success`
