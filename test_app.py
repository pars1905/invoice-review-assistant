import unittest
from app import parse_invoice, post_to_erp, review
from demo import PO, SAMPLE


class InvoiceTests(unittest.TestCase):
    def test_valid_invoice_requires_approval(self):
        invoice = parse_invoice(SAMPLE)
        decision = review(invoice, PO, {})
        self.assertTrue(decision["approved_for_review"])
        posted = {}
        with self.assertRaises(PermissionError):
            post_to_erp(invoice, PO, False, posted)
        self.assertFalse(posted)
        post_to_erp(invoice, PO, True, posted)
        self.assertIn("Invoice already posted", review(invoice, PO, posted)["issues"])

    def test_line_and_total_discrepancies_block_post(self):
        invoice = parse_invoice(SAMPLE.replace("25.00", "26.00"))
        decision = review(invoice, PO, {})
        self.assertIn("Line arithmetic mismatch: PAPER", decision["issues"])
        self.assertIn("Grand total mismatch", decision["issues"])
        with self.assertRaises(ValueError):
            post_to_erp(invoice, PO, True, {})

    def test_post_rechecks_invoice_after_review(self):
        invoice = parse_invoice(SAMPLE)
        self.assertTrue(review(invoice, PO, {})["approved_for_review"])
        invoice["total"] += 1
        with self.assertRaises(ValueError):
            post_to_erp(invoice, PO, True, {})

    def test_nonfinite_amount_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_invoice(SAMPLE.replace("Total: 31.00", "Total: NaN"))

    def test_missing_and_duplicate_fields_fail_closed(self):
        for text in (SAMPLE.replace("Vendor: Acme Supplies\n", ""), SAMPLE + "Total: 31.00\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_invoice(text)

    def test_blank_field_does_not_swallow_next_line(self):
        for label in ("Invoice: INV-101", "Vendor: Acme Supplies", "PO: PO-42"):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    parse_invoice(SAMPLE.replace(label, label.split(":")[0] + ":"))

    def test_duplicate_detection_ignores_case(self):
        posted = {}
        post_to_erp(parse_invoice(SAMPLE), PO, True, posted)
        variant = parse_invoice(SAMPLE.replace("INV-101", "inv-101"))
        self.assertIn("Invoice already posted", review(variant, PO, posted)["issues"])

    def test_only_plain_decimal_amounts_are_accepted(self):
        for value in ("1e999999", "3_1.00", "Infinity"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    parse_invoice(SAMPLE.replace("12.50", value))

    def test_pdf_layout_whitespace_is_tolerated(self):
        text = SAMPLE.replace("Total:", "\f  Total:").replace("\n", "\r\n")
        self.assertEqual(str(parse_invoice(text)["total"]), "31.00")

    def test_only_boolean_true_counts_as_approval(self):
        posted = {}
        for value in ("false", "no", 1):
            with self.subTest(value=value):
                with self.assertRaises(PermissionError):
                    post_to_erp(parse_invoice(SAMPLE), PO, value, posted)
        self.assertFalse(posted)


if __name__ == "__main__":
    unittest.main()
