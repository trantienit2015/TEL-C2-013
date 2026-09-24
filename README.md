# TEL-C2-013 — Telecom Network Incident Knowledge Base Q&A Agent

> **Category**: Cat 2 (orchestrates multiple steps to accomplish a specific use case)
> **Industry**: TEL

## Overview

Helps network operations engineers find resolution steps for a network incident, such as a
BGP session flap, a cell site outage or high CPU on the packet core. Input is a plain-text
incident description; empty input is rejected. Optional request context may carry incident
metadata, and a request whose context contains a credential-shaped value (API key, JWT, AWS
key or Bearer token) is rejected.

Candidate passages are retrieved from runbooks and past incident tickets. Without an injected
retriever the agent uses a small bundled sample knowledge base of five Japanese-language
entries with keyword and device/error-code scoring; replace it with your own runbook and
ticket corpus through a retriever supplied in the graph configuration. The passages are then
ranked by retrieval score weighted by source (runbooks above past tickets), and an escalation
path is merged from the ranked entries.

The output contains the guidance text (a recommended resolution, up to two alternatives and
the escalation path), the ranked resolutions, the escalation path, citations to the source
documents and a fixed disclaimer to verify against current network state before acting. No
language model is used; every step is deterministic. All outer nodes require the caller to be
at the highest trust level (INTERNAL).

This is an agent template built with the **AGENTIC STAR** development platform and the
**AgentCore Framework**. It is intended to be taken as a starting point: fork it, adapt it to
your own data and policies, and run it inside your own AGENTIC STAR deployment.

## Requirements

**This template does not run standalone.** It requires:

| Requirement | Notes |
|---|---|
| **AGENTIC STAR platform** | The agent connects to the platform at start-up. Without it, start-up fails immediately (see *Behaviour without the platform* below). Deployment guides and API documentation: [AGENTIC STAR Developers](https://developers.fd.agenticstar.tm.softbank.jp/) |
| **AgentCore Framework** (`agenticstar-agentcore`) | Installed from PyPI as a dependency. |
| Python | 3.11 or later |

```bash
pip install -e .
```

### Behaviour without the platform

The framework is designed to run **only** on AGENTIC STAR. There is no fallback or degraded
mode. If the platform is unreachable or the SDK version does not match, the agent raises
`PlatformRequired` during graph compile / start-up preflight rather than starting in a partially
working state. This is intentional — a half-running agent is worse than one that refuses to start.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m pytest tests/ -v
```

Tests run without a platform connection. Running the agent itself does not.

## Project Structure

```
src/          agent implementation (nodes, services, schemas)
tests/        unit, integration and boundary tests
config/       agent configuration
docs/         design and test specification
```

See `docs/02_design.md` for the design and `docs/03_test_spec.md` for the test specification.

## Customising

1. Adjust `config/` for your own environment and policies.
2. Replace the knowledge sources and sample data with your own.
3. Review the node implementations under `src/nodes/` for domain-specific logic.
4. Re-run the test suite.

## License

MIT — see [LICENSE](LICENSE).

## Status of this repository

This template is published **as is**, by its individual author, under the MIT license. It carries
**no warranty and no support commitment**, and no organisation stands behind its behaviour or
fitness for any purpose. Issues and pull requests may or may not receive a response; that is at
the sole discretion of the repository owner.
