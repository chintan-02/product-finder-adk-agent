import { useEffect, useRef, useState } from "react";

import { searchProducts } from "./api";
import ChatInput from "./components/ChatInput";
import FilterSummary from "./components/FilterSummary";
import ProductGrid from "./components/ProductGrid";

const EXAMPLE_QUERIES = [
  "Show all clothing products",
  "Electronics over $200",
  "Products exactly $49",
  "Groceries at most $5",
];

export default function App() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const activeRequest = useRef(null);

  useEffect(() => () => activeRequest.current?.abort(), []);

  async function runSearch(rawQuery) {
    const normalizedQuery = rawQuery.trim();
    if (!normalizedQuery || isLoading) return;

    activeRequest.current?.abort();
    const controller = new AbortController();
    activeRequest.current = controller;

    setSubmittedQuery(normalizedQuery);
    setQuery(normalizedQuery);
    setResult(null);
    setError("");
    setIsLoading(true);

    try {
      const payload = await searchProducts(normalizedQuery, controller.signal);
      setResult(payload);
    } catch (requestError) {
      if (requestError.name !== "AbortError") {
        setError(requestError.message || "Unable to connect to the product service.");
      }
    } finally {
      if (activeRequest.current === controller) {
        activeRequest.current = null;
        setIsLoading(false);
      }
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    runSearch(query);
  }

  function clearSearch() {
    activeRequest.current?.abort();
    activeRequest.current = null;
    setQuery("");
    setSubmittedQuery("");
    setResult(null);
    setError("");
    setIsLoading(false);
  }

  return (
    <main className="app-shell">
      <header className="site-header">
        <a className="brand" href="#top" aria-label="Product Finder home">
          <span className="brand-mark" aria-hidden="true">P</span>
          <span>
            <strong>Product Finder</strong>
            <small>AI Agent</small>
          </span>
        </a>
        <div className="system-status">
          <span aria-hidden="true" />
          Deterministic search
        </div>
      </header>

      <section className="hero" id="top">
        <div className="eyebrow">Powered by Google ADK</div>
        <h1>Describe what you need.<br />We’ll find the right products.</h1>
        <p>
          Search the catalogue naturally by category, price, or product name.
          Exact filtering happens in verified code.
        </p>

        <div className="search-panel">
          <ChatInput
            value={query}
            onChange={setQuery}
            onSubmit={handleSubmit}
            isLoading={isLoading}
          />
          <div className="example-row" aria-label="Example product searches">
            <span>Try an example</span>
            <div>
              {EXAMPLE_QUERIES.map((example) => (
                <button
                  type="button"
                  className="example-chip"
                  key={example}
                  disabled={isLoading}
                  onClick={() => runSearch(example)}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="results-section" aria-live="polite" aria-busy={isLoading}>
        {isLoading && (
          <div className="state-card loading-state">
            <div className="spinner" aria-hidden="true" />
            <div>
              <strong>Finding matching products</strong>
              <p>The agent is interpreting your request and checking the catalogue.</p>
            </div>
          </div>
        )}

        {error && (
          <div className="state-card error-state" role="alert">
            <span aria-hidden="true">!</span>
            <div>
              <strong>Search unavailable</strong>
              <p>{error}</p>
            </div>
            <button type="button" onClick={() => runSearch(submittedQuery)}>Try again</button>
          </div>
        )}

        {result && (
          <>
            <div className="conversation">
              <div className="message user-message">
                <span>You</span>
                <p>{submittedQuery}</p>
              </div>
              <div className="message agent-message">
                <span className="agent-avatar" aria-hidden="true">P</span>
                <div>
                  <span>Product Finder</span>
                  <p>{result.message}</p>
                </div>
              </div>
            </div>

            <div className="results-header">
              <div>
                <p className="section-kicker">Search results</p>
                <h2>{result.count} {result.count === 1 ? "product" : "products"} found</h2>
              </div>
              <button className="clear-button" type="button" onClick={clearSearch}>Clear search</button>
            </div>
            <FilterSummary filters={result.applied_filters} />

            {result.count > 0 ? (
              <ProductGrid products={result.products} />
            ) : (
              <div className="state-card empty-state">
                <span aria-hidden="true">⌕</span>
                <div>
                  <strong>No matching products</strong>
                  <p>Try changing the category, price, or product wording.</p>
                </div>
              </div>
            )}
          </>
        )}

        {!isLoading && !error && !result && (
          <div className="trust-row">
            <div><strong>13</strong><span>catalogue products</span></div>
            <div><strong>5</strong><span>price operators</span></div>
            <div><strong>1</strong><span>grounded agent</span></div>
          </div>
        )}
      </section>

      <footer>
        <p>Product facts come only from the supplied catalogue.</p>
        <p>Google ADK · Deterministic Python filtering</p>
      </footer>
    </main>
  );
}
