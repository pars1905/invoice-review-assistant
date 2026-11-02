"""Evaluate acceptance/rejection on versioned synthetic invoice texts."""
import json
from pathlib import Path
from app import _posted_key, parse_invoice, review
from demo import PO


def evaluate(cases):
    buckets = {}
    for case in cases:
        try:
            invoice = parse_invoice(case["text"])
            posted = {_posted_key(invoice): {}} if case.get("already_posted") else {}
            accepted = review(invoice, PO, posted)["approved_for_review"]
        except ValueError:
            accepted = False
        bucket = buckets.setdefault(case["category"], {"total": 0, "correct": 0,
                                                       "expected_accept": case["expected_accept"]})
        bucket["total"] += 1
        bucket["correct"] += accepted == case["expected_accept"]
    return {"examples": len(cases), "by_category": {
        name: {**value, "rate": round(value["correct"] / value["total"], 3)}
        for name, value in sorted(buckets.items())}}


if __name__ == "__main__":
    cases = json.loads((Path(__file__).parent / "data" / "invoices_100.json").read_text())
    print(json.dumps(evaluate(cases), indent=2))
