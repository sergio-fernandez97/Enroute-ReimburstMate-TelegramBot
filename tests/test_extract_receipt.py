import unittest
from unittest.mock import patch

from src.nodes.extract_receipt import ExtractReceipt
from src.schemas.state import WorkflowState


class ExtractReceiptTests(unittest.TestCase):
    def test_extract_receipt_updates_receipt_json(self) -> None:
        state = WorkflowState(file_id="file_123")
        expected = {"merchant_name": "Test Store", "total": 12.34}

        with patch.object(
            ExtractReceipt, "_load_image_bytes", return_value=(b"fake", ".jpg")
        ):
            with patch(
                "src.nodes.extract_receipt.extract_receipt_from_image",
                return_value=expected,
            ):
                updated_state = ExtractReceipt()(state)

        self.assertIsNone(state.receipt_json)
        self.assertEqual(updated_state.receipt_json, expected)

    def test_extract_receipt_skips_when_missing_file_id(self) -> None:
        state = WorkflowState()

        with patch.object(ExtractReceipt, "_load_image_bytes") as loader:
            updated_state = ExtractReceipt()(state)

        loader.assert_not_called()
        self.assertIsNone(updated_state.receipt_json)


if __name__ == "__main__":
    unittest.main()
