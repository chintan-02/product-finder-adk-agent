"""Validate the assignment's fixed product catalogue without external packages."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse


CATALOGUE_PATH = Path(__file__).parents[1] / "app" / "data" / "products.json"
REQUIRED_FIELDS = {"id", "name", "category", "description", "price", "image"}
EXPECTED_CATEGORIES = {"accessories", "clothing", "electronics", "groceries"}


def validate_catalogue() -> None:
    products = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))

    if not isinstance(products, list):
        raise ValueError("Catalogue must be a JSON array.")
    if len(products) != 13:
        raise ValueError(f"Expected 13 products, found {len(products)}.")

    ids: list[int] = []
    categories: set[str] = set()

    for index, product in enumerate(products):
        if not isinstance(product, dict):
            raise ValueError(f"Product at index {index} must be an object.")

        missing = REQUIRED_FIELDS - product.keys()
        extra = product.keys() - REQUIRED_FIELDS
        if missing or extra:
            raise ValueError(
                f"Product at index {index} has missing={sorted(missing)} "
                f"and extra={sorted(extra)} fields."
            )

        product_id = product["id"]
        if not isinstance(product_id, int) or isinstance(product_id, bool):
            raise ValueError(f"Product at index {index} has a non-integer ID.")
        ids.append(product_id)

        for field in ("name", "category", "description", "image"):
            value = product[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Product {product_id} has an invalid {field}.")
            if value != value.strip() or "\n" in value or "\r" in value:
                raise ValueError(f"Product {product_id} has whitespace artifacts in {field}.")

        price = product["price"]
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
            raise ValueError(f"Product {product_id} has an invalid price.")

        parsed_url = urlparse(product["image"])
        if parsed_url.scheme != "https" or not parsed_url.netloc or " " in product["image"]:
            raise ValueError(f"Product {product_id} has an invalid image URL.")

        categories.add(product["category"])

    if sorted(ids) != list(range(13)) or len(set(ids)) != 13:
        raise ValueError(f"Expected unique IDs 0-12, found {sorted(ids)}.")
    if categories != EXPECTED_CATEGORIES:
        raise ValueError(f"Unexpected categories: {sorted(categories)}.")

    print("Catalogue valid: 13 products, IDs 0-12, 4 categories.")


if __name__ == "__main__":
    validate_catalogue()
