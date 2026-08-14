# Agent execution: practical concept map

## What makes this system agentic

A plain chatbot generates text directly. This agent can interpret a request,
choose a function tool, build structured arguments, observe the tool response,
and then generate a concise grounded reply.

## Execution sequence

1. The backend creates an ephemeral ADK session for the request.
2. `Runner.run_async()` adds the user message to the session and invokes the
   single `product_finder_agent`.
3. Gemini interprets the request and emits a `find_products` function call.
4. ADK executes the Python function tool.
5. The tool validates the arguments through `ProductFilters`.
6. `search_products()` applies category, price, and optional text comparisons.
7. The tool returns structured products from the supplied JSON catalogue.
8. ADK emits a function-response event containing the authoritative result.
9. Gemini produces a short final message grounded in that result.
10. `ProductAgentRuntime` returns both the final message and the captured tool
    output. The future API and frontend use the tool output for product cards.

## Responsibility boundary

| Component | May do | Must not do |
|---|---|---|
| Gemini through ADK | Interpret wording and select filter arguments | Invent products or decide numeric matches |
| Function tool | Validate inputs and call the search service | Generate catalogue facts |
| Product service | Perform exact deterministic comparisons | Interpret open-ended natural language |
| JSON catalogue | Provide product facts | Change during a request |
| Frontend | Render structured products | Parse product facts from conversational prose |

## Session decision

The prototype uses `InMemorySessionService`, as documented by Google ADK. Each
API request will initially receive a new ephemeral session. This is enough for
the assignment's independent search examples and avoids adding a database or
user identity system. Persistent multi-turn history would require a deliberate
session identifier and durable session service, neither of which the PDF asks
for.

## Failure behavior

- Invalid tool arguments return a safe structured error.
- A result with zero matches remains a valid successful search.
- If the agent does not call the required tool, the runtime raises an explicit
  error instead of trusting ungrounded generated text.
- Missing or invalid Google credentials are handled at the future API boundary;
  credentials never belong in the frontend or repository.

## Current verified versions

- Google ADK installed and import-tested locally: `2.7.0`
- Default model: `gemini-3.6-flash` (configurable through environment)

The model is configurable because model availability changes faster than the
application's business logic.
