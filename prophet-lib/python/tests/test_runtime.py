from __future__ import annotations

import unittest

from prophet_events_runtime import EventWireEnvelope
from prophet_events_runtime import NoOpEventPublisher
from prophet_events_runtime import TransitionValidationResult
from prophet_events_runtime import create_event_id
from prophet_events_runtime import now_iso
from prophet_events_runtime import publish_batch_sync
from prophet_events_runtime import publish_sync


class RuntimeTests(unittest.TestCase):
    def test_create_event_id(self) -> None:
        value = create_event_id()
        self.assertTrue(value)

    def test_now_iso(self) -> None:
        value = now_iso()
        self.assertIn("T", value)

    def test_sync_helpers(self) -> None:
        publisher = NoOpEventPublisher()
        envelope = EventWireEnvelope(
            event_id="evt-1",
            trace_id="trace-1",
            event_type="Example",
            schema_version="1.0.0",
            occurred_at=now_iso(),
            source="tests",
            payload={},
            updated_objects=[
                {
                    "object_type": "Order",
                    "object_ref": {"orderId": "ord-1"},
                    "object": {"orderId": "ord-1", "totalAmount": 42},
                }
            ],
        )
        publish_sync(publisher, envelope)
        publish_batch_sync(publisher, [envelope])

    def test_transition_validation_result_helpers(self) -> None:
        passed = TransitionValidationResult.passed()
        self.assertTrue(passed.passesValidation)
        self.assertIsNone(passed.failureReason)

        failed = TransitionValidationResult.failed("blocked")
        self.assertFalse(failed.passesValidation)
        self.assertEqual("blocked", failed.failureReason)


if __name__ == "__main__":
    unittest.main()
