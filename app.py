"""Invoice extraction and PO validation; narrow synthetic document format."""
import re
import shutil
import subprocess
from decimal import Decimal, InvalidOperation


FIELDS = {"invoice": ("Invoice", "Invoice No"), "vendor": ("Vendor", "Supplier"),
          "po": ("PO",), "total": ("Total",)}


def read_document(path):
    if str(path).lower().endswith(".pdf"):
        if not shutil.which("pdftotext"):
            raise RuntimeError("Install pdftotext to read text-layer PDFs")
        return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                              capture_output=True, text=True).stdout
    with open(path, encoding="utf-8") as stream:
        return stream.read()


def parse_invoice(text):
    """Expected fields: Invoice/Vendor/PO/Total and Item: SKU | qty | price | amount."""
    fields = {}
    for field, labels in FIELDS.items():
        expression = "|".join(re.escape(label) for label in labels)
        matches = re.findall(r"^(?:" + expression + r"):\s*(.*?)\s*$", text,
                             re.MULTILINE | re.IGNORECASE)
        if len(matches) != 1 or not matches[0]:
            raise ValueError(f"Expected exactly one nonempty {field} field")
        fields[field] = matches[0]
    lines = []
    for raw in re.findall(r"^Item:\s*(.*?)\s*$", text, re.MULTILINE | re.IGNORECASE):
        parts = [part.strip() for part in raw.split("|")]
        if len(parts) != 4 or not parts[0]:
            raise ValueError("Item format: SKU | quantity | unit price | amount")
        try:
            quantity, price, amount = map(Decimal, parts[1:])
        except InvalidOperation as error:
            raise ValueError("Invalid item amount") from error
        if not all(value.is_finite() for value in (quantity, price, amount)):
            raise ValueError("Non-finite item amount")
        lines.append({"sku": parts[0], "quantity": quantity, "unit_price": price, "amount": amount})
    if not lines:
        raise ValueError("At least one Item required")
    try:
        total = Decimal(fields["total"])
    except InvalidOperation as error:
        raise ValueError("Invalid total") from error
    if not total.is_finite() or total < 0:
        raise ValueError("Invalid total")
    return {"number": fields["invoice"], "vendor": fields["vendor"],
            "po_id": fields["po"], "total": total, "lines": lines}


def review(invoice, purchase_orders, posted):
    issues = []
    key = (invoice["vendor"], invoice["number"])
    if key in posted:
        issues.append("Invoice already posted")
    po = purchase_orders.get(invoice["po_id"])
    if po is None:
        issues.append("Purchase order not found")
    elif po["vendor"] != invoice["vendor"]:
        issues.append("Vendor does not match purchase order")
    seen = set()
    for line in invoice["lines"]:
        sku = line["sku"]
        if sku in seen:
            issues.append(f"Duplicate line: {sku}")
        seen.add(sku)
        if line["quantity"] <= 0 or line["unit_price"] < 0 or line["amount"] < 0:
            issues.append(f"Invalid amount: {sku}")
        if line["quantity"] * line["unit_price"] != line["amount"]:
            issues.append(f"Line arithmetic mismatch: {sku}")
        if po:
            expected = po["items"].get(sku)
            if expected is None:
                issues.append(f"SKU not on purchase order: {sku}")
            elif line["quantity"] > Decimal(str(expected["quantity"])) or line["unit_price"] != Decimal(str(expected["unit_price"])):
                issues.append(f"Purchase order mismatch: {sku}")
    if invoice["total"] != sum((line["amount"] for line in invoice["lines"]), Decimal("0")):
        issues.append("Grand total mismatch")
    return {"approved_for_review": not issues, "issues": issues,
            "invoice": invoice["number"], "vendor": invoice["vendor"]}


def post_to_erp(invoice, purchase_orders, reviewer_approved, posted):
    if not reviewer_approved:
        raise PermissionError("Reviewer approval required")
    decision = review(invoice, purchase_orders, posted)
    if not decision["approved_for_review"]:
        raise ValueError("Resolve discrepancies before posting")
    key = (invoice["vendor"], invoice["number"])
    if key in posted:
        raise ValueError("Invoice already posted")
    record = {"invoice": invoice["number"], "vendor": invoice["vendor"],
              "total": str(invoice["total"]), "status": "posted"}
    posted[key] = record
    return record
