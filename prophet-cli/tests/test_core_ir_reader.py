from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "prophet-cli" / "src"))

from prophet_cli.core.errors import ProphetError
from prophet_cli.core.ir_reader import IRReader


def minimal_ir() -> dict:
    return {
        "ir_version": "0.1",
        "toolchain_version": "0.3.0",
        "ontology": {"id": "ont", "name": "Ont", "version": "0.1.0"},
        "types": [{"id": "t1", "name": "Money"}],
        "objects": [{"id": "o1", "name": "Order"}],
        "structs": [],
        "action_inputs": [],
        "action_outputs": [],
        "actions": [{"id": "a1", "name": "createOrder"}],
        "events": [],
        "triggers": [],
        "ir_hash": "abc123",
    }


class IRReaderTests(unittest.TestCase):
    def test_reader_validates_and_exposes_indexes(self) -> None:
        reader = IRReader.from_dict(minimal_ir())
        self.assertEqual(reader.ir_hash, "abc123")
        self.assertIn("o1", reader.object_by_id())
        self.assertIn("t1", reader.type_by_id())
        self.assertIn("a1", reader.action_by_id())

    def test_reader_rejects_missing_required_key(self) -> None:
        payload = minimal_ir()
        del payload["objects"]
        with self.assertRaises(ProphetError) as ctx:
            IRReader.from_dict(payload)
        self.assertIn("missing required key", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

