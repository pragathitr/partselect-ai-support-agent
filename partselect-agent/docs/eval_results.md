# Eval Results

Local backend test run:

```text
python -m pytest
Run this locally after the final dependency/database changes.
```

Scenario eval run:

```text
python -m pytest backend/tests/eval/test_scenarios.py
25 passed
```

## Coverage

The test suite is split into:

- unit/data tests for deterministic tools, SQLite queries, Chroma retrieval, and order verification;
- graph/system tests for supervisor routing, tool loops, validator behavior, and declines;
- API integration-style tests for chat, stream-session/SSE, auth gating, and conversation persistence;
- scenario evals with mocked LLM outputs.

The scenario suite covers:

- 7 out-of-scope requests, including unsupported appliances, unrelated topics, and small talk.
- 5 refrigerator workflows, including symptom diagnosis, compatibility, product lookup, and installation.
- 5 dishwasher workflows, including draining, latch lookup, installation, compatibility, and residue troubleshooting.
- 3 compatibility checks, including OEM cross-reference behavior.
- 2 order tracking flows, including email-verified lookup behavior in the tool layer.
- 3 safety escalation cases for gas/refrigerant concern, electrical burning, and flooding.

## Notes

LLM calls are mocked in the scenario evals. This keeps the suite deterministic and focused on graph routing, state updates, validator handling, and response-shape expectations. Tool and data-layer tests separately cover SQLite queries, Chroma retrieval behavior, and API endpoints.

The eval text is aligned with the seeded catalog, including:

- `PS11752391` as the refrigerator ice maker assembly.
- `PS11701542` as the EveryDrop water and ice filter.
- `PS11752778` as the refrigerator door shelf bin.
- `PS11756967` as the dishwasher door latch.
- `12345` as the sample shipped order, verified with `demo@example.com`.
