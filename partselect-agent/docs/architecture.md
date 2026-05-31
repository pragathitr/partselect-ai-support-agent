# Architecture

This project implements a scoped commerce-support agent for PartSelect refrigerator and dishwasher parts. The core design goal is to combine an LLM chat experience with deterministic tools, so the assistant can be conversational without inventing part numbers, compatibility results, installation steps, or order status.

## Goals

- Stay focused on refrigerator and dishwasher parts.
- Give accurate product and compatibility answers from structured data.
- Support broad customer workflows: find a part, check fit, troubleshoot symptoms, install a part, and track an order.
- Make the system easy to extend to more appliance types.
- Make agent behavior inspectable through tests and streaming UI events.
- Keep user messages out of stream URLs and require lightweight email verification for order lookup.

## Request Flow

```text
User message
  -> supervisor
  -> specialist
  -> tool_node, if tools are requested
  -> specialist, with tool results
  -> validator
  -> final answer
```

Out-of-scope questions take a shorter path:

```text
User message
  -> supervisor
  -> decline
  -> final answer
```

## Backend Components

### FastAPI

`backend/main.py` creates the app, initializes persistence on startup, enables local frontend CORS, and mounts the API router.

Primary endpoints:

- `POST /api/chat`: blocking response for a full agent turn.
- `POST /api/chat/stream-session`: stores the user message server-side and returns an opaque stream token.
- `GET /api/chat/stream`: Server-Sent Events stream with one event per graph node, addressed by stream token.
- `GET /api/conversations`: list persisted conversations.
- `GET /api/conversations/{conversation_id}`: load a prior conversation.
- `DELETE /api/conversations/{conversation_id}`: delete a conversation.

When `APP_API_KEY` is configured, chat, stream-session creation, and conversation endpoints require `X-API-Key`. The SSE endpoint itself uses a one-time opaque stream token because browser `EventSource` cannot send custom headers.

### LangGraph

`backend/agent/graph.py` defines the orchestration graph.

- `supervisor`: classifies the request as refrigerator, dishwasher, unknown, or out-of-scope. It also extracts a model number when present.
- `decline`: returns a focused refusal for unsupported appliance types or unrelated questions.
- `specialist`: loads the appliance-specific YAML prompt and calls the model with tools bound.
- `tool_node`: executes LangChain tool calls against deterministic backend functions.
- `validator`: reviews the final answer for safety or clearly wrong product claims.

This separates routing, domain expertise, tool execution, and safety review instead of asking one prompt to do everything.

### Tools

The specialist model can call these tools:

- `search_parts_tool`: keyword search across part name, description, and OEM number.
- `get_part_detail_tool`: exact lookup by PartSelect number or OEM number.
- `check_compatibility_tool`: verifies whether a part fits a model.
- `get_compatible_models_tool`: lists models known to fit a part.
- `list_symptoms_tool`: discovers valid symptom IDs and descriptions for an appliance type.
- `diagnose_symptom_tool`: maps a known-valid symptom ID to ranked repair parts, optionally filtered by model.
- `get_install_guide_tool`: returns deterministic installation steps.
- `search_repair_articles_tool`: semantic search over repair article excerpts.
- `get_order_status_tool`: returns mock order status, tracking, and delivery date after order ID and email match.
- `get_cart_deep_link_tool`: returns a mock PartSelect cart handoff URL for a part and quantity.

The most important design choice is that product, compatibility, order, and install facts come from tools rather than the model's memory.

Cart support is implemented as a handoff link rather than real cart mutation. This closes the transaction-support loop for the case study while avoiding fake checkout state or payment handling without a real PartSelect commerce backend.

Symptom diagnosis uses a two-tool pattern. The model first calls `list_symptoms_tool` to discover catalog-backed symptom IDs, then calls `diagnose_symptom_tool` with a known-valid ID. This avoids hardcoding long symptom lists in tool descriptions and gives a cleaner extension path as more categories and symptoms are added.

## Data Layer

SQLite stores structured commerce and support data:

- appliance categories;
- parts;
- models;
- compatibility edges;
- symptoms;
- symptom-to-part fix rankings;
- installation guides;
- conversations and messages;
- mock orders with customer email verification.

Chroma stores repair article chunks for semantic troubleshooting. Structured catalog operations remain in SQLite so exact queries, compatibility checks, and installation guides stay deterministic.

## Frontend

The frontend is a Create React App chat interface. It uses the provided starter direction as a foundation and extends it with PartSelect-specific support workflows.

The UI listens to streamed graph events:

- supervisor events display detected model/appliance context;
- specialist events display final text or lookup status;
- tool events create structured cards;
- validator events display pass/warn status or safety escalation;
- done events store the conversation ID for multi-turn continuity.

The frontend creates stream sessions with `POST /api/chat/stream-session`, then opens `EventSource` with only the returned stream token in the URL. This prevents the customer's full message from being stored in browser history or server access logs as a query parameter.

Structured cards make tool results visible and actionable:

- product cards for part details, price, stock, brand, and OEM number;
- compatibility badges for fit checks;
- installation checklists with tools and safety notes;
- troubleshooting cards for ranked likely fixes;
- validator and escalation components for trust and safety feedback.

## Scope Control

The agent is intentionally constrained to:

- refrigerator parts, symptoms, compatibility, and installation;
- dishwasher parts, symptoms, compatibility, and installation;
- PartSelect order tracking.

The supervisor routes unsupported appliances, small talk, and unrelated questions to the decline node before a specialist model is called. The specialist fallback prompt repeats the same scope rule, and the validator can replace unsafe answers with an escalation message.

## Extensibility

The data model is designed around appliance categories. A new category can be added by:

1. adding a category row;
2. adding parts, models, compatibility edges, symptoms, and guides;
3. adding a specialist YAML file;
4. updating the supervisor scope rules to activate that category.

The existing tools work across appliance categories because they query category slugs and model/part relationships instead of hard-coding refrigerator or dishwasher behavior in every function.

## Safety And Accuracy

Accuracy controls:

- Compatibility answers should call `check_compatibility_tool`.
- Product details come from seeded SQLite data.
- Install instructions come from deterministic guide rows.
- Troubleshooting combines structured symptom mappings with RAG article excerpts.
- Order tracking requires both order ID and customer email.

Safety controls:

- Out-of-scope routing avoids unsupported advice.
- Validator verdicts are `pass`, `warn`, or `escalate`.
- Escalation replaces the answer for hazards such as electrical burning, flooding, or gas/refrigerant leak concerns.

Security controls:

- Optional shared API-key gate for demo deployments.
- One-time stream tokens instead of raw chat text in SSE URLs.
- Sanitized frontend markdown rendering.
- Parameterized SQL queries.
- Clean SSE `error` events for provider or tool failures.

Production hardening would replace shared API-key auth with per-user authentication, enforce conversation ownership, add rate limits, and verify order access through account identity or stronger customer verification.

## Evaluation

The test suite uses mocked LLM calls so routing and behavior can be checked without external API calls. Scenario evals cover:

- unsupported appliances and unrelated questions;
- refrigerator part lookup, install, compatibility, and symptoms;
- dishwasher part lookup, install, compatibility, and symptoms;
- order tracking;
- safety escalation.

This gives confidence in the graph shape and tool contracts while keeping local tests fast and repeatable.

Test coverage is organized into:

- unit/data tests for deterministic tools, SQLite queries, and Chroma retrieval with mocked embeddings;
- graph/system tests for LangGraph routing, specialist/tool loops, validator behavior, and scoped declines;
- API integration-style tests for FastAPI chat, stream-session/SSE behavior, optional API-key gating, and conversation persistence;
- evaluation tests with 25 scenario cases across customer workflows and safety boundaries.

## Tradeoffs

- The seeded catalog is intentionally small for the case study, but the schema is shaped like a larger commerce catalog.
- The validator improves safety, but high-stakes repairs should still route customers to support or a licensed technician.
- RAG is used for open-ended repair articles, while exact catalog facts stay in SQLite to reduce hallucination risk.
- The frontend is a focused chat experience rather than a complete PartSelect storefront; product cards are designed to show how transactional affordances could be added.

## Production Scalability

SQLite is intentional for the case study because it makes the prototype reproducible and keeps deterministic lookups simple. In production, SQLite would not be the source of truth for a changing commerce catalog.

The same tool interface could connect to:

- PartSelect catalog and order services for live product, compatibility, pricing, inventory, cart, and order data;
- a production relational database such as PostgreSQL or MySQL for structured data and operational persistence;
- a search service such as OpenSearch, Elasticsearch, Algolia, or an existing commerce search API for product discovery;
- Redis or another shared cache for short-lived stream-token, session, rate-limit, and hot-lookup state;
- a managed vector/search layer for repair article retrieval.

The scalable piece is the tool abstraction. The agent calls stable tools such as `search_parts`, `check_compatibility`, `diagnose_symptom`, and `get_order_status`, while the underlying data source can evolve without changing the chat orchestration.
