import unittest
from tempfile import NamedTemporaryFile
from unittest.mock import patch

from src.nodes.extract_receipt import ExtractReceipt
from src.schemas.state import WorkflowState


class TestExtractReceipt(unittest.TestCase):
    def test_extract_receipt_from_local_path(self) -> None:
        with NamedTemporaryFile(suffix=".jpg") as tmp_file:
            tmp_file.write(b"fake-bytes")
            tmp_file.flush()

            state = WorkflowState(file_id=tmp_file.name)

            with patch("src.nodes.extract_receipt.extract_receipt_from_image") as mock_extract:
                mock_extract.return_value = {"merchant_name": "Test Cafe"}

                updated = ExtractReceipt()(state)

        self.assertIsNotNone(updated.receipt_json)
        self.assertEqual(updated.receipt_json["merchant_name"], "Test Cafe")
        mock_extract.assert_called_once()

    def test_extract_receipt_without_file_id(self) -> None:
        state = WorkflowState()

        updated = ExtractReceipt()(state)

        self.assertIsNone(updated.receipt_json)


if __name__ == "__main__":
    unittest.main()
