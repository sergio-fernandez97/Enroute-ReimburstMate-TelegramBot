import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.nodes.extract_receipt import ExtractReceipt
from src.schemas.state import WorkflowState


class TestExtractReceipt(unittest.TestCase):
    def test_skips_without_file_id(self) -> None:
        extractor = Mock()
        node = ExtractReceipt(extractor=extractor)
        state = WorkflowState(user_input="hi")

        result = node(state)

        self.assertIsNone(result.file_id)
        self.assertIsNone(result.receipt_json)
        extractor.assert_not_called()

    def test_extracts_from_local_path(self) -> None:
        payload = {"merchant_name": "Test Cafe", "total": 12.34}
        extractor = Mock(return_value=payload)
        node = ExtractReceipt(extractor=extractor)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
            temp_file.write(b"fake-image-bytes")
            file_path = temp_file.name

        try:
            state = WorkflowState(file_id=file_path)
            result = node(state)

            extractor.assert_called_once()
            call_args = extractor.call_args.kwargs
            self.assertTrue(Path(call_args["image_path"]).is_file())
            self.assertEqual(result.receipt_json, payload)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


if __name__ == "__main__":
    unittest.main()
