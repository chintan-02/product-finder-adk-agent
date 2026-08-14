export default function ChatInput({ value, onChange, onSubmit, isLoading }) {
  return (
    <form className="search-form" onSubmit={onSubmit}>
      <label className="sr-only" htmlFor="product-query">
        Describe the products you want to find
      </label>
      <div className="search-control">
        <span className="search-icon" aria-hidden="true">
          ⌕
        </span>
        <input
          id="product-query"
          name="message"
          type="text"
          value={value}
          maxLength={500}
          autoComplete="off"
          placeholder="Try “clothing under $50”"
          onChange={(event) => onChange(event.target.value)}
          disabled={isLoading}
        />
        <button
          className="search-button"
          type="submit"
          disabled={isLoading || !value.trim()}
        >
          {isLoading ? "Searching…" : "Find products"}
        </button>
      </div>
      <div className="input-meta">
        <span>Natural language supported</span>
        <span>{value.length}/500</span>
      </div>
    </form>
  );
}
