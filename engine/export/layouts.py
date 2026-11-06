"""Data-driven column layouts and mappings (P29). Marketplace layouts register here later; the generic CSV
and the column-mapping screen only ever see a `Layout`."""

from __future__ import annotations

from pydantic import BaseModel

from engine.models import SECTION_KEYS, PDPPack, ProductTruth

TRUTH_SOURCES = ("product_name", "brand", "category", "size", "ingredients", "manufacturer", "country_of_origin")
SOURCES: tuple[str, ...] = (*SECTION_KEYS, *TRUTH_SOURCES)


class ColumnSpec(BaseModel):
    header: str
    default_source: str | None = None  # a name in SOURCES, or None to leave blank
    required: bool = False


class Layout(BaseModel):
    id: str
    label: str
    placeholder: bool = False
    columns: list[ColumnSpec]


class MappingError(ValueError):
    pass


# Documented placeholder: NOT a marketplace layout. Replaced per marketplace once a real template arrives.
PLACEHOLDER_LAYOUT = Layout(
    id="generic-v0",
    label="Generic CSV (placeholder layout, not a marketplace template)",
    placeholder=True,
    columns=[
        ColumnSpec(header="Product Name", default_source="product_name", required=True),
        ColumnSpec(header="Brand", default_source="brand"),
        ColumnSpec(header="Category", default_source="category"),
        ColumnSpec(header="Size", default_source="size"),
        ColumnSpec(header="Title", default_source="title", required=True),
        *[ColumnSpec(header=f"Bullet {i}", default_source=f"bullet_{i}") for i in range(1, 6)],
        ColumnSpec(header="Description", default_source="description"),
        ColumnSpec(header="How To Use", default_source="how_to_use"),
        ColumnSpec(header="Warnings And Storage", default_source="warnings_storage"),
        ColumnSpec(header="Ingredients", default_source="ingredients"),
        ColumnSpec(header="Manufacturer", default_source="manufacturer"),
        ColumnSpec(header="Country Of Origin", default_source="country_of_origin"),
        ColumnSpec(header="SEO Title", default_source="seo_title"),
        ColumnSpec(header="SEO Description", default_source="seo_description"),
    ],
)

_REGISTRY: dict[str, Layout] = {PLACEHOLDER_LAYOUT.id: PLACEHOLDER_LAYOUT}


def register_layout(layout: Layout) -> None:
    _REGISTRY[layout.id] = layout


def get_layout(layout_id: str) -> Layout:
    try:
        return _REGISTRY[layout_id]
    except KeyError:
        raise MappingError(f"unknown layout {layout_id!r}") from None


def list_layouts() -> list[Layout]:
    return list(_REGISTRY.values())


# header -> source name (or None for a blank column)
Mapping = dict[str, str | None]


def default_mapping(layout: Layout) -> Mapping:
    return {c.header: c.default_source for c in layout.columns}


def validate_mapping(layout: Layout, mapping: Mapping) -> Mapping:
    """Return a complete mapping (unmapped headers become blank) or raise MappingError."""
    headers = {c.header for c in layout.columns}
    extra = sorted(set(mapping) - headers)
    if extra:
        raise MappingError(f"unknown columns: {extra}")
    full: Mapping = {c.header: mapping.get(c.header) for c in layout.columns}
    for c in layout.columns:
        src = full[c.header]
        if src is not None and src not in SOURCES:
            raise MappingError(f"column {c.header!r}: unknown source {src!r}")
        if c.required and src is None:
            raise MappingError(f"column {c.header!r} is required")
    return full


def source_value(source: str, pack: PDPPack, truth: ProductTruth) -> str:
    if source in SECTION_KEYS:
        return " ".join(s.text for s in pack.section(source).sentences)
    value = getattr(truth, source)
    if isinstance(value, list):
        return ", ".join(value)
    return value or ""
