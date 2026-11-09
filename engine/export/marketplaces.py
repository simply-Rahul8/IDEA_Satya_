"""Best-effort marketplace layouts for Nykaa and Amazon India beauty (SAT-29).

These are NOT the real seller templates. Nykaa's and Amazon's catalogue templates live behind the
seller panel / account manager, vary by seller and category, and are not reliably public (plan P29).
So each layout here is a best-effort preset of the commonly required beauty fields, marked
`placeholder=True`. The column-mapping screen lets the seller reconcile headers and fill
seller-only fields (SKU, MRP, price, images) before export, so a wrong guess never ships silently.

When a real template arrives, replace the matching layout's `columns` with the exact headers
(or build the exact exporter) and drop `placeholder=True`.
"""

from __future__ import annotations

from engine.export.layouts import ColumnSpec, Layout, register_layout

# Fields Satya can source from a ProductTruth/PDPPack map to default_source; seller-only fields
# (SKU, MRP, selling price, images, discovery attributes) default to None for the seller to map or fill.
NYKAA_BEAUTY_LAYOUT = Layout(
    id="nykaa-beauty-v0",
    label="Nykaa beauty (best-effort preset — reconcile with your seller template)",
    placeholder=True,
    columns=[
        ColumnSpec(header="Seller SKU", default_source=None),  # seller-assigned
        ColumnSpec(header="Product Name", default_source="product_name", required=True),
        ColumnSpec(header="Brand", default_source="brand"),
        ColumnSpec(header="Category", default_source="category"),
        ColumnSpec(header="MRP", default_source=None),  # seller pricing
        ColumnSpec(header="Selling Price", default_source=None),
        ColumnSpec(header="Net Quantity", default_source="size"),
        ColumnSpec(header="About The Product", default_source="description"),
        *[ColumnSpec(header=f"Key Benefit {i}", default_source=f"bullet_{i}") for i in range(1, 6)],
        ColumnSpec(header="How To Use", default_source="how_to_use"),
        ColumnSpec(header="Ingredients", default_source="ingredients"),
        ColumnSpec(header="Shade", default_source=None),  # discovery attribute
        ColumnSpec(header="Skin Type", default_source=None),
        ColumnSpec(header="Concern", default_source=None),
        ColumnSpec(header="Formulation", default_source=None),
        ColumnSpec(header="Finish", default_source=None),
        ColumnSpec(header="Warnings And Storage", default_source="warnings_storage"),
        ColumnSpec(header="Country Of Origin", default_source="country_of_origin"),
        ColumnSpec(header="Manufacturer / Marketer", default_source="manufacturer"),
        ColumnSpec(header="Image URL 1", default_source=None),
    ],
)

AMAZON_IN_BEAUTY_LAYOUT = Layout(
    id="amazon-in-beauty-v0",
    label="Amazon India beauty (best-effort preset — reconcile with your category flat file)",
    placeholder=True,
    columns=[
        ColumnSpec(header="Seller SKU (item_sku)", default_source=None),
        ColumnSpec(header="Product Name (item_name)", default_source="title", required=True),
        ColumnSpec(header="Brand (brand_name)", default_source="brand"),
        ColumnSpec(header="Product Type (feed_product_type)", default_source=None),
        ColumnSpec(header="Standard Price", default_source=None),
        ColumnSpec(header="Quantity", default_source=None),
        ColumnSpec(header="Product Description", default_source="description"),
        *[ColumnSpec(header=f"Bullet Point {i}", default_source=f"bullet_{i}") for i in range(1, 6)],
        ColumnSpec(header="Generic Keywords", default_source="seo_description"),
        ColumnSpec(header="Directions (how_to_use)", default_source="how_to_use"),
        ColumnSpec(header="Ingredients", default_source="ingredients"),
        ColumnSpec(header="Safety Warning", default_source="warnings_storage"),
        ColumnSpec(header="Item Volume (size)", default_source="size"),
        ColumnSpec(header="Country Of Origin", default_source="country_of_origin"),
        ColumnSpec(header="Manufacturer", default_source="manufacturer"),
        ColumnSpec(header="Main Image URL (main_image_url)", default_source=None),
    ],
)

for _layout in (NYKAA_BEAUTY_LAYOUT, AMAZON_IN_BEAUTY_LAYOUT):
    register_layout(_layout)
