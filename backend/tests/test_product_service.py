"""Boundary and behavior tests for deterministic product filtering."""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from backend.app.product_service import load_products, search_products


class CatalogueLoadingTests(unittest.TestCase):
    def test_loads_exact_assignment_catalogue(self) -> None:
        products = load_products()

        self.assertEqual(len(products), 13)
        self.assertEqual([product.id for product in products], list(range(13)))

    def test_catalogue_is_immutable(self) -> None:
        products = load_products()

        with self.assertRaises(ValidationError):
            products[0].price = 1


class ProductSearchTests(unittest.TestCase):
    @staticmethod
    def names(result) -> list[str]:
        return [product.name for product in result.products]

    def test_no_filters_returns_all_products(self) -> None:
        result = search_products()

        self.assertEqual(result.count, 13)

    def test_category_filter_is_case_insensitive(self) -> None:
        result = search_products(category=" CLOTHING ")

        self.assertEqual(
            self.names(result),
            ["UBC Hoodie", "Running Shoes", "T-Shirt", "Denim Jacket"],
        )

    def test_less_than_excludes_boundary(self) -> None:
        result = search_products(category="clothing", price_operator="lt", price_value=45)

        self.assertEqual(self.names(result), ["T-Shirt"])

    def test_less_than_or_equal_includes_boundary(self) -> None:
        result = search_products(category="clothing", price_operator="lte", price_value=45)

        self.assertEqual(self.names(result), ["UBC Hoodie", "T-Shirt"])

    def test_greater_than_excludes_boundary(self) -> None:
        result = search_products(category="electronics", price_operator="gt", price_value=249)

        self.assertEqual(self.names(result), ["MacBook Air"])

    def test_greater_than_or_equal_includes_boundary(self) -> None:
        result = search_products(category="electronics", price_operator="gte", price_value=249)

        self.assertEqual(self.names(result), ["MacBook Air", "Smartwatch"])

    def test_equal_price(self) -> None:
        result = search_products(price_operator="eq", price_value=49)

        self.assertEqual(self.names(result), ["Backpack"])

    def test_required_combined_category_and_price_filter(self) -> None:
        result = search_products(category="clothing", price_operator="lt", price_value=50)

        self.assertEqual(self.names(result), ["UBC Hoodie", "T-Shirt"])
        self.assertEqual(result.count, 2)

    def test_unknown_category_returns_empty_result(self) -> None:
        result = search_products(category="furniture")

        self.assertEqual(result.products, ())
        self.assertEqual(result.count, 0)

    def test_text_search_matches_name(self) -> None:
        result = search_products(search_text="headphones")

        self.assertEqual(self.names(result), ["Bluetooth Headphones"])

    def test_text_search_matches_description(self) -> None:
        result = search_products(search_text="whole grain")

        self.assertEqual(self.names(result), ["Brown Rice"])

    def test_search_does_not_mutate_catalogue(self) -> None:
        before = load_products()

        search_products(category="groceries", price_operator="lte", price_value=5)

        self.assertIs(load_products(), before)
        self.assertEqual(len(before), 13)

    def test_applied_filters_are_returned(self) -> None:
        result = search_products(category=" ELECTRONICS ", price_operator="gt", price_value=200)

        self.assertEqual(result.applied_filters.category, "electronics")
        self.assertEqual(result.applied_filters.price_operator, "gt")
        self.assertEqual(result.applied_filters.price_value, 200)


if __name__ == "__main__":
    unittest.main()
