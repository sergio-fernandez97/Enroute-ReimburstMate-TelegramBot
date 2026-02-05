import unittest
from unittest.mock import patch

from src.nodes.extract_receipt import ExtractReceipt
from src.schemas.state import WorkflowState


class TestExtractReceipt(unittest.TestCase):
    def test_returns_state_when_no_file_id(self):
        state = WorkflowState(user_input="No receipt here")
        node = ExtractReceipt()

        result = node(state)

        self.assertIsNone(result.receipt_json)

    def test_sets_receipt_json_from_extractor(self):
        state = WorkflowState(file_id="file-123")
        node = ExtractReceipt()

        with patch.object(
            ExtractReceipt, "_load_image_bytes", return_value=(b"image-bytes", ".jpg")
        ), patch.object(
            ExtractReceipt, "_extract_receipt_json", return_value={"is_receipt": True}
        ):
            result = node(state)

        self.assertEqual(result.receipt_json, {"is_receipt": True})


if __name__ == "__main__":
    unittest.main()
