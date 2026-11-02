import json
import unittest
from pathlib import Path
from evaluate import evaluate


class EvaluationTests(unittest.TestCase):
    def test_balanced_synthetic_cases_expose_format_gap(self):
        cases = json.loads((Path(__file__).parent / "data" / "invoices_100.json").read_text())
        result = evaluate(cases)
        self.assertEqual(result["examples"], 100)
        self.assertEqual({x["total"] for x in result["by_category"].values()}, {20})
        self.assertEqual(result["by_category"]["valid_unsupported_format"]["correct"], 10)


if __name__ == "__main__":
    unittest.main()
