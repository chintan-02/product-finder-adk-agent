import catalogue from "../../backend/app/data/products.json" with { type: "json" };

const examples = {
  "Show all clothing products": { category: "clothing" },
  "Electronics over $200": { category: "electronics", price_operator: "gt", price_value: 200 },
  "Products exactly $49": { price_operator: "eq", price_value: 49 },
  "Groceries at most $5": { category: "groceries", price_operator: "lte", price_value: 5 },
};

const comparePrice = {
  gt: (price, limit) => price > limit,
  eq: (price, limit) => price === limit,
  lte: (price, limit) => price <= limit,
};

export const EXAMPLE_QUERIES = Object.keys(examples);

export function browseCategory(product) {
  // The source dataset groups footwear under clothing. Keep the storefront
  // distinction consistent for example cards and subsequent clothing results.
  return product.id === 5 ? "footwear" : product.category;
}

export function findCatalogueExample(message) {
  if (!Object.hasOwn(examples, message)) return null;
  const filters = examples[message];
  const products = catalogue.filter((product) =>
    (!filters.category || browseCategory(product) === filters.category) &&
    (!filters.price_operator || comparePrice[filters.price_operator](product.price, filters.price_value)),
  );
  return {
    message: `${products.length} exact ${products.length === 1 ? "match" : "matches"}.`,
    products,
    count: products.length,
    applied_filters: filters,
  };
}

export function visibleSearchResult(result) {
  if (result.clarification || result.applied_filters.category !== "clothing") return result;
  const products = result.products.filter((product) => browseCategory(product) === "clothing");
  return products.length === result.count ? result : {
    ...result,
    products,
    count: products.length,
    message: `${products.length} exact ${products.length === 1 ? "match" : "matches"}.`,
  };
}
