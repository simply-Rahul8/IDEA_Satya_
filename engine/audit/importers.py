"""Catalogue importers (plan section 3 step 3, P29). Owner: Engine.

Shopify product CSV, pasted text and a generic CSV with header sniffing and column-mapping hints. Every cell is
data (P19): capped in length, stripped of control characters and defanged if it looks like a spreadsheet formula.
Nykaa and Amazon downloads need the real templates (SAT-4): add them with `register_importer`.
"""

from __future__ import annotations

import csv
import html
import io
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from engine.audit.models import ProductRecord

MAX_ROWS = 500  # products per audit (screen-audit "Over the limit")
MAX_BYTES = 2_000_000
MAX_CELL_CHARS = 5000
FORMULA_STARTS = ("=", "+", "-", "@")

FIELDS = tuple(ProductRecord.model_fields)

# Header synonyms, compared after lowercasing and stripping non-alphanumerics.
SYNONYMS: dict[str, tuple[str, ...]] = {
    "sku": ("sku", "variantsku", "productsku", "itemsku", "sellersku", "productcode", "itemcode", "id", "handle"),
    "name": ("name", "title", "productname", "producttitle", "itemname", "product"),
    "description": ("description", "bodyhtml", "body", "productdescription", "details", "about", "longdescription"),
    "category": ("category", "type", "producttype", "productcategory", "categories"),
    "brand": ("brand", "vendor", "brandname"),
    "net_quantity": ("netquantity", "netqty", "netcontent", "netweight", "quantity", "size", "volume", "weight"),
    "mrp": ("mrp", "maximumretailprice", "compareatprice", "variantcompareatprice", "listprice"),
    "manufacturer": ("manufacturer", "manufacturedby", "packer", "packedby", "importer", "manufacturername"),
    "country_of_origin": ("countryoforigin", "origin", "madein", "country"),
    "consumer_care": ("consumercare", "customercare", "consumercaredetails", "grievancecontact", "contactdetails"),
}


class ImportProblem(Exception):
    """A file or text that cannot be audited. `code` drives the screen state; `message` is brand-facing."""

    def __init__(self, code: str, message: str, **extra):
        super().__init__(message)
        self.code, self.message, self.extra = code, message, extra


class NeedsMapping(ImportProblem):
    """No known template matched (P29). `headers` are the file's columns, `suggested` our best guess."""

    def __init__(self, headers: list[str], suggested: dict[str, str]):
        super().__init__("needs_mapping", "We couldn't tell which column is the product name.")
        self.headers, self.suggested = headers, suggested


class OverLimit(ImportProblem):
    def __init__(self, count: int):
        super().__init__(
            "over_limit",
            f"This file has {count} products. v1 checks up to {MAX_ROWS} at a time. "
            f"Split the file, or check the first {MAX_ROWS}.",
            count=count,
            limit=MAX_ROWS,
        )


@dataclass
class ImportResult:
    importer: str
    products: list[ProductRecord]
    total_rows: int  # products found before any truncation
    truncated: bool = False
    warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Importer:
    name: str
    matches: Callable[[list[str]], bool]  # given the header row
    parse: Callable[[list[str], list[list[str]]], list[ProductRecord]]


_REGISTRY: list[Importer] = []


def register_importer(importer: Importer, *, first: bool = True) -> None:
    """Hook for marketplace templates (Nykaa, Amazon). Earlier importers win; the generic CSV is the fallback."""
    _REGISTRY[:] = [i for i in _REGISTRY if i.name != importer.name]
    _REGISTRY.insert(0 if first else len(_REGISTRY), importer)


def importer_names() -> list[str]:
    return [i.name for i in _REGISTRY]


# ---------- cell hygiene ----------

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_cell(value: str | None) -> str:
    """Treat a cell as data: no control characters, bounded length, formulas defanged with a leading apostrophe."""
    raw = _CONTROL.sub("", value or "")[:MAX_CELL_CHARS]
    text = raw.strip()
    if text.startswith(FORMULA_STARTS) or raw[:1] in ("\t", "\r"):
        text = "'" + text
    return text


def _key(header: str) -> str:
    return re.sub(r"[^a-z0-9]", "", header.lower())


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", text))).strip()


def suggest_mapping(headers: list[str]) -> dict[str, str]:
    """Our field -> the file's column, by header synonyms. First column that matches wins; no column is reused."""
    keys = {h: _key(h) for h in headers}
    mapping: dict[str, str] = {}
    for fld in FIELDS:
        for syn in SYNONYMS.get(fld, ()):
            hit = next((h for h, k in keys.items() if k == syn and h not in mapping.values()), None)
            if hit:
                mapping[fld] = hit
                break
    return mapping


# ---------- decoding ----------


def decode(data: bytes | str) -> str:
    if isinstance(data, str):
        text, size = data, len(data.encode("utf-8"))
    else:
        size = len(data)
        if data[:2] == b"PK":
            raise ImportProblem(
                "unsupported_type", "Spreadsheet files (XLSX) are not supported yet. Export the sheet as CSV."
            )
        if b"\x00" in data[:4096]:
            raise ImportProblem("unsupported_type", "That file isn't text or CSV.")
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = data.decode("cp1252", errors="replace")
    if size > MAX_BYTES:
        raise ImportProblem("too_large", f"That file is {size / 1e6:.1f} MB. The limit is {MAX_BYTES // 1_000_000} MB.")
    if not text.strip():
        raise ImportProblem("empty", "That file is empty.")
    return text


def _read_table(text: str) -> tuple[list[str], list[list[str]]]:
    try:
        dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    try:
        rows = [r for r in csv.reader(io.StringIO(text, newline=""), dialect) if any(c.strip() for c in r)]
    except csv.Error as exc:
        raise ImportProblem("unreadable", f"We couldn't read that file as CSV ({exc}).") from exc
    if not rows:
        raise ImportProblem("empty", "That file has no rows.")
    return [h.strip() for h in rows[0]], rows[1:]


# ---------- parsers ----------


def _parse_generic(headers: list[str], rows: list[list[str]], mapping: dict[str, str] | None = None):
    mapping = mapping or suggest_mapping(headers)
    idx = {fld: headers.index(col) for fld, col in mapping.items() if col in headers}
    out: list[ProductRecord] = []
    for n, row in enumerate(rows, start=1):
        vals = {f: clean_cell(row[i]) if i < len(row) else "" for f, i in idx.items()}
        if "description" in vals:
            vals["description"] = clean_cell(_strip_html(vals["description"]))
        if not vals.get("name"):
            continue  # a row with no product name is not a product
        vals["sku"] = vals.get("sku") or f"ROW-{n}"
        out.append(ProductRecord(**vals))
    return out


def _is_shopify(headers: list[str]) -> bool:
    keys = {_key(h) for h in headers}
    return {"handle", "title"} <= keys and ("bodyhtml" in keys or "variantsku" in keys)


_SHOPIFY_COLUMNS = (
    ("name", "title"), ("description", "bodyhtml"), ("brand", "vendor"), ("category", "producttype"),
    ("mrp", "variantcompareatprice"), ("sku", "variantsku"),
)  # fmt: skip


def _parse_shopify(headers: list[str], rows: list[list[str]]) -> list[ProductRecord]:
    """Shopify exports one row per variant or image: rows share a Handle and the first non-empty value of each
    field wins. The SKU is the first variant's SKU, falling back to the handle."""
    col: dict[str, int] = {}
    for i, h in enumerate(headers):
        col.setdefault(_key(h), i)

    def cell(row: list[str], key: str) -> str:
        i = col.get(key)
        return clean_cell(row[i]) if i is not None and i < len(row) else ""

    by_handle: dict[str, dict[str, str]] = {}
    for row in rows:
        handle = cell(row, "handle")
        if not handle:
            continue
        cur = by_handle.setdefault(handle, {})
        for fld, key in _SHOPIFY_COLUMNS:
            cur[fld] = cur.get(fld) or cell(row, key)
        cur["category"] = cur.get("category") or cell(row, "productcategory")
    return [
        ProductRecord(
            sku=v.get("sku") or handle,
            name=v["name"],
            description=clean_cell(_strip_html(v.get("description", ""))),
            category=v.get("category", ""),
            brand=v.get("brand", ""),
            mrp=v.get("mrp", ""),
        )
        for handle, v in by_handle.items()
        if v.get("name")
    ]


register_importer(Importer("generic_csv", lambda h: "name" in suggest_mapping(h), _parse_generic), first=False)
register_importer(Importer("shopify_csv", _is_shopify, _parse_shopify))

_BLOCK_RULE = re.compile(r"\n\s*[-=]{3,}\s*\n")


def _parse_pasted(text: str) -> list[ProductRecord]:
    """Pasted text: products separated by a line of 3+ dashes or '=', or else by blank lines. The first line of a
    block is the product name and the rest is its description."""
    blocks = _BLOCK_RULE.split(text) if _BLOCK_RULE.search(text) else re.split(r"\n\s*\n", text)
    out: list[ProductRecord] = []
    for block in blocks:
        lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
        if lines:
            out.append(
                ProductRecord(
                    sku=f"TEXT-{len(out) + 1}",
                    name=clean_cell(lines[0]),
                    description=clean_cell(" ".join(lines[1:])),
                )
            )
    return out


def _looks_tabular(text: str) -> bool:
    """Pasted prose or a CSV? A first line whose cells include a known column header (name, title, sku, ...) is a CSV.
    Uploads of unknown layouts should pass kind="csv" so they reach the column-mapping step instead."""
    first = text.lstrip().splitlines()[0]
    return bool(suggest_mapping([h.strip() for h in re.split(r"[,;	|]", first)]))


# ---------- entry point ----------


def import_catalogue(
    data: bytes | str,
    *,
    kind: str = "auto",  # auto | csv (uploads) | text (paste)
    mapping: dict[str, str] | None = None,
    allow_truncate: bool = False,
) -> ImportResult:
    """Parse an upload or paste into product records.

    `mapping` is the user's confirmed "Satya field -> your column" choice; it forces the generic importer.
    Raises ImportProblem (NeedsMapping, OverLimit, ...). With allow_truncate=True an over-limit file keeps its
    first MAX_ROWS products.
    """
    text = decode(data)
    warnings: list[str] = []
    if kind == "text" or (kind == "auto" and not mapping and not _looks_tabular(text)):
        name, products = "pasted_text", _parse_pasted(text)
    else:
        headers, rows = _read_table(text)
        if mapping:
            bad = [c for c in mapping.values() if c not in headers]
            if bad or mapping.get("name") not in headers:
                raise ImportProblem("bad_mapping", "The column mapping doesn't match the file's columns.", unknown=bad)
            name, products = "generic_csv", _parse_generic(headers, rows, mapping)
        else:
            imp = next((i for i in _REGISTRY if i.matches(headers)), None)
            if imp is None:
                raise NeedsMapping(headers, suggest_mapping(headers))
            name, products = imp.name, imp.parse(headers, rows)
    if not products:
        raise ImportProblem("no_products", "We found no products in that file.")
    total = len(products)
    truncated = total > MAX_ROWS
    if truncated:
        if not allow_truncate:
            raise OverLimit(total)
        products = products[:MAX_ROWS]
        warnings.append(f"Checked the first {MAX_ROWS} of {total} products.")
    return ImportResult(name, products, total, truncated, warnings)
