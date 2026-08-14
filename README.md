# Product Finder ADK Agent

A lightweight Product Finder AI Agent built from the supplied 13-product JSON catalogue. The system will use one Google Agent Development Kit (ADK) agent to interpret natural-language requests and deterministic Python code to filter products.

## Current status

Phases 0-4 are complete:

- Assignment requirements verified against the original PDF
- Repository foundation created
- Product catalogue reconstructed and validated
- Typed product, filter, and search-result contracts added
- Deterministic category, price, and optional text filtering implemented
- Boundary and validation tests added
- No agent, API, frontend, or deployment code has been added yet

## Source-of-truth requirement matrix

| ID | Requirement from assignment | Classification | Planned implementation | Verification |
|---|---|---|---|---|
| R1 | Use the supplied JSON dataset | Mandatory | `backend/app/data/products.json` | Catalogue validation |
| R2 | Build a lightweight Product Finder AI Agent | Mandatory | One Google ADK agent | Agent integration evaluation |
| R3 | Understand natural-language product requests | Mandatory | Gemini through Google ADK | Natural-language query evaluation |
| R4 | Recommend relevant products | Mandatory | Agent calls the deterministic search tool | End-to-end tests |
| R5 | Filter deterministically by category | Mandatory | Python search service | Unit tests |
| R6 | Filter deterministically by price greater than a value | Mandatory | Python search service | Boundary unit tests |
| R7 | Filter deterministically by price less than a value | Mandatory | Python search service | Boundary unit tests |
| R8 | Filter deterministically by price equal to a value | Mandatory | Python search service | Exact-price unit test |
| R9 | Support combined category and price filtering | Mandatory by example | Python search service | Combined-filter unit test |
| R10 | Use Google Agent Development Kit | Mandatory | Google ADK backend integration | Code inspection and live demo |
| R11 | Use a simple custom chatbot-style frontend | Mandatory | Minimal React UI | Browser verification |
| R12 | Connect the frontend directly to hosted Cloud Run | Mandatory | Configured backend URL | Browser network inspection |
| R13 | Render title, price, description, and image | Mandatory | Product cards | UI verification |
| R14 | Package the backend in Docker | Mandatory | Backend Dockerfile | Local container test |
| R15 | Deploy the backend as a serverless service on GCP Cloud Run | Mandatory | Cloud Run service | HTTPS health and chat checks |
| R16 | Demonstrate the live frontend-to-Cloud-Run connection | Mandatory | Deployed end-to-end application | Walkthrough |
| R17 | Keep implementation feasible within 3-5 hours and explain the code | Constraint | Small, traceable architecture | Demo rehearsal |
| P1 | Do not use embeddings | Explicitly prohibited | No embedding dependency or code | Dependency/code audit |
| P2 | Do not use RAG | Explicitly prohibited | No retrieval pipeline or vector store | Architecture audit |
| P3 | Do not use multiple agents | Explicitly prohibited | Exactly one ADK agent | Agent configuration audit |
| P4 | Do not use ADK's built-in web UI | Explicitly prohibited | Custom frontend | UI/code inspection |

Features such as a database, authentication, checkout, accounts, LangGraph, Kubernetes, recommendation models, and an admin dashboard are not prohibited by the PDF. They are intentionally excluded because they are not needed for this fixed-catalogue prototype.

## Planned architecture

```text
User -> custom React UI -> FastAPI backend on Cloud Run
                            -> one Google ADK agent
                            -> deterministic Python search tool
                            -> supplied products.json
```

The agent interprets intent and constructs tool arguments. Python remains authoritative for category and numeric price comparisons. Product facts always come from the supplied catalogue.

## Repository structure

```text
backend/
  app/
    data/products.json
    models.py
    product_service.py
  scripts/validate_catalogue.py
  tests/
frontend/
docs/
```

## Validate the catalogue

From the repository root:

```bash
python3 backend/scripts/validate_catalogue.py
```

Expected output:

```text
Catalogue valid: 13 products, IDs 0-12, 4 categories.
```

## Run backend tests

From the repository root:

```bash
python3 -m unittest discover -s backend/tests -v
```

The deterministic layer supports:

| Operator | Meaning | Natural-language example |
|---|---|---|
| `lt` | Less than | under $50 |
| `lte` | Less than or equal | at most $5 |
| `gt` | Greater than | over $200 |
| `gte` | Greater than or equal | at least $49 |
| `eq` | Exactly equal | exactly $49 |

The PDF explicitly requires less than, greater than, and equal. Inclusive operators are a small extension needed to represent common natural-language boundaries without letting the LLM perform numeric comparisons.

## Next phase

Learn the Google ADK execution model, verify the current official API, and connect exactly one agent to this tested search service.
