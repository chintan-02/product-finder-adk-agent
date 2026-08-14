"""Validation tests for the typed search contracts."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from backend.app.models import ProductFilters, SearchResult


class ProductFiltersTests(unittest.TestCase):
    def test_normalizes_category_and_search_text(self) -> None:
        filters = ProductFilters(category="  ELECTRONICS  ", search_text="  USB-C   HUB ")

        self.assertEqual(filters.category, "electronics")
        self.assertEqual(filters.search_text, "usb-c hub")

    def test_rejects_operator_without_value(self) -> None:
        with self.assertRaisesRegex(ValidationError, "supplied together"):
            ProductFilters(price_operator="lt")

    def test_rejects_value_without_operator(self) -> None:
        with self.assertRaisesRegex(ValidationError, "supplied together"):
            ProductFilters(price_value=50)

    def test_rejects_negative_price(self) -> None:
        with self.assertRaises(ValidationError):
            ProductFilters(price_operator="lt", price_value=-1)

    def test_rejects_unsupported_operator(self) -> None:
        with self.assertRaises(ValidationError):
            ProductFilters(price_operator="approximately", price_value=50)

    def test_rejects_blank_optional_text(self) -> None:
        with self.assertRaises(ValidationError):
            ProductFilters(category="   ")


class SearchResultTests(unittest.TestCase):
    def test_rejects_incorrect_count(self) -> None:
        with self.assertRaisesRegex(ValidationError, "count must equal"):
            SearchResult(products=(), applied_filters=ProductFilters(), count=1)


if __name__ == "__main__":
    unittest.main()
