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
    color: str | None = None
    sizes: tuple[str, ...] = ()
    waterproof: bool | None = None

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
    price_value: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    search_text: str | None = None
    color: str | None = None
    size: str | None = None
    waterproof: bool | None = None
    max_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    min_price: float | None = Field(default=None, ge=0, allow_inf_nan=False)

    @field_validator("color", "size")
    @classmethod
    def normalize_attribute(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        if info.field_name == "size":
            size = value.strip().upper()
            if size not in {"XS", "S", "M", "L", "XL", "XXL"}:
                raise ValueError("unsupported size")
            return size
        color = value.strip().casefold()
        color = {"navy": "blue", "gray": "grey", "charcoal": "grey"}.get(color, color)
        if color not in {"black", "blue", "red", "green", "grey", "white", "brown"}:
            raise ValueError("unsupported colour")
        return color

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
        if self.min_price is not None and self.max_price is not None:
            if self.min_price > self.max_price:
                raise ValueError("minimum price exceeds maximum price")
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


class ChatRequest(BaseModel):
    """Validated browser-to-backend chat request."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=500)
    active_filters: ProductFilters | None = None
    demo_catalogue: bool = False
    accept_relaxation: bool = False

    @field_validator("message")
    @classmethod
    def trim_and_reject_blank_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message must not be blank")
        return normalized


class ChatResponse(BaseModel):
    """Stable response contract consumed by the custom frontend."""

    model_config = ConfigDict(extra="forbid")

    message: str
    products: tuple[Product, ...]
    applied_filters: ProductFilters
    count: int = Field(ge=0)
    request_id: str
    clarification: bool = False
    relaxation_offer: str | None = None

    @model_validator(mode="after")
    def count_must_match_products(self) -> "ChatResponse":
        if self.count != len(self.products):
            raise ValueError("count must equal the number of products")
        return self
