"""Deterministic catalogue loading and product filtering."""

from __future__ import annotations

import json
import operator
from collections.abc import Callable, Iterable
from functools import lru_cache
from pathlib import Path

from pydantic import TypeAdapter

from .models import PriceOperator, Product, ProductFilters, SearchResult


CATALOGUE_PATH = Path(__file__).parent / "data" / "products.json"

PRICE_COMPARISONS: dict[PriceOperator, Callable[[float, float], bool]] = {
    PriceOperator.LESS_THAN: operator.lt,
    PriceOperator.LESS_THAN_OR_EQUAL: operator.le,
    PriceOperator.GREATER_THAN: operator.gt,
    PriceOperator.GREATER_THAN_OR_EQUAL: operator.ge,
    PriceOperator.EQUAL: operator.eq,
}


@lru_cache(maxsize=1)
def load_products() -> tuple[Product, ...]:
    """Load and validate the fixed JSON catalogue once per process."""

    raw_products = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    products = TypeAdapter(list[Product]).validate_python(raw_products)

    ids = [product.id for product in products]
    if len(products) != 13 or sorted(ids) != list(range(13)) or len(set(ids)) != 13:
        raise ValueError("Catalogue must contain exactly one product for each ID from 0 to 12.")

    return tuple(products)


def search_products(
    *,
    category: str | None = None,
    price_operator: PriceOperator | str | None = None,
    price_value: float | None = None,
    search_text: str | None = None,
    products: Iterable[Product] | None = None,
) -> SearchResult:
    """Apply validated filters in a deterministic, linear scan.

    The optional ``products`` argument exists for isolated tests. Production
    calls use the validated assignment catalogue returned by ``load_products``.
    """

    filters = ProductFilters(
        category=category,
        price_operator=price_operator,
        price_value=price_value,
        search_text=search_text,
    )
    catalogue = tuple(products) if products is not None else load_products()

    matches: list[Product] = []
    for product in catalogue:
        if filters.category and product.category.casefold() != filters.category:
            continue

        if filters.price_operator is not None and filters.price_value is not None:
            comparison = PRICE_COMPARISONS[filters.price_operator]
            if not comparison(product.price, filters.price_value):
                continue

        if filters.search_text:
            searchable_text = f"{product.name} {product.description}".casefold()
            if filters.search_text not in searchable_text:
                continue

        matches.append(product)

    return SearchResult(
        products=tuple(matches),
        applied_filters=filters,
        count=len(matches),
    )
