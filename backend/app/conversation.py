"""Validated search transitions and deterministic zero-match suggestions."""

from functools import lru_cache

from .models import Product, ProductFilters, SearchResult
from .product_service import load_products, search_products

PRICE_FIELDS = {"price_operator", "price_value", "min_price", "max_price"}
CLEAR_FIELDS = set(ProductFilters.model_fields) - {"price_operator", "price_value"} | {"price"}


@lru_cache(maxsize=1)
def demo_products() -> tuple[Product, ...]:
    image = load_products()[8].image
    return tuple(
        Product(
            id=product_id, name=name, category="clothing",
            description="Waterproof jacket in the sample demo catalogue.",
            price=price, image=image, color=color, sizes=sizes, waterproof=True,
        )
        for product_id, name, price, color, sizes in (
            (100, "Sample Trail Jacket", 85, "black", ("M", "L")),
            (101, "Sample Ridge Jacket", 95, "blue", ("L",)),
            (102, "Sample Summit Jacket", 115, "black", ("XL",)),
            (103, "Sample Coast Jacket", 125, "green", ("XL",)),
        )
    )


def apply_filters(previous: ProductFilters, updates: dict, clear: list[str], reset: bool) -> ProductFilters:
    if set(clear) - CLEAR_FIELDS:
        raise ValueError("unknown filter to clear")
    values = {} if reset else previous.model_dump(exclude_none=True)
    for field in clear:
        for key in PRICE_FIELDS if field == "price" else (field,):
            values.pop(key, None)

    # A legacy single-price comparison and the conversational bounds use one
    # price representation at a time.
    if "price_operator" in updates or "price_value" in updates:
        for key in PRICE_FIELDS:
            values.pop(key, None)
    if "min_price" in updates or "max_price" in updates:
        for key in ("price_operator", "price_value"):
            values.pop(key, None)
    values.update(updates)
    return ProductFilters.model_validate(values)


def search(filters: ProductFilters, demo: bool) -> SearchResult:
    return search_products(**filters.model_dump(), products=demo_products() if demo else None)


def budget_offer(filters: ProductFilters, demo: bool) -> tuple[str, SearchResult] | None:
    if filters.max_price is None:
        return None
    unbounded = apply_filters(filters, {}, ["max_price"], False)
    candidates = search(unbounded, demo).products
    next_prices = [p.price for p in candidates if p.price > filters.max_price]
    if not next_prices:
        return None
    next_price = min(next_prices)
    updated = apply_filters(filters, {"max_price": next_price}, [], False)
    return f"Raise budget to ${next_price:g}", search(updated, demo)
