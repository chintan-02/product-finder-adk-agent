"""Typed contracts shared by the catalogue loader and search service."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator


class PriceOperator(StrEnum):
    """Supported deterministic price comparisons."""

    LESS_THAN = "lt"
    LESS_THAN_OR_EQUAL = "lte"
    GREATER_THAN = "gt"
    GREATER_THAN_OR_EQUAL = "gte"
    EQUAL = "eq"


class Product(BaseModel):
    """One immutable product from the assignment catalogue."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: int = Field(ge=0)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    description: str = Field(min_length=1)
    price: float = Field(ge=0)
    image: HttpUrl

    @field_validator("name", "category", "description")
    @classmethod
    def reject_blank_or_padded_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        if value != value.strip():
            raise ValueError("must not contain surrounding whitespace")
        return value


class ProductFilters(BaseModel):
    """Validated arguments that the ADK tool will eventually receive."""

    model_config = ConfigDict(extra="forbid")

    category: str | None = None
    price_operator: PriceOperator | None = None
    price_value: float | None = Field(default=None, ge=0)
    search_text: str | None = None

    @field_validator("category", "search_text")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split()).casefold()
        if not normalized:
            raise ValueError("must not be blank")
        return normalized

    @model_validator(mode="after")
    def require_complete_price_filter(self) -> "ProductFilters":
        has_operator = self.price_operator is not None
        has_value = self.price_value is not None
        if has_operator != has_value:
            raise ValueError("price_operator and price_value must be supplied together")
        return self


class SearchResult(BaseModel):
    """Structured, serializable output returned by deterministic search."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    products: tuple[Product, ...]
    applied_filters: ProductFilters
    count: int = Field(ge=0)

    @model_validator(mode="after")
    def count_must_match_products(self) -> "SearchResult":
        if self.count != len(self.products):
            raise ValueError("count must equal the number of products")
        return self
