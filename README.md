# Invoice Review Assistant

A standalone Python prototype for structured invoice review. It extracts fields from text-layer invoices, compares lines with a mock purchase order, detects duplicates, and posts to a mock ERP only after explicit human approval. No third-party Python packages are required.

**Scenario:** Accounts payable receives an invoice, checks its fields and line items against a purchase order, flags duplicates and discrepancies, then sends a record to a mock ERP only after a reviewer approves.

From the repository root run `python3 demo.py`, `python3 evaluate.py`, and `python3 -m unittest discover -v`. The demonstration uses synthetic plain-text invoices. `python3 demo.py path/to/invoice.pdf` accepts a text-layer PDF when `pdftotext` is installed; scanned PDFs need OCR, which this prototype does not include.

## Isolated environment

In GitHub, select **Code → Codespaces → Create codespace on main**, then run `python3 demo.py` in the terminal. The included `.devcontainer/devcontainer.json` selects Python 3.12. Text-layer PDF support in Codespaces needs `pdftotext` installed separately.

With Docker installed locally, run:

```bash
docker build -t invoice-assistant .
docker run --rm invoice-assistant
docker run --rm invoice-assistant python evaluate.py
docker run --rm invoice-assistant python -m unittest discover -v
```

The Docker image includes `pdftotext`. To use your own text-layer PDF, mount it read-only, for example `docker run --rm -v "$PWD/sample.pdf:/app/input.pdf:ro" invoice-assistant python demo.py /app/input.pdf`. The container runs a CLI demo; it does not publish a web service.

For an optional model-written explanation, set `OPENAI_API_KEY` and `OPENAI_MODEL` in your shell and run `python3 demo.py --ai`. The model receives only the review decision, never authorizes posting, and this API path has not been tested with a real key. Usage may incur charges.

Amounts use `Decimal`; each line item's quantity times unit price must match its amount, and the grand total must equal the line sum. Any missing field or mismatch blocks posting. Posting rechecks the invoice against the purchase order after approval, so a changed amount cannot bypass review. The parser intentionally accepts a narrow, documented format. Never upload confidential invoices to an external model without authorization.

`data/invoices_100.json` contains 100 generated synthetic cases across five categories. `python3 evaluate.py` reports acceptance for valid formats and rejection for duplicate or mismatched invoices. These labels are derived from a few repeated templates; the results are **not** real-world extraction accuracy. `Invoice No` and `Supplier` headings are supported, while `Purchase Order` is intentionally an unsupported variant in half the alternative-format cases. This exposes a parser limitation.

For a production pilot, connect to a real ERP behind authenticated APIs, store source-document references and reviewer identity, validate vendor identity and tax rules, and test many invoice layouts. The mock ERP is process-local and does not persist between runs.

**CV wording:** “Built a Python invoice review prototype with purchase-order reconciliation, duplicate checks, Decimal-based accounting, human approval, and evaluation on 100 synthetic cases.”
