import tempfile
import unittest
from unittest.mock import patch

from src.nodes.extract_receipt import ExtractReceiptNode
from src.schemas.state import WorkflowState


class TestExtractReceiptNode(unittest.TestCase):
    def test_returns_state_when_missing_file_id(self) -> None:
        node = ExtractReceiptNode()
        state = WorkflowState(file_id=None)

        result = node(state)

        self.assertIs(result, state)
        self.assertIsNone(result.receipt_json)

    def test_sets_receipt_json_from_extractor(self) -> None:
        node = ExtractReceiptNode()
        expected = {"merchant_name": "Test Cafe", "total": 12.34}

        with tempfile.NamedTemporaryFile(suffix=".jpg") as temp_file:
            temp_file.write(b"fake image bytes")
            temp_file.flush()
            state = WorkflowState(file_id=temp_file.name)

            with patch.object(node, "_extract_receipt", return_value=expected):
                result = node(state)

        self.assertEqual(result.receipt_json, expected)


if __name__ == "__main__":
    unittest.main()
