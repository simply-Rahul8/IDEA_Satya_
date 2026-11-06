"""Build data/samples/audit-120.csv: a synthetic Shopify-style catalogue of 120 products from data/corpus.

Run: python scripts/make_audit_sample.py   (fictional listings; every cell is data, never instructions)
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "samples" / "audit-120.csv"
NON_COSMETIC = [
    ("Ayurvedic Joint Pain Relief Oil", "Ayurvedic oil for arthritis and joint pain. Doctor recommended."),
    ("Paracetamol 500 mg Tablets", "Fast relief from fever. OTC drug, take one tablet after food."),
    ("Herbal Immunity Kadha", "AYUSH licensed herbal decoction to boost immunity."),
]
LM_TEXT = (
    " Net quantity 50 ml. MRP Rs. 499. Made in India."
    " Manufactured by Fictional Labs Pvt Ltd, Pune 411001. Customer care: care@example.com."
)
FIELDS = ["Handle", "Title", "Body (HTML)", "Vendor", "Type", "Variant SKU", "Variant Compare At Price"]


def main() -> None:
    pdps = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "data" / "corpus").glob("pdp-*.json"))]
    rows = []
    for i in range(120):
        if i in (30, 60, 90):
            title, body = NON_COSMETIC[i // 30 - 1]
            vendor, kind = "Fictional Wellness", "Wellness"
        else:
            pdp = pdps[i % len(pdps)]
            texts = [s["text"] for s in pdp["sentences"]]
            title, body = texts[0] + (f" ({i // len(pdps) + 1})" if i >= len(pdps) else ""), " ".join(texts[1:])
            vendor, kind = pdp["brand"], pdp["category"]
        if i % 4 == 0:  # a quarter of the catalogue declares all Legal Metrology fields
            body += LM_TEXT
        rows.append({
            "Handle": f"product-{i + 1:03d}", "Title": title, "Body (HTML)": f"<p>{body}</p>", "Vendor": vendor,
            "Type": kind, "Variant SKU": f"SKU-{i + 1:04d}", "Variant Compare At Price": "499" if i % 4 == 0 else "",
        })  # fmt: skip
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {OUT} ({len(rows)} products)")


if __name__ == "__main__":
    main()
