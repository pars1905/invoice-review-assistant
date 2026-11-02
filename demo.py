import json
import sys
from app import parse_invoice, post_to_erp, read_document, review

SAMPLE = """Invoice: INV-101
Vendor: Acme Supplies
PO: PO-42
Item: PAPER | 2 | 12.50 | 25.00
Item: PEN | 3 | 2.00 | 6.00
Total: 31.00
"""
PO = {"PO-42": {"vendor": "Acme Supplies", "items": {
    "PAPER": {"quantity": 2, "unit_price": "12.50"},
    "PEN": {"quantity": 3, "unit_price": "2.00"}}}}

if __name__ == "__main__":
    paths = [arg for arg in sys.argv[1:] if arg != "--ai"]
    document = read_document(paths[0]) if paths else SAMPLE
    invoice = parse_invoice(document)
    posted = {}
    decision = review(invoice, PO, posted)
    print(json.dumps({"review": decision}, indent=2))
    if "--ai" in sys.argv:
        from ai_explain import explain
        print(explain("invoice review", decision))
    if decision["approved_for_review"]:
        print(json.dumps({"approved_post": post_to_erp(invoice, PO, True, posted)}, indent=2))
