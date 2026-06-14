# PartSelect Chat Agent

Chat assistant for refrigerator and dishwasher parts on PartSelect. The agent helps customers find parts, check model compatibility, troubleshoot symptoms, view installation guidance, and track orders while declining questions outside the supported appliance scope.

## What It Does

- Answers refrigerator and dishwasher part questions only.
- Looks up real seeded part data by PartSelect number, OEM number, name, or description.
- Checks whether a part fits a customer appliance model before recommending it.
- Creates mock cart handoff links for parts the customer wants to buy.
- Diagnoses common symptoms such as ice maker failure, dishwasher not draining, leaks, and poor cleaning.
- Discovers valid symptom IDs from the catalog before running diagnosis, so symptom support can grow without stuffing IDs into prompts.
- Returns deterministic installation steps for supported parts.
- Streams intermediate agent steps through opaque stream tokens so user messages are not placed in SSE URLs.
- Persists conversations and supports email-verified order tracking with mock order data.
- Uses a validator pass to catch unsafe or clearly incorrect responses.

## Architecture At A Glance

The backend uses FastAPI plus LangGraph. Each chat turn flows through:

1. `supervisor`: classifies appliance type, extracts model number, and rejects out-of-scope requests.
2. `specialist`: uses refrigerator/dishwasher specialist prompts and bound tools to answer.
3. `tool_node`: executes deterministic catalog, compatibility, symptom discovery, diagnosis, install, RAG, cart handoff, and order tools.
4. `validator`: reviews the final answer and replaces unsafe responses with an escalation message.

This implements Anthropic's orchestrator-workers pattern: a lightweight supervisor routes, a specialist reasons, tools return facts.

Separating routing, domain reasoning, tool execution, and safety review means each component can be tested, replaced, and reasoned about independently.

The frontend is a React chat UI extended with streaming events and structured cards for products, compatibility, installation, troubleshooting, validation, and escalation. It is currently built with Create React App; for production the natural migration is Next.js — SSR, Vercel-native deployment, and API route co-location. The component structure is already organized to make that a straightforward lift.

See [docs/architecture.md](docs/architecture.md) for the full design walkthrough.

## Key Design Decisions

**Supervisor + specialist separation.** A lightweight supervisor (Haiku) classifies scope and extracts model context. A specialist (Sonnet) reasons over the domain task with appliance-specific prompts loaded from YAML. This keeps each prompt bounded — the specialist never needs to know about all appliance types, only its own.

**Deterministic over probabilistic wherever possible.** 
Compatibility checks are structured edge lookups, not LLM inference. Install guides are keyed rows, not RAG. Symptom diagnosis uses a two-tool pattern: list_symptoms discovers catalog-backed IDs, diagnose_symptom runs the lookup. The LLM reasons; the tools return facts.

**Stream tokens over query params.** User messages are never placed in SSE URLs. The frontend POSTs to create a stream session and receives an opaque token, then opens EventSource with only the token. This prevents chat text from appearing in server access logs or browser history.

**SQLite + recursive CTE for multi-hop traversal.** 
Symptom → part → model is a graph relationship. A recursive CTE in SQLite handles the traversal without a second data store, keeping the prototype reproducible with zero external services.

## Tech Stack

- Frontend: React, Create React App, Server-Sent Events, `marked`, `dompurify`.
- Backend: FastAPI, LangGraph, LangChain, Anthropic/OpenAI chat models.
- Data: SQLite for deterministic catalog/order data, Chroma for repair article retrieval.
- Tests: Pytest with mocked LLM calls for graph, API, tools, data layer, and scenario evals.

## Setup

```bash
cd partselect-agent
pip install -e ".[dev]"
cp .env.example .env
```

Fill in the API keys required by your chosen model providers. The default backend configuration uses Anthropic for supervisor/specialist calls and OpenAI for validation and embeddings.

`APP_API_KEY` is optional. When set, protected backend endpoints require `X-API-Key`. For the local React frontend, set the same value as `REACT_APP_API_KEY` in the frontend environment.

Seed local data:

```bash
python -m backend.scripts.seed_db
python -m backend.scripts.build_chroma
```

Run the backend:

```bash
python -m uvicorn backend.main:app --reload
```

Run the frontend in another terminal:

```bash
cd frontend
npm install
npm start
```

The React app proxies `/api/*` requests to `http://localhost:8000`.

## Useful Test Prompts

- `How can I install part number PS11752778?`
- `Is PS11756967 compatible with my WDT780SAEM1 dishwasher?`
- `The ice maker on my Whirlpool WRF555SDFZ fridge is not working. How can I fix it?`
- `What is the status of my order 12345? My email is demo@example.com.`
- `How do I fix my washing machine?`
- `Water is flooding out of the bottom of my dishwasher.`

Seeded demo orders:

- `12345` with `demo@example.com` — shipped, estimated delivery `2026-06-03`
- `12346` with `demo@example.com` — processing, estimated delivery `2026-06-05`
- `12347` with `customer@example.com` — delivered on `2026-05-27`
- `12348` with `shopper@example.com` — shipped, estimated delivery `2026-06-04`
- `12349` with `parts@example.com` — processing, estimated delivery `2026-06-06`

Order tracking can also be tested as a two-turn flow:

```text
I want to track my order. My order number is 12345
```

```text
demo@example.com
```

## Demo Checklist

For a Loom walkthrough, a compact path through the main capabilities is:

1. Ask `How can I install part number PS11752778?` to show deterministic install guidance and checklist UI.
2. Ask `Is PS11756967 compatible with my WDT780SAEM1 dishwasher?` to show compatibility checking.
3. Ask `The ice maker on my Whirlpool WRF555SDFZ fridge is not working. How can I fix it?` to show troubleshooting and part recommendations.
4. Ask `What is the status of my order 12345? My email is demo@example.com.` to show verified transaction/order support.
5. Ask `How do I fix my washing machine?` to show out-of-scope refusal.
6. Ask `Water is flooding out of the bottom of my dishwasher.` to show safety escalation.

## Tests

```bash
python -m pytest
```

The suite includes backend tests across four practical layers:

- Unit/data tests for deterministic tools, SQLite queries, and Chroma retrieval with mocked embeddings.
- Graph/system tests for LangGraph routing, out-of-scope handling, tool loops, and validator behavior.
- API integration-style tests for FastAPI chat, stream-session/SSE, auth gating, and conversation endpoints.
- Evaluation tests with 25 mocked scenarios across in-scope, out-of-scope, compatibility, order, and safety cases.

Useful targeted commands:

```bash
python -m pytest backend/tests/test_tools.py backend/tests/test_data_layer.py
python -m pytest backend/tests/test_graph.py
python -m pytest backend/tests/test_api.py
python -m pytest backend/tests/eval/test_scenarios.py
```

## Troubleshooting

If `uvicorn` is not recognized, run it through Python:

```bash
python -m uvicorn backend.main:app --reload
```

If PowerShell blocks `npm.ps1`, use the Windows command shim:

```bash
npm.cmd install
npm.cmd start
```

If `react-scripts` is not recognized, install frontend dependencies first:

```bash
cd frontend
npm.cmd install
```

If the frontend shows `Sorry, something went wrong. Please try again.`, check the backend terminal traceback. The browser message is intentionally generic; the backend log will show whether the issue is persistence, provider credentials, model configuration, or a tool error.

## Security Notes

The app includes prototype-friendly hardening:

- Optional shared API-key protection through `APP_API_KEY`.
- POST-created stream sessions so chat text is not sent in SSE query strings.
- One-time opaque stream tokens for the EventSource connection.
- Email verification for order lookup.
- Sanitized markdown rendering in the frontend.
- Parameterized SQLite queries.
- Clean SSE `error` events for provider/tool failures.

For production, replace shared API-key auth with real user/session auth, add per-user conversation ownership, rate-limit chat endpoints, and verify order access through account identity or stronger customer verification.

## Extensibility

Adding another appliance type is intended to be data/config led:

1. Insert a new row in `appliance_categories`.
2. Add parts, models, compatibility edges, symptoms, and install guides.
3. Add a specialist YAML file under `backend/config/specialists`.
4. Update the supervisor scope rules when the new category is ready to be public.

The tool layer and frontend cards are generic enough to reuse the same product, compatibility, troubleshooting, and installation surfaces for future categories.

## Production Scalability

SQLite is intentional for the case study: it keeps the prototype 
reproducible with zero external services. In production the same 
tool interface connects to real backends:

- Catalog/order data → PartSelect product and order services
- Structured lookups → production relational DB (Postgres)
- Product search → dedicated search service (Elasticsearch, pgvector)
- Session and stream-token state → Redis with TTLs
- Repair content retrieval → managed vector search
- Auth → per-user sessions replacing the shared API key
