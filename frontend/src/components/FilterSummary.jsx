const OPERATOR_LABELS = {
  lt: "under",
  lte: "at most",
  gt: "over",
  gte: "at least",
  eq: "exactly",
};

export default function FilterSummary({ filters }) {
  if (!filters) return null;

  const labels = [];
  if (filters.category) labels.push(filters.category);
  if (filters.price_operator && filters.price_value !== null) {
    labels.push(
      `${OPERATOR_LABELS[filters.price_operator] || filters.price_operator} $${Number(
        filters.price_value,
      ).toLocaleString()}`,
    );
  }
  if (filters.search_text) labels.push(`matching “${filters.search_text}”`);

  if (labels.length === 0) {
    labels.push("all products");
  }

  return (
    <div className="filter-summary" aria-label="Applied search filters">
      <span className="filter-label">Applied filters</span>
      {labels.map((label) => (
        <span className="filter-chip" key={label}>
          {label}
        </span>
      ))}
    </div>
  );
}
