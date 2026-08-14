# Product Finder AI Agent

A lightweight, full-stack Product Finder built with one Google Agent Development Kit (ADK) agent, deterministic Python filtering, FastAPI, React, Docker, and Google Cloud Run.

## Live application

- Frontend: https://product-finder-adk-chintan.netlify.app
- Cloud Run health: https://product-finder-api-688514789228.us-west1.run.app/health
- API documentation: https://product-finder-api-688514789228.us-west1.run.app/docs

## Final status

The assignment implementation is complete:

- The supplied 13-product catalogue is used as the only product source.
- One Google ADK agent interprets natural-language search requests.
- Deterministic Python code performs category and price comparisons.
- Less-than, less-than-or-equal, greater-than, greater-than-or-equal, and exact-price operators are supported.
- Combined category and price filters are supported.
- The custom React frontend renders structured product cards.
- The FastAPI backend is packaged as a non-root Docker container.
- The backend is deployed to Google Cloud Run.
- The frontend is deployed to Netlify and calls Cloud Run directly.
- The Gemini API key is stored in Google Secret Manager and is never sent to the browser.

## Architecture

```text
User
  -> React/Vite frontend on Netlify
  -> POST /api/v1/chat on Cloud Run
  -> FastAPI boundary and request validation
  -> one Google ADK product_finder_agent
  -> find_products structured function tool
  -> deterministic Python filtering
  -> supplied products.json catalogue
  -> structured result returned to React product cards
```

### Deterministic boundary

The LLM is responsible only for understanding the user's wording and converting it into structured tool arguments such as:

```json
{
  "category": "clothing",
  "price_operator": "lt",
  "price_value": 50
}
```

The LLM does not compare prices, filter the catalogue, or invent product facts. The `find_products` tool passes validated arguments to the Python search service, which performs authoritative category and numeric filtering. The frontend renders product details from the structured tool result rather than parsing the agent's prose.

This separation keeps natural-language interpretation flexible while making the returned catalogue results predictable and testable.

## Required examples

| Query | Expected result |
|---|---:|
| `Show me all your clothing products.` | 4 products |
| `What clothing items are available under $50?` | 2 products |
| `Electronics over $200` | 2 products |
| `Products exactly $49` | 1 product |
| `Show furniture` | 0 products |

## Technology stack

### Backend

- Python 3.12
- Google Agent Development Kit
- Gemini 3.5 Flash-Lite
- FastAPI and Uvicorn
- Pydantic validation
- Docker
- Google Cloud Run
- Google Secret Manager
- Artifact Registry and Cloud Build

### Frontend

- React
- Vite
- Custom CSS
- Netlify

## Repository structure

```text
backend/
  Dockerfile
  app/
    data/products.json
    agent.py
    agent_runtime.py
    config.py
    main.py
    models.py
    product_service.py
  scripts/validate_catalogue.py
  tests/
frontend/
  src/
    components/
    App.jsx
    api.js
    styles.css
docs/
```

## Run locally

### 1. Backend

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
```

Add your own Google AI Studio key to `backend/.env`:

```env
GOOGLE_API_KEY=your_key
PRODUCT_AGENT_MODEL=gemini-3.5-flash-lite
ADK_APP_NAME=product_finder
ALLOWED_ORIGINS=http://localhost:5173
```

Never commit `backend/.env`.

Start the API:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Check it:

```bash
curl --fail http://localhost:8000/health
```

### 2. Frontend

In a second terminal:

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Set `VITE_API_URL` in `frontend/.env` to the backend origin. For the local FastAPI command above:

```env
VITE_API_URL=http://localhost:8000
```

## Tests and verification

Run the catalogue validator:

```bash
python3 backend/scripts/validate_catalogue.py
```

Expected output:

```text
Catalogue valid: 13 products, IDs 0-12, 4 categories.
```

Run the backend suite:

```bash
python3 -m unittest discover -s backend/tests -v
```

Final verification completed during development:

- 45 backend tests passed.
- Frontend production build passed.
- Local Docker health and live Gemini requests passed.
- Cloud Run health and live chat requests passed.
- Production Netlify-to-Cloud-Run interaction passed.

The tests cover catalogue integrity, immutable models, price boundaries, combined filters, the single-agent definition, tool output, API validation, safe upstream errors, CORS, and the container contract.

## Docker

Build from the repository root:

```bash
docker build \
  --platform linux/amd64 \
  -f backend/Dockerfile \
  -t product-finder-api:local \
  backend
```

Run with a local, ignored environment file:

```bash
docker run --rm \
  --platform linux/amd64 \
  --name product-finder-api \
  -p 8080:8080 \
  --env-file backend/.env \
  -e PORT=8080 \
  product-finder-api:local
```

The container runs as a non-root user, listens on `0.0.0.0`, and respects Cloud Run's injected `PORT` value.

## Cloud deployment

The production backend follows this deployment path:

1. Cloud Build builds the backend Dockerfile.
2. Artifact Registry stores the versioned image.
3. Cloud Run runs the image with zero minimum instances and one maximum instance.
4. A dedicated runtime service account receives access only to the Gemini secret.
5. Secret Manager injects `GOOGLE_API_KEY` at runtime.
6. Explicit CORS origins allow the local and deployed custom frontends.

The frontend is connected to GitHub and deployed by Netlify with:

```text
Base directory: frontend
Build command: npm run build
Publish directory: dist
```

`VITE_API_URL` contains only the public Cloud Run origin. The browser never receives the Gemini API key.

## Design decisions and trade-offs

- **One agent, one tool:** matches the assignment and keeps the execution path easy to explain.
- **Deterministic filtering:** avoids asking an LLM to perform authoritative numeric comparisons.
- **Structured API response:** product cards use validated tool data instead of extracting facts from generated text.
- **Fixed JSON catalogue:** appropriate for the supplied 13-item prototype and requires no database.
- **In-memory ADK sessions:** sufficient because every search is independent; sessions are not durable across instances.
- **Scale to zero:** reduces demo cost but can introduce a cold-start delay on the first request.
- **Public demo endpoint:** enables direct browser access; maximum instances and billing alerts reduce cost exposure, but this is not an authenticated production commerce API.
- **External image URLs:** preserved from the assignment dataset. The UI provides an image-unavailable fallback when a source blocks hotlinking or becomes unavailable.
- **Flexible dependency ranges:** suitable for the time-boxed prototype, though a longer-lived production service should use a reproducible lock strategy and automated dependency updates.

## Explicitly out of scope

The assignment explicitly prohibits embeddings, RAG, and multiple agents. Those capabilities are not used.

The following features are also intentionally excluded because they are unnecessary for a fixed-catalogue, 3-5-hour prototype:

- Database
- Authentication and user accounts
- Checkout or payment processing
- Admin dashboard
- LangGraph or another orchestration framework
- Kubernetes
- Learned recommendation model

Adding these features would increase cost and complexity without improving compliance with the assignment's evaluation criteria.

## Known limitations

- Product availability and facts are limited to the supplied static catalogue.
- The API depends on Gemini availability and free-tier rate limits.
- Scale-to-zero can make the first request slower.
- Some third-party image hosts may block embedded images.
- The public demo is intentionally unauthenticated and should retain conservative Cloud Run scaling limits.

## Walkthrough summary

For a concise demonstration:

1. Submit a natural-language query in the custom frontend.
2. Show the browser request going directly to the Cloud Run `/api/v1/chat` endpoint.
3. Explain how the ADK agent maps language to `find_products` arguments.
4. Show that Python performs the actual filtering against `products.json`.
5. Show the structured JSON response and the rendered product cards.
6. Demonstrate category-only, combined category-price, exact-price, and no-result queries.
